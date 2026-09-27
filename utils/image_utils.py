"""读取图片封装并调用独立的执行图解析器。"""
from __future__ import annotations

import json
import struct
from pathlib import Path

from PIL import Image

from ..metadata.graph import empty_metadata, parse_execution_graph
from ..timing.storage import read_summary


def _read_apng_prompt(image_path):
    """读取官方 APNG 位于图像数据后的 comf 块。"""
    with open(image_path, "rb") as stream:
        if stream.read(8) != b"\x89PNG\r\n\x1a\n":
            return None
        file_size = Path(image_path).stat().st_size
        while stream.tell() + 12 <= file_size:
            length, kind = struct.unpack(">I4s", stream.read(8))
            if stream.tell() + length + 4 > file_size:
                raise ValueError("truncated_png_chunk")
            if kind == b"comf":
                data = stream.read(length)
                key, separator, value = data.partition(b"\0")
                if separator and key == b"prompt":
                    return value.decode("latin-1")
            else:
                stream.seek(length, 1)
            stream.seek(4, 1)
            if kind == b"IEND":
                break
    return None


def extract_detailed_metadata(image_path: str) -> dict:
    """基础信息独立保留；文件读取错误交由索引队列记录失败。"""
    with Image.open(image_path) as image:
        width, height = image.size
        image_format = image.format
        raw = None
        result = empty_metadata()
        try:
            if image_format == "PNG":
                raw = image.info.get("prompt")
                if raw is None:
                    raw = _read_apng_prompt(image_path)
            elif image_format == "WEBP":
                value = image.getexif().get(0x0110)
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                if isinstance(value, str) and value.startswith("prompt:"):
                    raw = value[len("prompt:"):]
            else:
                result["parse_status"] = "unsupported_container"
            if raw is not None:
                result = parse_execution_graph(json.loads(raw) if isinstance(raw, (str, bytes)) else raw)
        except (ValueError, TypeError, UnicodeError, struct.error) as exc:
            result = empty_metadata()
            result.update(parse_status="invalid", diagnostics=[{"code": "invalid_metadata", "node_id": "", "class_type": "", "field": "prompt", "detail": type(exc).__name__}])
        result.update(width=width, height=height, image_format=image_format)
        timing, pending = read_summary(image_path)
        if timing:
            result["generation_timing"] = timing
        result["timing_pending"] = pending
        return result


def extract_comfyui_png_metadata(image_path: str) -> dict:
    """保留提示词接口；所有字段由统一解析结果提供。"""
    info = extract_detailed_metadata(image_path)
    return {"positive": info["positive_prompt"], "negative": info["negative_prompt"],
            "has_metadata": info["has_metadata"], "formatted_info": info}


def _parse_positive_and_negative_prompts(prompt_json: dict) -> tuple[str, str]:
    """正反向仅来自唯一输出关联的末端采样阶段。"""
    info = parse_execution_graph(prompt_json)
    return info["positive_prompt"], info["negative_prompt"]
