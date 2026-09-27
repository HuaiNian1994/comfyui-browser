"""节点适配及属性定义；维护清单直接从本模块生成。"""
from __future__ import annotations

import json
from pathlib import Path

PARSER_VERSION = 3
CONTRACT_PATH = Path(__file__).with_name("node_contracts.json")
CONTRACTS = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["nodes"]

# 属性标识同时用于 API、翻译和维护文档。
ATTRIBUTES = {
    "positive": ("prompts", "正向提示词", "Positive prompt"),
    "negative": ("prompts", "反向提示词", "Negative prompt"),
    "system_prompt": ("prompts", "系统提示词", "System prompt"),
    "unassigned": ("prompts", "未归属提示词", "Unassigned prompt"),
    "conditioning": ("prompts", "条件处理", "Conditioning"),
    "model": ("models", "主模型", "Model"),
    "clip": ("models", "文本编码器", "Text encoder"),
    "vae": ("models", "变分自编码器", "VAE"),
    "lora": ("models", "LoRA 及权重", "LoRA and strengths"),
    "model_settings": ("models", "模型与编码器设置", "Model / encoder settings"),
    "seed": ("sampling", "采样种子", "Sampling seed"),
    "steps": ("sampling", "配置步数", "Configured steps"),
    "stage_steps": ("sampling", "阶段步数", "Stage steps"),
    "sampler": ("sampling", "采样器", "Sampler"),
    "scheduler": ("sampling", "调度器", "Scheduler"),
    "cfg": ("sampling", "CFG 引导强度", "CFG"),
    "guidance": ("sampling", "模型引导强度", "Model guidance"),
    "denoise": ("sampling", "降噪", "Denoise"),
    "start_at_step": ("sampling", "起始步数", "Start step"),
    "end_at_step": ("sampling", "结束步数", "End step"),
    "add_noise": ("sampling", "添加噪声", "Add noise"),
    "return_with_leftover_noise": ("sampling", "保留剩余噪声", "Return leftover noise"),
    "sampling_settings": ("sampling", "采样与噪声设置", "Sampling / noise settings"),
    "width": ("dimensions", "生成宽度", "Generation width"),
    "height": ("dimensions", "生成高度", "Generation height"),
    "batch_size": ("dimensions", "批量大小", "Batch size"),
    "controlnet": ("control", "ControlNet", "ControlNet"),
    "control_settings": ("control", "控制条件设置", "Control settings"),
    "upscale_model": ("processing", "放大模型", "Upscale model"),
    "upscale_method": ("processing", "缩放算法", "Resize method"),
    "scale_by": ("processing", "缩放倍率", "Scale factor"),
    "target_width": ("processing", "目标宽度", "Target width"),
    "target_height": ("processing", "目标高度", "Target height"),
    "grow_mask_by": ("processing", "遮罩扩展", "Mask expansion"),
    "noise_mask": ("processing", "噪声遮罩", "Noise mask"),
    "processing_settings": ("processing", "图像处理设置", "Image processing settings"),
}
NODES: dict[str, dict] = {}


def register(names, kind, **settings):
    """只登记基线中实际存在的类名，历史显式别名单独保留。"""
    for name in names.split("|") if isinstance(names, str) else names:
        if name in CONTRACTS:
            NODES[name] = {"kind": kind, **settings}


