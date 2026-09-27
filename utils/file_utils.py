"""快速枚举目录；失败交由调用方处理，单个消失文件直接跳过。"""
import os
from pathlib import Path
from ..constants import WHITE_EXTENSIONS
from .path_utils import resolve_folder_path, resolve_file_path
from ..timing.storage import file_lock


def get_target_folder_files(folder_path,folder_type='outputs'):
    target = resolve_folder_path(folder_type,folder_path)
    files = []
    with os.scandir(target) as entries:
        for item in entries:
            if item.name.startswith('.'):
                continue
            try:
                resolved=resolve_file_path(folder_type,folder_path,item.name)
                with file_lock(resolved):
                    stat = item.stat()
                    is_dir = item.is_dir()
                if not is_dir and Path(item.name).suffix.lower() not in WHITE_EXTENSIONS:
                    continue
                files.append({'type':'dir' if is_dir else 'file','name':item.name,
                              'bytes':0 if is_dir else stat.st_size,'created_at':stat.st_ctime,
                              'mtime':stat.st_mtime,'mtime_ns':stat.st_mtime_ns,
                              'folder_path':folder_path,'notes':''})
            except (FileNotFoundError,ValueError):
                continue
    return sorted(files,key=lambda item:(item['type']!='dir',-item['created_at']))
