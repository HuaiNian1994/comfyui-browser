"""图片处理工具"""
import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from PIL import Image
except ImportError:
    Image = None


def extract_comfyui_png_metadata(image_path: str) -> Dict[str, Any]:
    """
    从ComfyUI生成的PNG中提取workflow和prompt元数据
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        包含positive, negative和has_metadata的字典
    """
    if Image is None:
        return {"positive": "", "negative": "", "has_metadata": False}
    
    try:
        img = Image.open(image_path)
        prompt = img.info.get('prompt')
        
        if prompt:
            prompt_data = json.loads(prompt)
            positive_prompt, negative_prompt = _parse_positive_and_negative_prompts(prompt_data)
            return {
                "positive": positive_prompt,
                "negative": negative_prompt,
                "has_metadata": True
            }
        
        return {"positive": "", "negative": "", "has_metadata": False}
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {"positive": "", "negative": "", "has_metadata": False}


_PROMPT_INPUT_NAME_BY_ENCODER_CLASS: Dict[str, str] = {
    "CLIPTextEncode": "text",
    "TextEncodeKrea2": "prompt",
}

_SAMPLER_CLASS_TYPES_WITH_CONDITIONING = {
    "KSampler",
    "KSamplerAdvanced",
    "SamplerCustom",
}


def _prompt_string_from_encoder_node(node_data: Any) -> Optional[str]:
    """已知文本节点且提示词字段是字符串时返回该字符串，否则返回 None。"""
    if not isinstance(node_data, dict):
        return None
    prompt_input_name = _PROMPT_INPUT_NAME_BY_ENCODER_CLASS.get(node_data.get("class_type"))
    if prompt_input_name is None:
        return None
    node_inputs = node_data.get("inputs")
    if not isinstance(node_inputs, dict):
        return None
    prompt_value = node_inputs.get(prompt_input_name)
    if not isinstance(prompt_value, str):
        return None
    return prompt_value


def _resolved_prompt_from_conditioning_link(prompt_json: Dict[str, Any], conditioning_link: Any) -> Optional[str]:
    """连线直接指向文本节点且字段为字符串时返回提示词。连线或非文本节点返回 None。"""
    if not isinstance(conditioning_link, (list, tuple)) or len(conditioning_link) < 2:
        return None
    linked_node = prompt_json.get(str(conditioning_link[0]))
    return _prompt_string_from_encoder_node(linked_node)


def _positive_and_negative_from_first_resolved_sampler(prompt_json: Dict[str, Any]) -> Optional[tuple[str, str]]:
    """按对象顺序取第一个至少一侧解析成功的采样器。都没有则返回 None。"""
    for node_data in prompt_json.values():
        if not isinstance(node_data, dict):
            continue
        if node_data.get("class_type") not in _SAMPLER_CLASS_TYPES_WITH_CONDITIONING:
            continue
        node_inputs = node_data.get("inputs")
        if not isinstance(node_inputs, dict):
            continue
        positive_prompt = _resolved_prompt_from_conditioning_link(prompt_json, node_inputs.get("positive"))
        negative_prompt = _resolved_prompt_from_conditioning_link(prompt_json, node_inputs.get("negative"))
        if positive_prompt is None and negative_prompt is None:
            continue
        return positive_prompt or "", negative_prompt or ""
    return None


def _positive_and_negative_from_encoder_order(prompt_json: Dict[str, Any]) -> tuple[str, str]:
    """按对象顺序取前两个文本节点，分别作为正向和反向。"""
    prompt_strings: list[str] = []
    for node_data in prompt_json.values():
        prompt_string = _prompt_string_from_encoder_node(node_data)
        if prompt_string is None:
            continue
        prompt_strings.append(prompt_string)
        if len(prompt_strings) == 2:
            break
    positive_prompt = prompt_strings[0] if prompt_strings else ""
    negative_prompt = prompt_strings[1] if len(prompt_strings) > 1 else ""
    return positive_prompt, negative_prompt


def _parse_positive_and_negative_prompts(prompt_json: Dict[str, Any]) -> tuple[str, str]:
    """优先按采样器连线取正反向提示词；两侧都未解析到文本节点时按 JSON 顺序回退。"""
    if not isinstance(prompt_json, dict):
        return "", ""
    prompts_from_sampler = _positive_and_negative_from_first_resolved_sampler(prompt_json)
    if prompts_from_sampler is not None:
        return prompts_from_sampler
    return _positive_and_negative_from_encoder_order(prompt_json)

def extract_detailed_metadata(image_path: str) -> Dict[str, Any]:
    """
    提取详细的元数据，包括 Models, Loras 等
    """
    if Image is None:
        return {"models": [], "loras": [], "width": 0, "height": 0}
        
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        info = {
            "models": [],
            "loras": [],
            "positive_prompt": "",
            "negative_prompt": "",
            "width": width,
            "height": height
        }
        
        # 打印原始 PNG info，方便查看最初嵌入的全部字段
        try:
            print(json.dumps({"image_path": image_path, "raw_info": img.info}, ensure_ascii=False, indent=2))
        except Exception:
            pass

        prompt = img.info.get('prompt')
        if prompt:
            prompt_data = json.loads(prompt)
            
            # Extract prompts
            positive_prompt, negative_prompt = _parse_positive_and_negative_prompts(prompt_data)
            info["positive_prompt"] = positive_prompt
            info["negative_prompt"] = negative_prompt

            # 遍历节点提取信息
            for node in prompt_data.values():
                class_type = node.get("class_type", "")
                inputs = node.get("inputs", {})
                
                # Checkpoints
                if "CheckpointLoader" in class_type:
                    ckpt = inputs.get("ckpt_name")
                    if ckpt and ckpt not in info["models"]:
                        info["models"].append(ckpt)
                
                # UNet loaders (append到 models，前端使用 models 展示主模型信息)
                if "UNETLoader" in class_type:
                    unet = inputs.get("unet_name")
                    if unet and unet not in info["models"]:
                        info["models"].append(unet)
                
                # Loras
                if "LoraLoader" in class_type:
                    lora = inputs.get("lora_name")
                    if lora and lora not in info["loras"]:
                        info["loras"].append(lora)
                
                # LoRA (model-only variant)
                if "LoraLoaderModelOnly" in class_type:
                    lora_model_only = inputs.get("lora_name")
                    if lora_model_only and lora_model_only not in info["loras"]:
                        info["loras"].append(lora_model_only)
                        
        return info
    except Exception as e:
        print(f"Error extracting detailed metadata for {image_path}: {e}")
        return {"models": [], "loras": [], "width": 0, "height": 0}
