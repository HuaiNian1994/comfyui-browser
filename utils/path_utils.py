"""路径处理工具"""
import time
import uuid
import os
from ..services.directory_registry import DirectoryRegistry

directory_registry = DirectoryRegistry()
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
    在文件名中添加纳秒时间戳与随机标识
    
    Args:
        filename: 原始文件名
        
    Returns:
        新文件名格式: name_timestamp_random.ext
    """
    p = Path(filename)
    return f'{p.stem}_{time.time_ns()}_{uuid.uuid4().hex[:8]}{p.suffix}'

def _folder_root(folder_type,folder_path):
    """虚拟路径只解引用已登记的外部根，其余路径继续使用原配置根。"""
    if folder_type not in {'outputs','collections','sources'} or not isinstance(folder_path,str):
        raise ValueError('Invalid folder identity')
    relative=folder_path.replace('\\','/')
    if relative.startswith('/') or ':' in relative or '\x00' in relative or '..' in relative.split('/'):
        raise ValueError('Invalid folder path')
    parts=[part for part in relative.split('/') if part and part!='.']
    if parts and parts[0]=='@external':
        if folder_type!='outputs' or len(parts)<2:
            raise ValueError('Invalid external directory')
        return directory_registry.external_root(parts[1]),parts[2:]
    return os.path.realpath(get_parent_path(folder_type)),parts


def _resolve_beneath(base,parts):
    current=base
    for part in parts:
        current=os.path.realpath(os.path.join(current,part))
        try:
            contained=os.path.normcase(os.path.commonpath([base,current]))==os.path.normcase(base)
        except ValueError:
            contained=False
        if not contained:
            raise ValueError('Path escapes registered directory')
    return current


def resolve_folder_path(folder_type: FolderType,folder_path: str='') -> str:
    """逐层校验目录与符号链接，返回登记根以内的真实路径。"""
    base,parts=_folder_root(folder_type,folder_path)
    return _resolve_beneath(base,parts)


def resolve_file_path(folder_type: FolderType,folder_path: str,filename: str) -> str:
    if not isinstance(filename,str) or not filename or filename in {'.','..'} or any(c in filename for c in '/\\:\x00'):
        raise ValueError('Invalid filename')
    base,parts=_folder_root(folder_type,folder_path)
    return _resolve_beneath(base,parts+[filename])


def resolve_sidecar_path(folder_type,folder_path,filename):
    return resolve_file_path(folder_type,folder_path,get_info_filename(filename))


def file_version_from_stat(stat) -> str:
    return f'{stat.st_mtime_ns}:{stat.st_size}'
