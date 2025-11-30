"""图片处理工具"""
import json
from pathlib import Path
from typing import Dict, Any

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
            positive, negative = _parse_clip_text_encode(prompt_data)
            return {
                "positive": positive,
                "negative": negative,
                "has_metadata": True
            }
        
        return {"positive": "", "negative": "", "has_metadata": False}
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {"positive": "", "negative": "", "has_metadata": False}


def _parse_clip_text_encode(prompt_json: Dict[str, Any]) -> tuple[str, str]:
    """
    从prompt JSON中提取正向和反向提示词
    
    ComfyUI的prompt格式:
    {
        "node_id": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "提示词内容"
            }
        }
    }
    
    Args:
        prompt_json: ComfyUI的prompt JSON数据
        
    Returns:
        (positive_text, negative_text) 元组
    """
    positive_text = ""
    negative_text = ""
    
    # 收集所有CLIPTextEncode节点
    clip_text_nodes = []
    for node_id, node_data in prompt_json.items():
        if node_data.get("class_type") == "CLIPTextEncode":
            text = node_data.get("inputs", {}).get("text", "")
            clip_text_nodes.append((node_id, text))
    
    # 通常第一个是positive,第二个是negative
    if len(clip_text_nodes) >= 1:
        positive_text = clip_text_nodes[0][1]
    if len(clip_text_nodes) >= 2:
        negative_text = clip_text_nodes[1][1]
    
    return positive_text, negative_text