register("KSampler|KSamplerAdvanced|SamplerCustom|SamplerCustomAdvanced", "sample")
register("SaveImage|PreviewImage|SaveImageAdvanced|SaveAnimatedPNG|SaveAnimatedWEBP", "output")
register("CLIPTextEncode|CLIPTextEncodeSDXL|CLIPTextEncodeSDXLRefiner|CLIPTextEncodeSD3|CLIPTextEncodeFlux|CLIPTextEncodeHiDream|CLIPTextEncodeHunyuanDiT|CLIPTextEncodeLumina2|CLIPTextEncodePixArtAlpha|CLIPTextEncodeKandinsky5|TextEncodeQwenImageEdit|TextEncodeQwenImageEditPlus|TextEncodeQwenImage21|TextEncodeMageFlowEdit|TextEncodeJoyImageEdit|TextEncodeBooguEdit|TextEncodeZImageOmni|TextEncodeKrea2", "encoder")
register("CheckpointLoader|CheckpointLoaderSimple|unCLIPCheckpointLoader|ImageOnlyCheckpointLoader|Checkpoint Loader (LoraManager)|Random Checkpoint Loader (LoraManager)", "checkpoint", fields=["ckpt_name"])
register("UNETLoader|UnetLoaderGGUF|UnetLoaderGGUFAdvanced|Unet Loader (LoraManager)|Random Unet Loader (LoraManager)", "loader", resource="model", fields=["unet_name"])
register("DiffusersLoader", "checkpoint", fields=["model_path"])
register("CLIPLoader|DualCLIPLoader|TripleCLIPLoader|QuadrupleCLIPLoader|CLIPLoaderGGUF|DualCLIPLoaderGGUF|TripleCLIPLoaderGGUF|QuadrupleCLIPLoaderGGUF", "loader", resource="clip", fields=["clip_name", "clip_name1", "clip_name2", "clip_name3", "clip_name4"])
register("VAELoader", "loader", resource="vae", fields=["vae_name"])
register("ControlNetLoader|DiffControlNetLoader", "loader", resource="controlnet", fields=["control_net_name"])
register("UpscaleModelLoader|LatentUpscaleModelLoader", "loader", resource="upscale_model", fields=["model_name"])
register("LoraLoader|LoraLoaderModelOnly|LoraLoaderBypass|LoraLoaderBypassModelOnly|LoraModelLoader|Lora Loader Stack (rgthree)|Power Lora Loader (rgthree)|Lora Loader (LoraManager)|LoRA Text Loader (LoraManager)", "lora")
register("CFGGuider|BasicGuider|DualCFGGuider|DualModelGuider|PerpNegGuider", "guider")
register("RandomNoise|DisableNoise", "noise")
register("SplitSigmas|SplitSigmasDenoise|FlipSigmas|SetFirstSigma|ExtendIntermediateSigmas|ManualSigmas", "sigmas")
register("KSampler Config (rgthree)", "config")
register("PrimitiveString|PrimitiveStringMultiline|PrimitiveInt|PrimitiveFloat|PrimitiveBoolean|Seed (rgthree)|Power Primitive (rgthree)|Krea2SystemPrompt", "primitive")
register("Context (rgthree)|Context Big (rgthree)|Context Merge (rgthree)|Context Merge Big (rgthree)|Context Switch (rgthree)|Context Switch Big (rgthree)|Any Switch (rgthree)", "context")
register("VAEEncode|VAEEncodeTiled|VAEDecode|VAEDecodeTiled|VAEEncodeForInpaint|InpaintModelConditioning|SetLatentNoiseMask|RepeatLatentBatch|LatentFromBatch|RebatchLatents|LatentBatch|LatentComposite|LatentCompositeMasked|LatentCrop|LatentRotate|LatentFlip|ImageScale|ImageScaleBy|ImageScaleToTotalPixels|ImageUpscaleWithModel|LatentUpscale|LatentUpscaleBy|ImageCompositeMasked|ImagePadForOutpaint|ImageCrop|ImageBatch|ImageFromBatch|RepeatImageBatch|EmptyImage|EmptyLatentImage|EmptySD3LatentImage|EmptyFlux2LatentImage|EmptyHunyuanImageLatent|StableCascade_EmptyLatentImage|StableCascade_StageC_VAEEncode|LoadImage|LoadImageMask|GetImageSize|ImageOnlyCheckpointLoader|FluxKontextImageScale|ReferenceLatent|ConditioningSetArea|ConditioningSetMask|ConditioningSetAreaPercentage|ConditioningSetTimestepRange|ConditioningAverage|ConditioningCombine|ConditioningConcat|ConditioningZeroOut|ControlNetApply|ControlNetApplyAdvanced|ControlNetApplySD3|ControlNetInpaintingAliMamaApply|SetUnionControlNetType|FluxGuidance|FluxDisableGuidance|CLIPSetLastLayer|CLIPTextEncodeControlnet|StableCascade_StageB_Conditioning|InstructPixToPixConditioning|StableZero123_Conditioning|unCLIPConditioning|GLIGENTextBoxApply|StyleModelApply|CLIPVisionEncode|Canny|GrowMask|InvertMask|ThresholdMask|JoinImageWithAlpha|DifferentialDiffusion|CFGNorm|FreSca|T5TokenizerOptions|SD_4XUpscale_Conditioning|QwenImageDiffsynthControlnet|ZImageFunControlnet", "transform")
# 下列模块的节点通过标准数据端口传递资源；数值设置完整保留。
for name, contract in CONTRACTS.items():
    module = contract["module"]
    if name in NODES:
        continue
    if module == "comfy_extras.nodes_custom_sampler":
        if "SIGMAS" in contract["outputs"] and "sigmas" not in contract["inputs"]:
            register([name], "scheduler")
        elif "SAMPLER" in contract["outputs"]:
            register([name], "sampler")
    elif module in {"comfy_extras.nodes_align_your_steps", "comfy_extras.nodes_gits", "comfy_extras.nodes_optimalsteps"} or name in {"Flux2Scheduler", "Ideogram4Scheduler"}:
        register([name], "scheduler")
    elif module.startswith("comfy_extras.nodes_model_merging") or module in {
        "comfy_extras.nodes_model_advanced", "comfy_extras.nodes_freelunch",
        "comfy_extras.nodes_sag", "comfy_extras.nodes_slg", "comfy_extras.nodes_pag",
        "comfy_extras.nodes_apg", "comfy_extras.nodes_tcfg", "comfy_extras.nodes_cfg",
        "comfy_extras.nodes_hypertile", "comfy_extras.nodes_tomesd",
        "comfy_extras.nodes_attention_multiply", "comfy_extras.nodes_model_downscale",
    }:
        register([name], "transform")
    elif module == "comfy_extras.nodes_advanced_samplers":
        register([name], "sampler")

