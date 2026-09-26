"""按执行图端口追踪属性，保存可核查的值与来源。"""
from __future__ import annotations

import re
import math

from .registry import ATTRIBUTES, CONTRACTS, DIRECT_FIELDS, NODES, PARSER_VERSION, TEXT_FIELDS, node_contract

RESOURCE_TYPES = {"MODEL": "model", "CLIP": "clip", "VAE": "vae", "CONTROL_NET": "controlnet", "UPSCALE_MODEL": "upscale_model"}
ROLES = {"positive": "positive", "negative": "negative", "cond1": "positive", "cond2": "positive", "conditioning": "positive", "model": "model", "model_negative": "model", "clip": "clip", "vae": "vae", "noise": "noise", "guider": "guider", "sampler": "sampler", "sigmas": "sigmas", "latent_image": "latent", "samples": "latent", "images": "image", "image": "image", "pixels": "image", "control_net": "controlnet", "upscale_model": "upscale_model"}
PROCESSING = {"ImageScale", "ImageScaleBy", "ImageScaleToTotalPixels", "ImageUpscaleWithModel", "LatentUpscale", "LatentUpscaleBy", "VAEEncodeForInpaint", "InpaintModelConditioning", "ImagePadForOutpaint", "ImageCrop", "LatentCrop", "SD_4XUpscale_Conditioning"}
PROCESSING.update({'Image Resize (rgthree)', 'Image Inset Crop (rgthree)', 'ResizeAndPadImage'})
DIMENSION_IDS = {"width", "height", "batch_size"}


def empty_metadata():
    return {"parser_version": PARSER_VERSION, "parse_status": "missing", "has_metadata": False,
            "models": [], "loras": [], "positive_prompt": "", "negative_prompt": "",
            "width": 0, "height": 0, "branches": [], "stages": [], "unassigned": [], "diagnostics": []}


