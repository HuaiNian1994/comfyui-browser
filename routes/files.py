from aiohttp import web
import json
from os import path
import os
import shutil

from ..utils import get_target_folder_files, get_parent_path, get_info_filename, extract_comfyui_png_metadata, extract_detailed_metadata
from ..constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from ..services.db_service import DBService

db_service = DBService()

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


# folder_path, folder_type
async def api_get_files(request):
    folder_path = request.query.get('folder_path', '')
    folder_type = request.query.get('folder_type', 'outputs')
    
    # 1. Get disk files (Disk Scan - fast)
    disk_files = get_target_folder_files(folder_path, folder_type=folder_type)

    if disk_files is None:
        return web.Response(status=404)

    # 2. Get DB records (DB Query - fast)
    db_files_map = db_service.get_files_in_folder(folder_path, folder_type)
    
    # 3. Synchronization
    disk_files_map = {f['name']: f for f in disk_files}
    parent_path = get_parent_path(folder_type)
    
    # Check for updates or new files
    for file_info in disk_files:
        if file_info['type'] == 'dir':
            continue
            
        filename = file_info['name']
        mtime = file_info.get('mtime', 0)
        size = file_info.get('bytes', 0)
        
        should_update = False
        if filename not in db_files_map:
            should_update = True # New file
        else:
            db_record = db_files_map[filename]
            # Compare mtime and size (allow small tolerance for float mtime)
            if abs(db_record['mtime'] - mtime) > 0.001 or db_record['bytes'] != size:
                should_update = True # Modified file
        
        if should_update:
            full_path = path.join(parent_path, folder_path, filename)
            # Extract detailed metadata (Expensive I/O + JSON parse)
            metadata = extract_detailed_metadata(full_path)
            
            # Extract tags from .info file if they exist (Recovery Mechanism)
            tags_from_disk = []
            info_file_path = get_info_filename(full_path)
            if path.exists(info_file_path):
                try:
                    with open(info_file_path, 'r', encoding='utf-8') as f:
                        info_data = json.load(f)
                        tags_from_disk = info_data.get("tags", [])
                except Exception:
                    pass

            # Create hash (simple string concat as requested)
            hash_val = f"{full_path}{file_info['created_at']}{size}"
            
            # If recovering, pass tags_from_disk. If updating existing with new metadata, 
            # we should preserve existing DB tags unless disk has something (conflict resolution).
            # Here we assume: Database is master, but if DB entry is new/missing, Disk is master.
            # upsert_file handles preservation if tags=None. 
            # But if we found tags on disk for a new/updated file, we should probably use them 
            # OR merge them? For simplicity, if we found tags on disk, we use them.
            
            tags_to_save = tags_from_disk if tags_from_disk else None

            db_service.upsert_file(
                filename=filename,
                folder_path=folder_path,
                folder_type=folder_type,
                bytes_size=size,
                created_at=file_info['created_at'],
                mtime=mtime,
                hash_val=hash_val,
                formatted_info=metadata,
                tags=tags_to_save
            )
            
            # Update the map entry so the response is fresh
            current_tags = tags_to_save if tags_to_save is not None else db_files_map.get(filename, {}).get('tags', [])

            db_files_map[filename] = {
                'filename': filename,
                'folder_path': folder_path,
                'folder_type': folder_type,
                'bytes': size,
                'created_at': file_info['created_at'],
                'mtime': mtime,
                'hash': hash_val,
                'formatted_info': metadata,
                'tags': current_tags
            }

    # Check for deleted files
    to_delete = []
    for db_filename in db_files_map:
        if db_filename not in disk_files_map:
            to_delete.append(db_filename)
    
    if to_delete:
        db_service.delete_files(folder_path, folder_type, to_delete)
        for f in to_delete:
            del db_files_map[f]

    # 4. Merge results
    # We return the disk_files list but enriched with DB metadata
    response_files = []
    for file_info in disk_files:
        if file_info['type'] == 'dir':
            response_files.append(file_info)
            continue
            
        filename = file_info['name']
        if filename in db_files_map:
            db_record = db_files_map[filename]
            # Merge DB info into response
            file_info.update({
                'hash': db_record.get('hash'),
                'formatted_info': db_record.get('formatted_info'),
                'tags': db_record.get('tags')
            })
        response_files.append(file_info)

    return web.json_response({
        'files': response_files
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
    """获取图片元数据(ComfyUI workflow和prompt，以及模型、LoRA、标签等详细信息)"""
    folder_type = request.query.get("folder_type", "outputs")
    folder_path = request.query.get("folder_path", "")
    filename = request.query.get("filename", None)
    
    if not filename:
        return web.Response(status=400, text="filename is required")

    # 从数据库获取信息
    db_files_map = db_service.get_files_in_folder(folder_path, folder_type)
    db_record = db_files_map.get(filename)

    if not db_record:
        # 如果数据库中没有记录，返回 404
        return web.Response(status=404, text="File metadata not found in database. Ensure file exists and directory has been synchronized.")
    
    # 检查是否为图片文件（根据文件扩展名，DB中可能存储了非图片文件的记录，但它们不应有图片元数据）
    file_extension = path.splitext(filename)[1].lower()
    if file_extension not in IMAGE_EXTENSIONS:
        return web.json_response({
            "positive": "",
            "negative": "",
            "has_metadata": False,
            "formatted_info": {},
            "tags": db_record.get("tags", []) # 非图片文件也可能有标签
        })

    # 从数据库记录中提取并返回所有详细元数据
    formatted_info = db_record.get("formatted_info", {})
    tags = db_record.get("tags", [])
    
    # 构建符合前端期望的响应结构
    response_data = {
        "positive": formatted_info.get("positive_prompt", ""),
        "negative": formatted_info.get("negative_prompt", ""),
        "has_metadata": bool(formatted_info), # 如果 formatted_info 不为空，则认为有元数据
        "formatted_info": formatted_info,
        "tags": tags
    }

    return web.json_response(response_data)


# All tags
async def api_get_all_tags(request):
    """获取所有已使用的唯一标签"""
    all_tags = db_service.get_all_tags()
    return web.json_response({"all_tags": all_tags})