register("StyleModelLoader|CLIPVisionLoader|GLIGENLoader|PhotoMakerLoader|ModelPatchLoader|HypernetworkLoader", "auxiliary")
register("Save Image (LoraManager)", "output")
register("Power Prompt (rgthree)|Power Prompt - Simple (rgthree)|SDXL Power Prompt - Positive (rgthree)|SDXL Power Prompt - Simple / Negative (rgthree)|Prompt (LoraManager)", "encoder")
register("Lora Stacker (LoraManager)|Lora Stack Combiner (LoraManager)|Lora Randomizer (LoraManager)|Lora Cycler (LoraManager)", "lora_stack")
register("StringConcatenate|StringSubstring|StringLength|StringReplace|StringTrim|CaseConverter|StringCompare|StringContains|StringFormat|JsonExtractString|ConvertArrayToString|ConvertDictionaryToString|RegexReplace|RegexMatch|RegexExtract|ComfyNotNode|ComfySwitchNode|ComfyAndNode|ComfyOrNode|Text (LoraManager)|CustomCombo", "value")
register("SDXL Empty Latent Image (rgthree)|Image Resize (rgthree)|Image Inset Crop (rgthree)|Image or Latent Size (rgthree)|AddNoise|CFGOverride|FluxKVCache|FluxKontextMultiReferenceLatentMethod", "transform")
register("ConditioningMultiply|ConditioningSetAreaStrength|ConditioningSetDefaultCombine|ConditioningSetProperties|ConditioningSetPropertiesAndCombine|PairConditioningCombine|PairConditioningSetDefaultCombine|PairConditioningSetProperties|PairConditioningSetPropertiesAndCombine|SetClipHooks|SetHookKeyframes|CombineHooks2|CombineHooks4|CombineHooks8|CreateHookKeyframe|CreateHookKeyframesFromFloats|CreateHookKeyframesInterpolated|ConditioningTimestepsRange|EmptyQwenImageLayeredLatentImage|ImageAddNoise|ImageColorSpace|ImageFlip|ImageInvert|ImageRotate|LatentAdd|LatentSubtract|LatentBlend|LatentInterpolate|LatentMultiply|LatentBatchSeedBehavior|LatentApplyOperation|LatentApplyOperationCFG|LatentOperationSharpen|LatentOperationTonemapReinhard|LoadImageOutput|LoadLatent|QwenImage21Cache|SaveConditioning|SaveLatent|SkipLayerGuidanceSD3|ResizeAndPadImage", "transform")
register("CreateHookLora|CreateHookLoraModelOnly|Create Hook LoRA (LoraManager)", "lora")
register("ConditioningLoader", "external")
register("ResolutionSelector", "value")
register("CLIPTextEncodeControlnet", "encoder")
# 冻结契约中的单资源变换具有唯一来源，按该资源端口保留配置。
for name, contract in CONTRACTS.items():
    if name in NODES or not contract['module'].startswith('comfy_extras.'):
        continue
    for resource_type in ('MODEL', 'CLIP', 'VAE', 'CONDITIONING'):
        matching = [field for field, spec in contract['inputs'].items() if spec['type'] == resource_type]
        if contract['outputs'] == [resource_type] and len(matching) == 1:
            register([name], 'transform')
            break
