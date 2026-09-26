from aiohttp import web
import json
from os import path
import os
import shutil
import subprocess
import sys

from ..utils import get_target_folder_files, get_parent_path, get_info_filename, extract_comfyui_png_metadata, extract_detailed_metadata
from ..constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from ..services.db_service import DBService
from ..services.metadata_indexer import MetadataIndexQueue, MetadataIndexTask
from ..metadata.registry import PARSER_VERSION

db_service = DBService()
metadata_index_queue = MetadataIndexQueue(db_service, extract_detailed_metadata)

# 首次列表仅返回基础信息，不在请求路径中同步提取图片元数据，避免阻塞
INLINE_METADATA_SYNC_LIMIT = 0

def normalize_folder_path(folder_path: str) -> str:
    """
    将前端传入的路径标准化为相对路径，统一分隔符并去除首尾的分隔符。
    """
    if not folder_path:
        return ''
    return folder_path.strip('/').replace('\\', '/')


def update_file_info(file_path, notes=None, tags=None):
    """辅助函数：更新 .info 文件中的 notes 和 tags"""
    info_file_path = get_info_filename(file_path)
    info_data = {}
    
    # 1. 读取现有数据 (如果存在)
    if path.exists(info_file_path):
        try:
            with open(info_file_path, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
        except Exception:
            pass # 如果读取失败，就覆盖它
            
    # 2. 更新字段
    if notes is not None:
        info_data['notes'] = notes
    if tags is not None:
        info_data['tags'] = tags
        
    # 3. 写入文件
    try:
        with open(info_file_path, 'w', encoding='utf-8') as f:
            json.dump(info_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error writing info file {info_file_path}: {e}")


def create_metadata_task(record, full_path, folder_path, folder_type):
    """任务保存精确文件版本，后台写入同时核验记录身份。"""
    stat = os.stat(full_path)
    return MetadataIndexTask(
        filename=record['filename'], folder_path=folder_path, folder_type=folder_type,
        file_path=full_path, bytes_size=record['bytes'], created_at=record['created_at'],
        mtime=record['mtime'], mtime_ns=stat.st_mtime_ns, hash_val=record['hash'],
        record_id=record.get('id'),
    )


def schedule_file_metadata(record, full_path, folder_path, folder_type, queue, force=False):
    """版本过期自动补齐；已失败的同版本任务由用户刷新重试。"""
    if path.splitext(record['filename'])[1].lower() not in IMAGE_EXTENSIONS:
        return 'complete'
    task = create_metadata_task(record, full_path, folder_path, folder_type)
    info = record.get('formatted_info') or {}
    outdated = info.get('parser_version') != PARSER_VERSION
    if queue and (force or outdated):
        queue.enqueue(task, force=force)
    return (queue.status(task) if queue else None) or info.get('index_status', 'waiting' if outdated else 'complete')


def synchronize_folder(
    folder_path: str,
    folder_type: str,
    metadata_limit: int = INLINE_METADATA_SYNC_LIMIT,
    metadata_queue: MetadataIndexQueue = metadata_index_queue,
    database: DBService = db_service
):
    """快速同步文件身份，图片属性由后台队列按解析版本补齐。"""
    normalized = normalize_folder_path(folder_path)
    disk_files = get_target_folder_files(normalized, folder_type=folder_type)
    if disk_files is None:
        return []
    records = database.get_files_in_folder(normalized, folder_type)
    parent = get_parent_path(folder_type)
    disk_names = {item['name'] for item in disk_files}
    removed = [name for name in records if name not in disk_names]
    if removed:
        database.delete_files(normalized, folder_type, removed)
    for item in disk_files:
        if item['type'] == 'dir':
            continue
        record = records.get(item['name'])
        changed = not record or record.get('mtime') != item.get('mtime') or record.get('bytes') != item.get('bytes')
        if changed:
            full_path = path.join(parent, normalized, item['name'])
            tags = None
            sidecar = get_info_filename(full_path)
            if path.exists(sidecar):
                try:
                    with open(sidecar, encoding='utf-8') as stream:
                        tags = json.load(stream).get('tags')
                except (OSError, ValueError):
                    pass
            database.upsert_file(
                filename=item['name'], folder_path=normalized, folder_type=folder_type,
                bytes_size=item['bytes'], created_at=item['created_at'], mtime=item['mtime'],
                hash_val=f"{full_path}{item['mtime']}{item['bytes']}", formatted_info={}, tags=tags,
            )
    records = database.get_files_in_folder(normalized, folder_type)
    for item in disk_files:
        if item['type'] == 'dir':
            continue
        record = records.get(item['name'])
        if not record:
            continue
        try:
            status = schedule_file_metadata(record, path.join(parent, normalized, item['name']), normalized, folder_type, metadata_queue)
        except OSError:
            status = 'failed'
        item.update(hash=record.get('hash'), formatted_info=record.get('formatted_info'),
                    tags=record.get('tags', []), metadata_pending=status in {'waiting', 'processing'})
    return disk_files


# folder_path, folder_type
async def api_get_files(request):
    folder_path = request.query.get('folder_path', '')
    folder_type = request.query.get('folder_type', 'outputs')
    
    # 1. Get disk files (Disk Scan - fast)
    parent_path = get_parent_path(folder_type)
    target_path = path.join(parent_path, normalize_folder_path(folder_path))
    if folder_path and not path.exists(target_path):
        return web.Response(status=404)

    response_files = synchronize_folder(folder_path, folder_type)

    return web.json_response({
        'files': response_files
    })


def iter_relative_folders(target_root: str, base_root: str):
    """生成目标目录及其子目录的相对路径（以 / 分隔）。"""
    for current_dir, _, _ in os.walk(target_root):
        rel_path = path.relpath(current_dir, base_root)
        if rel_path == '.':
            yield ''
        else:
            yield rel_path.replace('\\', '/')


def open_system_folder(target_folder: str) -> bool:
    """在系统文件管理器中打开目标文件夹。"""
    try:
        if sys.platform.startswith('win'):
            os.startfile(target_folder)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.run(['open', target_folder], check=False)
        else:
            subprocess.run(['xdg-open', target_folder], check=False)
        return True
    except Exception as e:
        print(f"Open folder failed: {e}")
        return False


async def api_open_folder(request):
    """
    在操作系统文件资源管理器中打开指定目录。
    """
    json_data = await request.json()
    folder_type = json_data.get('folder_type', 'outputs')
    folder_path = normalize_folder_path(json_data.get('folder_path', ''))

    parent_path = get_parent_path(folder_type)
    normalized_parent = path.abspath(parent_path)
    target_path = path.abspath(path.join(parent_path, folder_path))

    if not target_path.startswith(normalized_parent):
        return web.Response(status=400, text="Invalid path")
    if not path.exists(target_path):
        return web.Response(status=404, text="Folder not found")
    if not path.isdir(target_path):
        target_path = path.dirname(target_path)
        if not target_path or not path.isdir(target_path):
            return web.Response(status=400, text="Target is not a directory")

    if not open_system_folder(target_path):
        return web.Response(status=500, text="Failed to open folder")

    return web.json_response({"opened": True, "path": target_path})


async def api_reindex_files(request):
    """
    清空指定目录对应的索引记录并重新索引。
    """
    try:
        json_data = await request.json()
    except Exception:
        json_data = {}

    folder_type = json_data.get('folder_type', 'outputs')
    folder_path = normalize_folder_path(json_data.get('folder_path', ''))

    parent_path = get_parent_path(folder_type)
    normalized_parent = path.abspath(parent_path)
    target_root = path.abspath(path.join(parent_path, folder_path))

    if not target_root.startswith(normalized_parent):
        return web.Response(status=400, text="Invalid path")
    if not path.exists(target_root):
        return web.Response(status=404, text="Target path not found")

    db_service.clear_records(folder_type, folder_path or None)

    indexed_folders = 0
    indexed_files = 0

    for relative_path in iter_relative_folders(target_root, normalized_parent):
        files_in_folder = synchronize_folder(relative_path, folder_type)
        indexed_folders += 1
        indexed_files += len([f for f in files_in_folder if f.get('type') != 'dir'])

    return web.json_response({
        "folder_type": folder_type,
        "folder_path": folder_path,
        "indexed_folders": indexed_folders,
        "indexed_files": indexed_files
    })


# filename, folder_path, folder_type
async def api_delete_file(request):
    json_data = await request.json()
    filename = json_data['filename']
    folder_path = json_data.get('folder_path', '')
    folder_type = json_data.get('folder_type', 'outputs')

    parent_path = get_parent_path(folder_type)
    target_path = path.join(parent_path, folder_path, filename)
    if not path.exists(target_path):
        return web.json_response(status=404)

    if path.isdir(target_path):
        shutil.rmtree(target_path)
    else:
        os.remove(target_path)
    info_file_path = get_info_filename(target_path)
    if path.exists(info_file_path):
        os.remove(info_file_path)

    return web.Response(status=201)


    return web.json_response(response_data)


# filename, folder_path, folder_type, tag
async def api_add_tag_to_file(request):
    """为指定文件添加标签"""
    json_data = await request.json()
    filename = json_data.get('filename')
    folder_path = json_data.get('folder_path', '')
    folder_type = json_data.get('folder_type', 'outputs')
    tag = json_data.get('tag')
    
    parent_path = get_parent_path(folder_type)
    file_path = path.join(parent_path, folder_path, filename)

    if not (filename and tag):
        return web.Response(status=400, text="filename and tag are required")

    db_files_map = db_service.get_files_in_folder(folder_path, folder_type)
    db_record = db_files_map.get(filename)

    if not db_record:
        return web.Response(status=404, text="File not found in database.")

    current_tags = db_record.get('tags', [])
    if tag not in current_tags:
        current_tags.append(tag)
        db_service.update_file_tags(filename, folder_path, folder_type, current_tags)
        # Sync to .info file
        update_file_info(file_path, tags=current_tags)
    
    return web.json_response({"tags": current_tags})


# filename, folder_path, folder_type, tag
async def api_remove_tag_from_file(request):
    """从指定文件移除标签"""
    json_data = await request.json()
    filename = json_data.get('filename')
    folder_path = json_data.get('folder_path', '')
    folder_type = json_data.get('folder_type', 'outputs')
    tag = json_data.get('tag')
    
    parent_path = get_parent_path(folder_type)
    file_path = path.join(parent_path, folder_path, filename)

    if not (filename and tag):
        return web.Response(status=400, text="filename and tag are required")

    db_files_map = db_service.get_files_in_folder(folder_path, folder_type)
    db_record = db_files_map.get(filename)

    if not db_record:
        return web.Response(status=404, text="File not found in database.")

    current_tags = db_record.get('tags', [])
    if tag in current_tags:
        current_tags.remove(tag)
        db_service.update_file_tags(filename, folder_path, folder_type, current_tags)
        # Sync to .info file
        update_file_info(file_path, tags=current_tags)
    
    return web.json_response({"tags": current_tags})


# filename, folder_path, folder_type, new_data: {}
async def api_update_file(request):
    json_data = await request.json()
    filename = json_data['filename']
    folder_path = json_data.get('folder_path', '')
    folder_type = json_data.get('folder_type', 'outputs')
    parent_path = get_parent_path(folder_type)

    new_data = json_data.get('new_data', None)
    if not new_data:
        return web.Response(status=400)

    new_filename = new_data.get('filename') # new_filename might be None if only notes/tags are updated
    notes = new_data.get('notes')
    tags = new_data.get('tags') # Expecting a list of strings if provided

    old_file_path = path.join(parent_path, folder_path, filename)

    if not path.exists(old_file_path):
        return web.Response(status=404)

    # 1. 处理文件重命名
    if new_filename and filename != new_filename:
        new_file_path = path.join(parent_path, folder_path, new_filename)
        shutil.move(
            old_file_path,
            new_file_path
        )
        # 如果有配套的 .info 文件，也一起重命名
        old_info_file_path = get_info_filename(old_file_path)
        if path.exists(old_info_file_path):
            new_info_file_path = get_info_filename(new_file_path)
            shutil.move(
                old_info_file_path,
                new_info_file_path
            )
        # 更新文件名变量，以用于后续的 notes/tags 处理
        filename = new_filename
        old_file_path = new_file_path # Update old_file_path to the new path for consistency

    # 2. 处理 notes 和 tags 更新 (利用新辅助函数)
    if notes is not None or tags is not None:
        update_file_info(old_file_path, notes=notes, tags=tags)

    # 3. 处理 tags 更新 (DB)
    if tags is not None: # Expecting tags to be a list, even empty list is valid
        # db_service.update_file_tags 会直接替换标签
        db_service.update_file_tags(filename, folder_path, folder_type, tags)

    return web.Response(status=201)


# filename, folder_path, folder_type
async def api_view_file(request):
    folder_type = request.query.get("folder_type", "outputs")
    folder_path = request.query.get("folder_path", "")
    filename = request.query.get("filename", None)
    if not filename:
        return web.Response(status=404)

    parent_path = get_parent_path(folder_type)
    file_path = path.join(parent_path, folder_path, filename)

    if not path.exists(file_path):
        return web.Response(status=404)

    with open(file_path, 'rb') as f:
        media_file = f.read()

    content_type = 'application/json'
    file_extension = path.splitext(filename)[1].lower()
    if file_extension in IMAGE_EXTENSIONS:
        content_type = f'image/{file_extension[1:]}'
    if file_extension in VIDEO_EXTENSIONS:
        content_type = f'video/{file_extension[1:]}'

    return web.Response(
        body=media_file,
        content_type=content_type,
        headers={"Content-Disposition": f"filename=\"{filename}\""}
    )


# filename, folder_path, folder_type
async def api_get_image_metadata(request):
    """返回缓存与任务状态；初次读取补齐版本，poll 请求仅读取。"""
    folder_type = request.query.get('folder_type', 'outputs')
    folder_path = normalize_folder_path(request.query.get('folder_path', ''))
    filename = request.query.get('filename')
    if not filename:
        return web.Response(status=400, text='filename is required')
    if path.basename(filename) != filename or '/' in filename or '\\' in filename:
        return web.Response(status=400, text='Invalid filename')
    record = db_service.get_files_in_folder(folder_path, folder_type).get(filename)
    if not record:
        return web.Response(status=404, text='File not found in synchronized directory')
    base = path.realpath(get_parent_path(folder_type))
    full_path = path.realpath(path.join(base, folder_path, filename))
    if path.commonpath([base, full_path]) != base:
        return web.Response(status=400, text='Invalid path')
    if path.splitext(filename)[1].lower() not in IMAGE_EXTENSIONS:
        return web.json_response({'positive': '', 'negative': '', 'has_metadata': False,
                                  'formatted_info': {}, 'tags': record.get('tags', []), 'index_status': 'complete'})
    try:
        stat = os.stat(full_path)
        if request.query.get('poll') == '1':
            task = create_metadata_task(record, full_path, folder_path, folder_type)
            info = record.get('formatted_info') or {}
            status = metadata_index_queue.status(task) or info.get('index_status')
            if stat.st_mtime != record['mtime'] or stat.st_size != record['bytes'] or not status:
                status = 'failed'
            latest = db_service.get_files_in_folder(folder_path, folder_type).get(filename)
            if not latest:
                return web.Response(status=404, text='File no longer exists')
            info = latest.get('formatted_info') or {}
            return web.json_response({
                'positive': info.get('positive_prompt', ''), 'negative': info.get('negative_prompt', ''),
                'has_metadata': info.get('has_metadata', False), 'formatted_info': info,
                'tags': latest.get('tags', []), 'index_status': status,
                'metadata_pending': status in {'waiting', 'processing'},
            })
        if stat.st_mtime != record['mtime'] or stat.st_size != record['bytes']:
            db_service.upsert_file(filename, folder_path, folder_type, stat.st_size, stat.st_ctime,
                                   stat.st_mtime, f"{full_path}{stat.st_mtime}{stat.st_size}", {}, None)
            record = db_service.get_files_in_folder(folder_path, folder_type)[filename]
        task = create_metadata_task(record, full_path, folder_path, folder_type)
        status = schedule_file_metadata(record, full_path, folder_path, folder_type, metadata_index_queue,
                                        force=request.query.get('refresh') == '1')
        # complete 状态在提交之后发布，随后读取可见的最新数据。
        record = db_service.get_files_in_folder(folder_path, folder_type).get(filename)
        if not record:
            return web.Response(status=404, text='File no longer exists')
    except FileNotFoundError:
        return web.Response(status=404, text='File no longer exists')
    info = record.get('formatted_info') or {}
    return web.json_response({
        'positive': info.get('positive_prompt', ''), 'negative': info.get('negative_prompt', ''),
        'has_metadata': info.get('has_metadata', False), 'formatted_info': info,
        'tags': record.get('tags', []), 'index_status': status,
        'metadata_pending': status in {'waiting', 'processing'},
    })


# All tags
async def api_get_all_tags(request):
    """获取所有已使用的唯一标签"""
    all_tags = db_service.get_all_tags()
    return web.json_response({"all_tags": all_tags})
