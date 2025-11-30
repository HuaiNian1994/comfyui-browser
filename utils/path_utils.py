"""路径处理工具"""
import time
from pathlib import Path
from typing import Literal

from ..config import get_collections_path, get_sources_path, get_outputs_path
from ..constants import INFO_FILE_SUFFIX

FolderType = Literal['outputs', 'collections', 'sources']


def get_parent_path(folder_type: FolderType) -> str:
    """
    根据folder_type获取父路径
    
    Args:
        folder_type: 文件夹类型,可选值: 'outputs', 'collections', 'sources'
        
    Returns:
        对应类型的路径字符串
    """
    if folder_type == 'collections':
        return get_collections_path()
    if folder_type == 'sources':
        return get_sources_path()
    return get_outputs_path()


def get_info_filename(filename: str) -> str:
    """
    获取info文件名
    
    Args:
        filename: 原始文件名
        
    Returns:
        添加.info后缀的文件名
    """
    return str(Path(filename).with_suffix(INFO_FILE_SUFFIX))


def add_uuid_to_filename(filename: str) -> str:
    """
    在文件名中添加时间戳作为UUID
    
    Args:
        filename: 原始文件名
        
    Returns:
        添加时间戳后的文件名,格式: name_timestamp.ext
    """
    p = Path(filename)
    return f'{p.stem}_{int(time.time())}{p.suffix}'