# 资源加载器优先于图像传递分类。
register("ImageOnlyCheckpointLoader", "checkpoint", fields=["ckpt_name"])

TEXT_FIELDS = ("text", "prompt", "user_prompt", "text_g", "text_l", "prompt_g", "prompt_l", "clip_l", "clip_g", "t5xxl", "llama", "bert", "mt5xl", "qwen25_7b")
DIRECT_FIELDS = {
    "seed": "seed", "noise_seed": "seed", "steps": "steps", "steps_total": "steps",
    "cfg": "cfg", "cfg_conds": "cfg", "cfg_cond2_negative": "cfg", "guidance": "guidance",
    "denoise": "denoise", "start_at_step": "start_at_step", "end_at_step": "end_at_step",
    "add_noise": "add_noise", "return_with_leftover_noise": "return_with_leftover_noise",
    "sampler_name": "sampler", "scheduler": "scheduler", "batch_size": "batch_size",
    "upscale_method": "upscale_method", "scale_by": "scale_by", "scale_ratio": "scale_by",
    "grow_mask_by": "grow_mask_by", "noise_mask": "noise_mask",
}


def node_contract(class_type):
    return CONTRACTS.get(class_type, {"inputs": {}, "outputs": [], "output_names": [], "module": "unknown"})


def property_ids(name, spec):
    """用于维护清单的直接属性；传递属性由消费端确定。"""
    fields = set(CONTRACTS[name]['inputs'])
    ids = {DIRECT_FIELDS[f] for f in fields if f in DIRECT_FIELDS}
    kind = spec['kind']
    if kind in {'encoder', 'guider'}: ids.update({'positive', 'negative', 'system_prompt', 'clip'})
    if kind == 'checkpoint': ids.update({'model', 'clip', 'vae'})
    if kind == 'loader': ids.add(spec['resource'])
    if kind in {'lora', 'lora_stack'}: ids.add('lora')
    if kind == 'sample': ids.update({'stage_steps', 'model', 'positive', 'negative', 'width', 'height', 'batch_size'})
    if kind == 'scheduler': ids.add('scheduler')
    if kind == 'sampler': ids.add('sampler')
    if kind in {'transform', 'auxiliary'}:
        ids.update(f for f in ('width', 'height', 'batch_size', 'target_width', 'target_height') if f in fields)
        ids.add('control_settings' if 'Control' in name or 'Conditioning' in name else 'model_settings' if any(t in {'MODEL','CLIP','VAE'} for t in CONTRACTS[name]['outputs']) else 'processing_settings')
    return sorted(ids)


def timing_rule(name, spec):
    """计时分类与静态节点登记使用同一份准确类名清单。"""
    kind = spec['kind']
    category = {'sample': 'sampling', 'checkpoint': 'model_loading', 'loader': 'model_loading',
                'lora': 'lora_application', 'lora_stack': 'lora_application', 'encoder': 'text_encoding',
                'output': 'image_save'}.get(kind, 'node_other')
    if name.startswith('VAEEncode'): category = 'vae_encode'
    elif name.startswith('VAEDecode'): category = 'vae_decode'
    elif name.startswith('LoadImage') or 'Preprocessor' in name: category = 'input_control'
    elif category == 'node_other' and kind in ('transform', 'auxiliary') and any(x in name for x in ('Image', 'Mask', 'Control', 'Upscale', 'Latent')): category = 'postprocess'
    return {'category': category, 'resource': spec.get('resource'), 'node_call': True,
            'internal': 'standard_sampler_and_resource_hooks', 'basis': 'ComfyUI 0.37.0 function calls',
            'limitation': '扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。'}


for _name, _spec in NODES.items():
    _spec['timing'] = timing_rule(_name, _spec)
    _spec['attributes'] = property_ids(_name, _spec)
    _spec['module'] = CONTRACTS[_name]['module']
    _spec['contract'] = _name
    _spec['tests'] = ['tests/test_execution_graph.py']
    _spec['status'] = 'static_with_runtime_limits'
    _spec['limitation'] = '外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。'
