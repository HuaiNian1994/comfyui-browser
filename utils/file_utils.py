"""文件操作工具"""
import json
from pathlib import Path
from typing import List, Dict, Any
from os import scandir

from ..constants import WHITE_EXTENSIONS
from .path_utils import get_parent_path, get_info_filename, FolderType


def get_target_folder_files(folder_path: str, folder_type: FolderType = 'outputs') -> List[Dict[str, Any]]:
    """
    获取目标文件夹的文件列表
    
    Args:
        folder_path: 文件夹路径
        folder_type: 文件夹类型
        
    Returns:
        文件信息列表,每个元素包含: type, name, bytes, created_at, folder_path, notes
    """
    # 防止路径遍历攻击
    if '..' in folder_path:
        return []

    parent_path = Path(get_parent_path(folder_type))
    target_path = parent_path / folder_path

    if not target_path.exists():
        return []

    files = []
    folder_listing = sorted(
        scandir(target_path),
        key=lambda f: (f.is_file(), -f.stat().st_ctime)
    )
    
    for item in folder_listing:
        if not Path(item.path).exists():
            continue

        name = Path(item.path).name
        # 忽略隐藏文件
        if not name or name.startswith('.'):
            continue

        ext = Path(name).suffix.lower()
        # 只包含白名单中的文件类型
        if item.is_file() and ext not in WHITE_EXTENSIONS:
            continue

        stat = item.stat()
        created_at = stat.st_ctime
        mtime = stat.st_mtime
        bytes_size = stat.st_size if item.is_file() else 0
        
        info_file_path = get_info_filename(item.path)
        notes = ""
        
        # 读取.info文件中的notes
        if Path(info_file_path).exists():
            try:
                with open(info_file_path, 'r', encoding='utf-8') as f:
                    info_data = json.load(f)
                    notes = info_data.get("notes", "")
            except Exception:
                pass

        file_info = {
            "type": "dir" if item.is_dir() else "file",
            "name": name,
            "bytes": bytes_size,
            "created_at": created_at,
            "mtime": mtime,
            "folder_path": folder_path,
            "notes": notes
        }
        files.append(file_info)

    return files