class GraphParser:
    def __init__(self, graph):
        self.nodes = {str(k): v for k, v in graph.items() if isinstance(v, dict) and isinstance(v.get("class_type"), str) and isinstance(v.get("inputs"), dict)}
        self.diagnostics = []
        self.used_encoders = set()
        self.cache = {}

    def node(self, node_id):
        return self.nodes.get(str(node_id), {})

    def source(self, node_id, field, port=None):
        source = {"node_id": str(node_id), "class_type": self.node(node_id).get("class_type", "unknown"), "field": field}
        if port is not None:
            source["output_port"] = port
        return source

    def issue(self, code, node_id, field="", detail=""):
        item = {"code": code, "node_id": str(node_id), "class_type": self.node(node_id).get("class_type", "unknown"), "field": field, "detail": detail}
        if item not in self.diagnostics:
            self.diagnostics.append(item)

    def is_link(self, node_id, field, value):
        if not isinstance(value, (list, tuple)) or len(value) != 2 or not isinstance(value[0], str) or type(value[1]) is not int:
            return False
        # 明确的结构化列表以值保留；其他已声明输入可通过连线提供。
        if field in {"loras", "lora_stack"} and value[0] not in self.nodes:
            return False
        return field in node_contract(self.node(node_id).get("class_type"))["inputs"] or value[0] in self.nodes

    def links(self, node_id):
        for field, value in self.node(node_id).get("inputs", {}).items():
            if self.is_link(node_id, field, value):
                yield field, value

    def value(self, node_id, field, stack=()):
        raw = self.node(node_id).get("inputs", {}).get(field)
        source = self.source(node_id, field)
        if not self.is_link(node_id, field, raw):
            return raw, [source], "recorded" if raw is not None else "unknown"
        value, sources, state = self.output_value(str(raw[0]), raw[1], stack)
        return value, sources + [source], state

    def output_value(self, node_id, port, stack=()):
        key = (node_id, port)
        if key in stack or len(stack) > 150:
            self.issue("cycle", node_id)
            return None, [self.source(node_id, "", port)], "unknown"
        if node_id not in self.nodes:
            self.issue("missing_node", node_id)
            return None, [self.source(node_id, "", port)], "unknown"
        cls = self.node(node_id)["class_type"]
        kind = NODES.get(cls, {}).get("kind")
        stack = (*stack, key)
        field = None
        if kind == "primitive":
            field = "seed" if cls == "Seed (rgthree)" else "text" if cls == "Krea2SystemPrompt" else "value"
        elif kind == "config":
            fields = ["steps_total", "refiner_step", "cfg", "sampler_name", "scheduler"]
            field = fields[port] if 0 <= port < len(fields) else None
        elif kind == "context":
            route = self.context_route(node_id, port, stack)
            if route:
                return self.value(*route, stack)
        elif kind == "value":
            return self.evaluate_value(node_id, port, stack)
        elif kind == "encoder" and node_contract(cls)["outputs"][port] == "STRING":
            fields = [f for f in TEXT_FIELDS if f in self.node(node_id)["inputs"]]
            string_ports = [i for i, t in enumerate(node_contract(cls)["outputs"]) if t == "STRING"]
            if port in string_ports and string_ports.index(port) < len(fields):
                return self.value(node_id, fields[string_ports.index(port)], stack)
        elif cls == "SDXL Empty Latent Image (rgthree)" and port in {1, 2}:
            dimensions, sources, _ = self.value(node_id, "dimensions", stack)
            scale, scale_sources, _ = self.value(node_id, "clip_scale", stack)
            match = re.match(r"\s*(\d+)\s*x\s*(\d+)", str(dimensions))
            if match and isinstance(scale, (float, int)):
                return int(int(match[port]) * scale), sources + scale_sources, "derived"
        elif cls in {'GetImageSize', 'Image or Latent Size (rgthree)', 'Image Resize (rgthree)'}:
            props = self.trace(node_id, 0, 'image', ()) if cls == 'Image Resize (rgthree)' else [p for field, _ in self.links(node_id) for p in self.trace_input(node_id, field, 'image', ())]
            wanted = ["width", "height", "batch_size"]
            size_port = port - 1 if cls == 'Image Resize (rgthree)' else port
            candidates = [p for p in props if 0 <= size_port < len(wanted) and p["id"] == wanted[size_port] and p["state"] != "unknown"]
            if candidates:
                return candidates[-1]["value"], candidates[-1]["sources"] + [self.source(node_id, "", port)], "derived"
        if field:
            value, sources, state = self.value(node_id, field, stack)
            if kind == "primitive" and cls == "Power Primitive (rgthree)" and value is not None:
                target = self.node(node_id)["inputs"].get("type", "STRING").split(" (")[0]
                try:
                    value = {"INT": lambda: int(float(value)), "FLOAT": lambda: float(value), "STRING": lambda: str(value), "BOOLEAN": lambda: str(value).lower() not in {"0", "false", "null", "none", ""}}[target]()
                except (ValueError, TypeError, KeyError):
                    return None, sources, "unknown"
            return value, sources, "derived" if state != "unknown" else state
        self.issue("unsupported_node" if cls not in NODES else "runtime_value", node_id, detail=str(port))
        return None, [self.source(node_id, "", port)], "unknown"

    def evaluate_value(self, node_id, port, stack):
        """计算已审核的纯标量节点；外部状态和动态模板保留为未知。"""
        import json
        cls = self.node(node_id)["class_type"]
        inputs = self.node(node_id)["inputs"]
        resolved = {field: self.value(node_id, field, stack) for field in inputs}
        sources = [source for _, path, _ in resolved.values() for source in path]
        values = {field: value for field, (value, _, _) in resolved.items()}
        if any(state == "unknown" for _, _, state in resolved.values()):
            return None, sources, "unknown"
        try:
            if cls == "StringConcatenate": value = values.get("delimiter", "").join((values["string_a"], values["string_b"]))
            elif cls == 'ResolutionSelector':
                ratio = re.match(r'(\d+):(\d+)', values['aspect_ratio'])
                a, b = int(ratio[1]), int(ratio[2])
                multiple = values.get('multiple', 8)
                scale = math.sqrt(values['megapixels'] * 1024 * 1024 / (a * b))
                value = round((a if port == 0 else b) * scale / multiple) * multiple
            elif cls == "StringSubstring": value = values["string"][values["start"]:values["end"]]
            elif cls == "StringLength": value = len(values["string"])
            elif cls == "StringReplace": value = values["string"].replace(values["find"], values["replace"])
            elif cls == "StringTrim": value = {"Both": str.strip, "Left": str.lstrip, "Right": str.rstrip}[values["mode"]](values["string"])
            elif cls == "CaseConverter": value = {"lowercase": str.lower, "UPPERCASE": str.upper, "Title Case": str.title, "Capitalize": str.capitalize}[values["mode"]](values["string"])
            elif cls == "StringContains":
                text, part = values["string"], values["substring"]
                value = part in text if values.get("case_sensitive", True) else part.lower() in text.lower()
            elif cls == "StringCompare":
                a, b = values["string_a"], values["string_b"]
                if not values.get("case_sensitive", True): a, b = a.lower(), b.lower()
                value = {"Equal": a == b, "Starts With": a.startswith(b), "Ends With": a.endswith(b)}[values["mode"]]
            elif cls == "ComfyNotNode": value = not values["value"]
            elif cls == "ComfySwitchNode": value = values["on_true"] if values["switch"] else values["on_false"]
            elif cls == "StringFormat": value = values["f_string"].format(**values["values"])
            elif cls == "JsonExtractString":
                try:
                    data = json.loads(values['json_string'])
                    value = str(data[values['key']]) if isinstance(data, dict) and data.get(values['key']) is not None else ''
                except (ValueError, TypeError): value = ''
            elif cls in {"ConvertArrayToString", "ConvertDictionaryToString"}:
                value = json.dumps(values.get("array", values.get("dictionary")), ensure_ascii=False, indent=values.get("indent") or None)
            elif cls in {'ComfyAndNode', 'ComfyOrNode'}:
                items = values['values']
                value = (all if cls == 'ComfyAndNode' else any)(items.values() if isinstance(items, dict) else items)
            elif cls.startswith('Regex'):
                flags = (re.IGNORECASE if values.get('case_insensitive', True) else 0) | (re.MULTILINE if values.get('multiline') else 0) | (re.DOTALL if values.get('dotall') else 0)
                regex = re.compile(values['regex_pattern'], flags)
                text = values['string']
                if cls == 'RegexReplace': value = regex.sub(values['replace'], text, count=values.get('count', 0))
                elif cls == 'RegexMatch': value = bool(regex.search(text))
                else:
                    match = regex.search(text)
                    mode = values['mode']
                    if mode == 'First Match': value = match.group(0) if match else ''
                    elif mode == 'First Group': value = match.group(values.get('group_index', 1)) if match and match.lastindex and values.get('group_index', 1) <= match.lastindex else ''
                    elif mode == 'All Matches':
                        matches = regex.findall(text)
                        value = '\n'.join(m[0] if isinstance(m, tuple) else m for m in matches)
                    else:
                        group_index = values.get('group_index', 1)
                        value = '\n'.join(m.group(group_index) for m in regex.finditer(text) if len(m.groups()) >= group_index)
            elif cls == "Text (LoraManager)":
                value = values["text"]
                if re.search(r"\{.*\}|__.+__", value):
                    self.issue("runtime_value", node_id, "text")
                    return None, sources, "unknown"
            elif cls == "CustomCombo" and port == 0: value = values["choice"]
            else:
                self.issue("runtime_value", node_id)
                return None, sources, "unknown"
            return value, sources, "derived"
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, re.error):
            self.issue("invalid_value", node_id)
            return None, sources, "unknown"

    def context_route(self, node_id, port, stack=()):
        cls = self.node(node_id)["class_type"]
        inputs = self.node(node_id)["inputs"]
        if cls == "Any Switch (rgthree)":
            candidates = [(node_id, field) for field in inputs if inputs[field] is not None]
            if len(candidates) == 1:
                return candidates[0]
            self.issue("runtime_selection", node_id)
            return None
        names = node_contract(cls)["output_names"]
        if port >= len(names) or port == 0:
            return None
        wanted = names[port].lower()
        aliases = {"context": "base_ctx", "step_refiner": "step_refiner"}
        wanted = aliases.get(wanted, wanted)
        seen = set()

        def search(current):
            if current in seen:
                self.issue("cycle", current)
                return None
            seen.add(current)
            values = self.node(current).get("inputs", {})
            if wanted in values and values[wanted] is not None:
                return current, wanted
            ctx_links = [(f, v) for f, v in self.links(current) if f == "base_ctx" or f.startswith("ctx_")]
            current_cls = self.node(current).get("class_type", "")
            if "Switch" in current_cls and len(ctx_links) > 1:
                self.issue("runtime_selection", current)
                return None
            if "Merge" in current_cls:
                ctx_links.reverse()
            for _, link in ctx_links:
                result = search(link[0])
                if result:
                    return result
            return None

        return search(node_id)

    def prop(self, node_id, field, attr=None, channel=None):
        value, sources, state = self.value(node_id, field)
        attr = attr or DIRECT_FIELDS.get(field, field)
        if attr == "seed" and value is not None:
            if isinstance(value, int) and value < 0:
                value, state = None, "unknown"
            else:
                value = str(value)
        result = {"id": attr, "group": ATTRIBUTES.get(attr, ("processing",))[0], "value": value, "state": state, "sources": sources}
        if channel:
            result["channel"] = channel
        if state == "unknown":
            result["reason"] = "runtime_value"
        return result

    def constant(self, node_id, field, attr, value, state="recorded", **extra):
        return {"id": attr, "group": ATTRIBUTES[attr][0], "value": value, "state": state, "sources": [self.source(node_id, field)], **extra}

    def trace_input(self, node_id, field, role, stack):
        value = self.node(node_id).get("inputs", {}).get(field)
        if self.is_link(node_id, field, value):
            props = self.trace(str(value[0]), value[1], role, stack)
            origin = self.source(node_id, field)
            return [{**p, "sources": p["sources"] + ([origin] if origin not in p["sources"] else [])} for p in props]
        return []

    def trace(self, node_id, port, role, stack=()):
        key = (node_id, port, role)
        if key in stack or len(stack) > 150:
            self.issue("cycle", node_id)
            return []
        if node_id not in self.nodes:
            self.issue("missing_node", node_id)
            return []
        cls = self.node(node_id)["class_type"]
        spec = NODES.get(cls)
        contract = node_contract(cls)
        if port < 0 or (contract["outputs"] and port >= len(contract["outputs"])):
            self.issue("invalid_port", node_id, detail=str(port))
            return []
        if not spec:
            self.issue("unsupported_node", node_id)
            return [self.constant(node_id, "", role if role in ATTRIBUTES else "processing_settings", None, "unknown", reason="unsupported_node")]
        kind = spec["kind"]
        inputs = self.node(node_id)["inputs"]
        stack = (*stack, key)
        props = []
        if kind in {"checkpoint", "loader"}:
            resource = RESOURCE_TYPES.get(contract["outputs"][port], role) if contract["outputs"] else role
            resource = resource if resource in ATTRIBUTES else spec.get("resource", "model")
            for field in spec["fields"]:
                if field not in inputs:
                    continue
                p = self.prop(node_id, field, resource)
                if inputs.get("select_at_random"):
                    p.update(value=None, state="unknown", reason="runtime_selection")
                elif kind == "checkpoint" and resource in {"clip", "vae"}:
                    p["value"] = {"builtin_checkpoint": p["value"]}
                props.append(p)
            props += self.settings(node_id, set(spec["fields"]) | {"select_at_random"}, "model_settings")
            return props
        if kind == "context":
            route = self.context_route(node_id, port)
            if route:
                return self.trace_input(*route, role, stack)
            self.issue("runtime_selection", node_id)
            return [self.constant(node_id, "", role if role in ATTRIBUTES else "processing_settings", None, "unknown", reason="runtime_selection")]
        if kind == "sample":
            # 上一采样阶段只向下游传递尺寸，采样参数由各自阶段保存。
            return [p for p in self.trace_input(node_id, "latent_image", "latent", stack) if p["id"] in DIMENSION_IDS]
        if kind == "primitive" or kind == "config":
            value, sources, state = self.output_value(node_id, port)
            return [{**self.constant(node_id, "", role if role in ATTRIBUTES else "processing_settings", value, state), "sources": sources}]
        if kind == "encoder":
            self.used_encoders.add(node_id)
            output_type = contract["outputs"][port] if contract["outputs"] else "CONDITIONING"
            if output_type == 'LATENT':
                props = [self.prop(node_id, field, field) for field in ('width', 'height', 'batch_size') if field in inputs]
                if not any(p['id'] == 'width' for p in props):
                    props += [self.constant(node_id, '', dim, None, 'unknown', reason='runtime_value') for dim in ('width', 'height')]
                return props
            if output_type in {"MODEL", "CLIP"}:
                return self.trace_input(node_id, "opt_model" if output_type == "MODEL" else "opt_clip", role, stack) + self.prompt_loras(node_id)
            text_role = role if role in {"positive", "negative", "unassigned"} else "unassigned"
            text_fields = ('negative_prompt',) if 'negative_prompt' in inputs and port == 1 else TEXT_FIELDS
            for field in text_fields:
                if field in inputs:
                    p = self.prop(node_id, field, text_role, field)
                    if cls == 'Prompt (LoraManager)' and isinstance(p['value'], str):
                        if re.search(r'\{.*\}|__.+__', p['value']):
                            props.append(self.prop(node_id, field, 'unassigned', 'configured_text'))
                            p.update(value=None, state='unknown', reason='runtime_value')
                        else:
                            triggers = [self.value(node_id, f) for f in inputs if f.startswith('trigger_words')]
                            if any(state == 'unknown' for _, _, state in triggers):
                                p.update(value=None, state='unknown', reason='runtime_value')
                            elif triggers:
                                p.update(value=', '.join([str(v) for v, _, _ in triggers if v] + [p['value']]), state='derived')
                                p['sources'] = [s for _, sources, _ in triggers for s in sources] + p['sources']
                    props.append(p)
            if "system_prompt" in inputs:
                props.append(self.prop(node_id, "system_prompt", "system_prompt"))
            props += self.trace_input(node_id, "clip", "clip", stack)
            props += self.trace_input(node_id, "opt_clip", "clip", stack)
            props += self.trace_input(node_id, 'conditioning', role, stack)
            props += self.prompt_loras(node_id)
            props += self.trace_input(node_id, "vae", "vae", stack)
            for field in {"guidance", "width", "height", "target_width", "target_height"} & inputs.keys():
                props.append(self.prop(node_id, field, field, "conditioning"))
            return props
        if kind == "lora":
            route = "clip" if role == "clip" else "model"
            props += self.trace_input(node_id, route, route, stack)
            props += self.trace_input(node_id, 'prev_hooks', 'lora', stack)
            props += self.loras(node_id, stack)
            return props
        if kind == 'external':
            props += self.settings(node_id, set(), 'conditioning')
            props.append(self.constant(node_id, '', role if role in ATTRIBUTES else 'processing_settings', None, 'unknown', reason='runtime_value'))
            return props
        if kind == "lora_stack":
            return self.loras(node_id, stack)
        if kind in {"scheduler", "sampler", "noise"}:
            for field in inputs:
                if field in DIRECT_FIELDS:
                    props.append(self.prop(node_id, field))
            if kind == "scheduler" and "scheduler" not in inputs:
                props.append(self.constant(node_id, "class_type", "scheduler", cls))
            if kind == "sampler" and "sampler_name" not in inputs:
                props.append(self.constant(node_id, "class_type", "sampler", cls))
            if cls == "DisableNoise":
                props.append(self.constant(node_id, "class_type", "add_noise", False))
            props += self.settings(node_id, set(DIRECT_FIELDS), "sampling_settings")
            return props
        if kind == "sigmas":
            props += self.trace_input(node_id, "sigmas", "sigmas", stack)
            props += self.settings(node_id, set(), "sampling_settings")
            return props
        if cls == "ConditioningZeroOut":
            return [self.constant(node_id, "conditioning", "conditioning", "zeroed", channel=role)]
        if kind == "auxiliary":
            props += self.settings(node_id, set(), "control_settings" if "Control" in cls or "Patch" in cls else "model_settings")
        # 条件输出按端口选择正反向；资源输出只追踪对应类型的端口。
        output_type = contract["outputs"][port] if contract["outputs"] else ""
        resource_type = output_type if output_type in RESOURCE_TYPES else None
        for field, link in self.links(node_id):
            input_type = contract["inputs"].get(field, {}).get("type")
            if resource_type and input_type != resource_type:
                if field not in {"model_patch", "control_net", "hooks", "hook_kf"}:
                    continue
            if output_type == "CONDITIONING" and "positive" in inputs and "negative" in inputs:
                chosen = "positive" if port == 0 else "negative"
                if field in {"positive", "negative"} and field != chosen:
                    continue
            if output_type == 'CONDITIONING' and cls.startswith('PairConditioning'):
                if field.startswith('positive') and port != 0 or field.startswith('negative') and port != 1:
                    continue
            if cls == "InpaintModelConditioning" and port == 2 and field in {"positive", "negative"}:
                continue
            if kind == "guider":
                child_role = ROLES.get(field, role)
            elif input_type == "CONDITIONING":
                child_role = role if role in {"positive", "negative", "unassigned"} else ROLES.get(field, "unassigned")
            else:
                child_role = RESOURCE_TYPES.get(input_type, ROLES.get(field, role))
            # 标量连线由 prop/value 处理，避免把标量当成资源。
            if input_type in {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}:
                continue
            props += self.trace_input(node_id, field, child_role, stack)
        if kind == "guider":
            for field in inputs:
                if field in DIRECT_FIELDS:
                    props.append(self.prop(node_id, field, channel=field))
            return props
        for field in inputs:
            if field in DIRECT_FIELDS:
                props.append(self.prop(node_id, field))
        input_dimensions = {p['id']: p for p in props if p['id'] in {'width', 'height'} and not p.get('channel')}
        # 变换节点保存显式尺寸，并覆盖其上游尺寸。
        for dim in ("width", "height", "batch_size"):
            if dim in inputs and (not resource_type):
                p = self.prop(node_id, dim, dim)
                if p["value"] not in {None, 0}:
                    props = [q for q in props if q["id"] != dim]
                    props.append(p)
                    if cls in PROCESSING and dim != "batch_size":
                        props.append(self.prop(node_id, dim, "target_" + dim))
        if cls in {"ImageScaleBy", "LatentUpscaleBy"}:
            factor, _, _ = self.value(node_id, "scale_by")
            for p in props:
                if p["id"] in {"width", "height"} and isinstance(p["value"], (int, float)) and isinstance(factor, (int, float)):
                    size = round(p["value"] * factor)
                    if cls == "LatentUpscaleBy":
                        size = round(p["value"] / 8 * factor) * 8
                    p.update(value=size, state="derived", sources=p["sources"] + [self.source(node_id, "scale_by")])
        if cls in {'ImageScale', 'Image Resize (rgthree)', 'ResizeAndPadImage'}:
            original_w = input_dimensions.get('width', {}).get('value')
            original_h = input_dimensions.get('height', {}).get('value')
            width_field, height_field = ('target_width', 'target_height') if cls == 'ResizeAndPadImage' else ('width', 'height')
            w, ws, _ = self.value(node_id, width_field)
            h, hs, _ = self.value(node_id, height_field)
            fit = inputs.get('fit', 'crop')
            if cls == 'Image Resize (rgthree)' and inputs.get('measurement') == 'percentage':
                w = round(w * original_w / 100) if isinstance(w, (int, float)) and isinstance(original_w, (int, float)) else None
                h = round(h * original_h / 100) if isinstance(h, (int, float)) and isinstance(original_h, (int, float)) else None
            known_original = isinstance(original_w, (int, float)) and isinstance(original_h, (int, float)) and original_w > 0 and original_h > 0
            if w == 0 and h == 0: w, h = original_w, original_h
            elif w == 0 or h == 0:
                fit = 'contain'
                if w == 0: w = round(h / original_h * original_w) if known_original and isinstance(h, (int, float)) else None
                if h == 0: h = round(w / original_w * original_h) if known_original and isinstance(w, (int, float)) else None
            if cls == 'Image Resize (rgthree)' and fit == 'contain':
                if known_original and isinstance(w, (int, float)) and isinstance(h, (int, float)):
                    ratio = min(w / original_w, h / original_h)
                    w, h = round(original_w * ratio), round(original_h * ratio)
                else: w, h = None, None
            props = [p for p in props if p['id'] not in {'width', 'height'} or p.get('channel')]
            sources = [s for p in input_dimensions.values() for s in p['sources']] + ws + hs
            for dim, value in (('width', w), ('height', h)):
                props.append({**self.constant(node_id, dim, dim, value, 'derived' if value is not None else 'unknown', **({'reason': 'runtime_value'} if value is None else {})), 'sources': sources})
        if cls in {'ImageRotate', 'LatentRotate'} and inputs.get('rotation') in {'90 degrees', '270 degrees', '90', '270'}:
            for p in props:
                if p['id'] in {'width', 'height'}:
                    p['id'] = 'height' if p['id'] == 'width' else 'width'
                    p['state'] = 'derived' if p['state'] != 'unknown' else 'unknown'
        if cls == "RepeatLatentBatch":
            amount, _, _ = self.value(node_id, "amount")
            for p in props:
                if p["id"] == "batch_size" and isinstance(p["value"], int) and isinstance(amount, int):
                    p.update(value=p["value"] * amount, state="derived", sources=p["sources"] + [self.source(node_id, "amount")])
        if cls == "SDXL Empty Latent Image (rgthree)":
            dimensions, _, _ = self.value(node_id, "dimensions")
            match = re.match(r"\s*(\d+)\s*x\s*(\d+)", str(dimensions))
            if match:
                props += [self.constant(node_id, "dimensions", dim, int(match[i]), "derived") for i, dim in enumerate(("width", "height"), 1)]
        if cls in {"LoadImage", "LoadImageOutput", "LoadImageMask", "LoadLatent", "ImageUpscaleWithModel", "ImageScaleToTotalPixels", "FluxKontextImageScale"}:
            # 输入文件与模型的实际输出尺寸未记录在执行图内。
            props = [p for p in props if p["id"] not in {"width", "height"}]
            for dim in ("width", "height"):
                props.append(self.constant(node_id, "", dim, None, "unknown", reason="runtime_value"))
        excluded = set(DIRECT_FIELDS) | {"width", "height", "batch_size"}
        group = "control_settings" if "Control" in cls or "Conditioning" in cls else "model_settings" if resource_type else "processing_settings"
        props += self.settings(node_id, excluded, group)
        if output_type == 'CONDITIONING':
            props = [p for p in props if p['id'] not in DIMENSION_IDS or p.get('channel') == 'conditioning']
        return props

    def settings(self, node_id, excluded, attr):
        result = []
        inputs = self.node(node_id)["inputs"]
        for field, raw in inputs.items():
            if field in excluded:
                continue
            typ = node_contract(self.node(node_id)["class_type"])["inputs"].get(field, {}).get("type")
            if self.is_link(node_id, field, raw) and typ not in {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}:
                continue
            if isinstance(raw, (str, int, float, bool)) or typ in {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}:
                result.append(self.prop(node_id, field, attr, field))
        return result

    def loras(self, node_id, stack=()):
        inputs = self.node(node_id)["inputs"]
        cls = self.node(node_id)["class_type"]
        result = []

        def append(field, name, model, clip=None, active=True):
            if not active or name in {None, "None", ""}:
                return
            result.append(self.constant(node_id, field, "lora", {"name": name, "strength_model": model, "strength_clip": clip, "active": active}))

        if "lora_name" in inputs:
            name, src, state = self.value(node_id, "lora_name")
            model, model_src, model_state = self.value(node_id, "strength_model")
            clip, clip_src, clip_state = self.value(node_id, "strength_clip") if "strength_clip" in inputs else (None, [], "recorded")
            append("lora_name", name, model, clip)
            if result:
                result[-1]["sources"] = src + model_src + clip_src
                if "unknown" in {state, model_state, clip_state}:
                    result[-1].update(state="unknown", reason="runtime_value")
        elif cls == "Power Lora Loader (rgthree)":
            for field, value in inputs.items():
                if field.lower().startswith("lora_") and isinstance(value, dict):
                    append(field, value.get("lora"), value.get("strength"), value.get("strengthTwo", value.get("strength")) if "clip" in inputs else None, value.get("on", False))
        elif cls == "Lora Loader Stack (rgthree)":
            for index in range(1, 5):
                field = f"lora_{index:02}"
                name, _, _ = self.value(node_id, field)
                strength, _, _ = self.value(node_id, f"strength_{index:02}")
                append(field, name, strength, strength)
        elif "LoraManager" in cls:
            if cls in {"Lora Randomizer (LoraManager)", "Lora Cycler (LoraManager)"}:
                return [self.constant(node_id, "", "lora", None, "unknown", reason="runtime_selection")]
            if cls == "Lora Stack Combiner (LoraManager)":
                return self.trace_input(node_id, "lora_stack1", "lora", stack) + self.trace_input(node_id, "lora_stack2", "lora", stack)
            entries = inputs.get("loras", [])
            if isinstance(entries, dict):
                entries = entries.get("__value__", [])
            if isinstance(entries, str):
                import json
                try:
                    entries = json.loads(entries)
                except ValueError:
                    entries = []
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict):
                        append("loras", entry.get("name"), entry.get("strength"), entry.get("clipStrength", entry.get("strength")), entry.get("active", False))
            if "lora_syntax" in inputs:
                text, _, state = self.value(node_id, "lora_syntax")
                if isinstance(text, str):
                    for match in re.finditer(r"<lora:([^:>]+):([^:>]+)(?::([^:>]+))?>", text, re.IGNORECASE):
                        try:
                            append("lora_syntax", match[1], float(match[2]), float(match[3] or match[2]))
                        except ValueError:
                            self.issue("invalid_value", node_id, "lora_syntax")
                elif state == "unknown":
                    result.append(self.constant(node_id, "lora_syntax", "lora", None, "unknown", reason="runtime_value"))
            if "lora_stack" in inputs:
                value = inputs["lora_stack"]
                if self.is_link(node_id, "lora_stack", value):
                    result += self.trace_input(node_id, "lora_stack", "lora", stack)
                elif isinstance(value, list):
                    for entry in value:
                        if isinstance(entry, (list, tuple)) and len(entry) == 3:
                            append("lora_stack", *entry)
        return result

    def prompt_loras(self, node_id):
        inputs = self.node(node_id)["inputs"]
        if "rgthree" not in self.node(node_id)["class_type"] or inputs.get("insert_lora") == "DISABLE LORAS" or not inputs.get("opt_model"):
            return []
        result = []
        for field in ("prompt", "prompt_g", "prompt_l"):
            value, sources, _ = self.value(node_id, field)
            if isinstance(value, str):
                for name, strength in re.findall(r"<lora:([^:>]+):([+-]?[\d.]+)>", value):
                    result.append({**self.constant(node_id, field, "lora", {"name": name, "strength_model": float(strength), "strength_clip": float(strength), "active": True}), "sources": sources})
        return result

    def sigma_length(self, node_id, port, stack=()):
        if (node_id, port) in stack:
            return None
        stack = (*stack, (node_id, port))
        node = self.node(node_id)
        cls = node.get("class_type")
        inputs = node.get("inputs", {})
        if NODES.get(cls, {}).get("kind") == "scheduler":
            steps, _, _ = self.value(node_id, "steps")
            denoise, _, _ = self.value(node_id, "denoise")
            if isinstance(steps, int):
                return 0 if denoise == 0 else steps + 1
        link = inputs.get("sigmas")
        if not self.is_link(node_id, "sigmas", link):
            return None
        size = self.sigma_length(link[0], link[1], stack)
        if size is None:
            return None
        if cls == "SplitSigmas":
            step, _, _ = self.value(node_id, "step")
            if isinstance(step, int) and step >= 0:
                return min(size, step + 1) if port == 0 else max(0, size - step)
        if cls == "SplitSigmasDenoise":
            denoise, _, _ = self.value(node_id, "denoise")
            if isinstance(denoise, (float, int)):
                count = round(max(0, size - 1) * denoise)
                return (max(0, size - count) if count else 0) if port == 0 else min(size, count + 1)
        if cls in {"FlipSigmas", "SetFirstSigma"}:
            return size
        return None

    def unique(self, properties):
        result = []
        for prop in properties:
            match = next((p for p in result if (p["id"], p.get("channel"), p["value"], p["sources"][0]) == (prop["id"], prop.get("channel"), prop["value"], prop["sources"][0])), None)
            if match:
                match["sources"] += [s for s in prop["sources"] if s not in match["sources"]]
            else:
                result.append(prop)
        return result

    def stage(self, node_id):
        node = self.node(node_id)
        cls = node["class_type"]
        kind = NODES.get(cls, {}).get("kind")
        props = []
        if kind == "sample":
            for field in node["inputs"]:
                if field in DIRECT_FIELDS:
                    props.append(self.prop(node_id, field))
            for field, _ in self.links(node_id):
                if field not in DIRECT_FIELDS:
                    props += self.trace_input(node_id, field, ROLES.get(field, field), ())
            steps, _, _ = self.value(node_id, "steps")
            stage_steps = None
            if isinstance(steps, int):
                start, _, _ = self.value(node_id, "start_at_step")
                end, _, _ = self.value(node_id, "end_at_step")
                stage_steps = max(0, min(steps, end if isinstance(end, int) else steps) - max(0, start if isinstance(start, int) else 0))
                if node["inputs"].get("denoise") == 0:
                    stage_steps = 0
            elif "sigmas" in node["inputs"]:
                link = node["inputs"]["sigmas"]
                if self.is_link(node_id, "sigmas", link):
                    length = self.sigma_length(link[0], link[1])
                    stage_steps = max(0, length - 1) if length is not None else None
            props.append(self.constant(node_id, "steps" if isinstance(steps, int) else "sigmas", "stage_steps", stage_steps, "derived" if stage_steps is not None else "unknown", **({"reason": "runtime_value"} if stage_steps is None else {})))
            # 解码 VAE 在采样下游，作为独立阶段附加资源处理。
        else:
            props = self.trace(node_id, 0, "image", ())
        return {"id": node_id, "node_id": node_id, "class_type": cls, "kind": "sampling" if kind == "sample" else "processing", "properties": self.unique(props), "depends_on": []}

    def ancestors(self, node_id, stack=()):
        if node_id in stack:
            self.issue("cycle", node_id)
            return []
        if len(stack) > 150:
            self.issue("cycle", node_id)
            return []
        result = []
        for _, link in self.links(node_id):
            if link[0] not in self.nodes:
                self.issue("missing_node", link[0])
                continue
            for parent in self.ancestors(link[0], (*stack, node_id)):
                if parent not in result:
                    result.append(parent)
        if node_id not in result:
            result.append(node_id)
        return result

    def parse(self):
        info = empty_metadata()
        info["has_metadata"] = bool(self.nodes)
        if not self.nodes:
            info["parse_status"] = "invalid"
            return info
        outputs = [n for n in self.nodes if NODES.get(self.nodes[n]["class_type"], {}).get("kind") == "output"]
        stage_ids = [n for n in self.nodes if NODES.get(self.nodes[n]["class_type"], {}).get("kind") == "sample" or self.nodes[n]["class_type"] in PROCESSING or self.nodes[n]["class_type"] in {"VAEDecode", "VAEDecodeTiled"}]
        if not outputs:
            outputs = [n for n in stage_ids if not any(n != other and n in self.ancestors(other) for other in stage_ids)]
        ordered = []
        for output in outputs:
            parents = self.ancestors(output)
            ids = [n for n in parents if n in stage_ids]
            if not ids:
                ids = [output]
            for n in ids:
                if n not in ordered:
                    ordered.append(n)
            is_output = NODES.get(self.node(output)["class_type"], {}).get("kind") == "output"
            info["branches"].append({"id": output, "output_node_id": output if is_output else None, "association": "unique" if len(outputs) == 1 and is_output else "unconfirmed", "stage_ids": ids})
        info["stages"] = [self.stage(n) for n in ordered]
        for stage in info["stages"]:
            ancestors = self.ancestors(stage["id"])[:-1]
            dependencies = [n for n in ancestors if n in ordered]
            stage["depends_on"] = [n for n in dependencies if not any(n != other and n in self.ancestors(other) for other in dependencies)]
        for node_id, node in self.nodes.items():
            if NODES.get(node["class_type"], {}).get("kind") == "encoder" and node_id not in self.used_encoders:
                info["unassigned"] += self.trace(node_id, 0, "unassigned")
        if not info['stages'] and not info['unassigned']:
            for node_id in self.nodes:
                if self.node(node_id)['class_type'] not in NODES:
                    self.issue('unsupported_node', node_id)
        all_props = [p for s in info["stages"] for p in s["properties"]]
        for p in all_props:
            target = "models" if p["id"] == "model" else "loras" if p["id"] == "lora" else None
            value = p["value"].get("name") if p["id"] == "lora" and isinstance(p["value"], dict) else p["value"]
            if target and isinstance(value, str) and value not in info[target]:
                info[target].append(value)
        if len(info["branches"]) == 1 and info["branches"][0]["association"] == "unique":
            samplers = [s for s in info["stages"] if s["kind"] == "sampling"]
            terminal = [s for s in samplers if not any(s["id"] != other["id"] and s["id"] in self.ancestors(other["id"]) for other in samplers)]
            if len(terminal) == 1:
                for role in ("positive", "negative"):
                    values = [p for p in terminal[0]["properties"] if p["id"] == role and isinstance(p["value"], str)]
                    info[role + "_prompt"] = "\n\n".join((f"[{p.get('channel', role)}]\n" if len(values) > 1 else "") + p["value"] for p in values)
        info["diagnostics"] = self.diagnostics
        info["parse_status"] = "partial" if self.diagnostics or any(p["state"] == "unknown" for p in all_props + info['unassigned']) else "complete"
        return info


def parse_execution_graph(graph):
    """接受已解码的执行图；属性错误以局部诊断形式返回。"""
    if not isinstance(graph, dict):
        result = empty_metadata()
        result["parse_status"] = "invalid"
        return result
    return GraphParser(graph).parse()
