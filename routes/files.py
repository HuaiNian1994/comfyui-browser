from aiohttp import web
import asyncio
import json
from os import path
import os
import shutil
import subprocess
import sys

from ..utils import get_target_folder_files, get_parent_path, extract_detailed_metadata
from ..constants import IMAGE_EXTENSIONS
from ..services.db_service import DBService
from ..services.metadata_indexer import MetadataIndexQueue, MetadataIndexTask
from ..metadata.registry import PARSER_VERSION
from ..timing.storage import read_summary, file_lock, file_locks
from ..utils.path_utils import resolve_folder_path, resolve_file_path, resolve_sidecar_path
from ..services.directory_service import DirectoryScanService, directory_sync_lock
from ..services.reindex_service import ReindexService

db_service = DBService()
metadata_index_queue = MetadataIndexQueue(db_service, extract_detailed_metadata)
directory_scan_service = DirectoryScanService()
reindex_service = ReindexService()

def normalize_folder_path(folder_path: str) -> str:
    """
    将前端传入的路径标准化为相对路径，统一分隔符并去除首尾的分隔符。
    """
    if not folder_path:
        return ''
    return folder_path.strip('/').replace('\\', '/')


def update_file_info(info_file_path, notes=None, tags=None):
    """辅助函数：更新 .info 文件中的 notes 和 tags"""
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
    """任务直接复用数据库身份，构造过程无需读取文件。"""
    return MetadataIndexTask(
        filename=record['filename'], folder_path=folder_path, folder_type=folder_type,
        file_path=full_path, bytes_size=record['bytes'], created_at=record['created_at'],
        mtime=record['mtime'], mtime_ns=record.get('mtime_ns'), hash_val=record['hash'],
        record_id=record.get('id'), index_generation=record.get('index_generation'))


def schedule_file_metadata(record, full_path, folder_path, folder_type, queue, force=False):
    if path.splitext(record['filename'])[1].lower() not in IMAGE_EXTENSIONS:
        return 'complete'
    task = create_metadata_task(record,full_path,folder_path,folder_type)
    info = record.get('summary') or record.get('formatted_info') or {}
    failed = info.get('parse_status')=='failed' or info.get('index_status')=='failed'
    outdated = info.get('parser_version')!=PARSER_VERSION
    if queue and (force or (outdated and not failed)):
        queue.enqueue(task,force=force)
    status = queue.status(task) if queue else None
    # 终态必须与本次数据库快照的摘要一致；队列可能已提交了快照之后的新结果。
    if status=='complete' and (outdated or failed):
        return 'waiting'
    return status or ('failed' if failed else 'waiting' if outdated else 'complete')


def synchronize_folder(folder_path,folder_type,metadata_queue=metadata_index_queue,database=db_service,reindex=False):
    """同目录的普通扫描与重建共用完整同步锁。"""
    normalized = normalize_folder_path(folder_path)
    with directory_sync_lock(database,folder_type,normalized):
        return _synchronize_folder_locked(normalized,folder_type,metadata_queue,database,reindex)


def _synchronize_folder_locked(folder_path,folder_type,metadata_queue,database,reindex):
    """批量同步文件身份；逐文件锁仅覆盖 stat，数据库提交保持批量。"""
    normalized = normalize_folder_path(folder_path)
    disk_files = get_target_folder_files(normalized,folder_type=folder_type)
    if disk_files is None:
        return []
    records = database.get_files_in_folder(normalized,folder_type)
    observed_tasks = [create_metadata_task(record,'',normalized,folder_type) for record in records.values()]
    changes = []
    migrated_notes = []
    present = []
    for item in disk_files:
        if item['type']=='dir':
            present.append(item)
            continue
        full_path = resolve_file_path(folder_type,normalized,item['name'])
        try:
            with file_lock(full_path):
                stat = os.stat(full_path)
            item.update(bytes=stat.st_size,mtime=stat.st_mtime,mtime_ns=stat.st_mtime_ns)
        except FileNotFoundError:
            continue
        record = records.get(item['name'])
        if record and not record.get('notes_initialized'):
            notes = ''
            try:
                with open(resolve_sidecar_path(folder_type,normalized,item['name']),encoding='utf-8') as stream:
                    notes = json.load(stream).get('notes','')
            except (OSError,ValueError):
                pass
            migrated_notes.append((notes,record['id']))
        if not record or record.get('mtime_ns')!=stat.st_mtime_ns or record['bytes']!=stat.st_size:
            item['hash'] = f'{full_path}{stat.st_mtime_ns}{stat.st_size}'
            if not record:
                try:
                    with open(resolve_sidecar_path(folder_type,normalized,item['name']),encoding='utf-8') as stream:
                        sidecar = json.load(stream)
                    item.update(tags=sidecar.get('tags',[]),notes=sidecar.get('notes',''))
                except (OSError,ValueError):
                    pass
            changes.append((item,record))
        present.append(item)
    if migrated_notes:
        database.initialize_notes(migrated_notes)
    names = {item['name'] for item in present}
    database.sync_identities(normalized,folder_type,changes,[record for name,record in records.items() if name not in names])
    if reindex:
        database.bump_generation(normalized,folder_type)
    records = database.get_files_in_folder(normalized,folder_type)
    tasks = []
    result = []
    for item in present:
        if item['type']=='dir':
            result.append(item)
            continue
        record = records.get(item['name'])
        if not record:
            continue
        full_path = resolve_file_path(folder_type,normalized,item['name'])
        task = create_metadata_task(record,full_path,normalized,folder_type)
        tasks.append(task)
        status = schedule_file_metadata(record,full_path,normalized,folder_type,metadata_queue)
        item.update(bytes=record['bytes'],mtime=record['mtime'],mtime_ns=record['mtime_ns'],created_at=record['created_at'],
                    hash=record.get('hash'),tags=record.get('tags',[]),notes=record.get('notes',''),
                    file_version=record['file_version'],index_generation=record['index_generation'],
                    summary=record.get('summary',{}),index_status=status,
                    metadata_pending=status in {'waiting','processing'},folder_path=normalized)
        result.append(item)
    if metadata_queue:
        metadata_queue.forget_folder(folder_type,normalized,tasks,observed_tasks=observed_tasks)
    return result


def request_services(request):
    app = getattr(request,'app',{})
    return app.get('file_database',db_service),app.get('file_metadata_queue',metadata_index_queue)


async def api_get_files(request):
    folder_path = normalize_folder_path(request.query.get('folder_path',''))
    folder_type = request.query.get('folder_type','outputs')
    try:
        target = await asyncio.to_thread(resolve_folder_path,folder_type,folder_path)
        if not await asyncio.to_thread(path.isdir,target):
            return web.Response(status=404)
        database,queue = request_services(request)
        key = (id(database),id(queue),folder_type,folder_path)
        files = await directory_scan_service.scan(key,lambda:synchronize_folder(folder_path,folder_type,metadata_queue=queue,database=database))
        return await asyncio.to_thread(web.json_response,{'files':files})
    except ValueError:
        return web.Response(status=400,text='Invalid path')
    except OSError:
        return web.Response(status=500,text='Directory enumeration failed')


def summary_updates(data,database,queue):
    if not isinstance(data,dict):
        raise ValueError('Invalid summary request')
    folder_type = data.get('folder_type','outputs')
    if folder_type not in {'outputs','collections','sources'}:
        raise ValueError('Invalid folder type')
    requested = data.get('files',[])
    visible = data.get('visible_files',[])
    if not isinstance(requested,list) or not isinstance(visible,list) or len(requested)>200 or len(visible)>100:
        raise ValueError('Invalid batch size')
    items = []
    for item in requested+visible:
        if not isinstance(item,dict) or not isinstance(item.get('name'),str) or not isinstance(item.get('file_version'),str) or not isinstance(item.get('index_generation'),int):
            raise ValueError('Invalid file identity')
        folder = normalize_folder_path(item.get('folder_path',''))
        if any(c in item['name'] for c in '/\\:') or '..' in folder.split('/') or ':' in folder:
            raise ValueError('Invalid file identity')
        items.append(dict(item,folder_path=folder))
    records = database.get_summary_batch(folder_type,items)
    visible_tasks = []
    for item in items[len(requested):]:
        record = records.get((item['folder_path'],item['name']))
        if record and record['file_version']==item['file_version'] and record['index_generation']==item['index_generation']:
            visible_tasks.append(create_metadata_task(record,'',item['folder_path'],folder_type))
    if queue:
        queue.update_visible(str(data.get('session_id',''))[:200],visible_tasks)
    result = []
    for item in items[:len(requested)]:
        record = records.get((item['folder_path'],item['name']))
        row = dict(item)
        if not record:
            row['status'] = 'missing'
        elif record['file_version']!=item['file_version'] or record['index_generation']!=item['index_generation']:
            row['status'] = 'stale'
        else:
            task = create_metadata_task(record,'',item['folder_path'],folder_type)
            summary = record.get('summary') or {}
            status = queue.status(task) if queue else None
            if queue and queue.outcome(task)=='superseded':
                status = 'stale'
            if status=='complete' and (summary.get('parser_version')!=PARSER_VERSION or summary.get('parse_status')=='failed'):
                # 下次批量轮询读取提交后的摘要，保持本次快照完整且无需逐文件补读。
                status = 'waiting'
            if not status:
                status = 'failed' if summary.get('parse_status')=='failed' else 'complete' if summary.get('parser_version')==PARSER_VERSION or path.splitext(item['name'])[1].lower() not in IMAGE_EXTENSIONS else 'waiting'
            row.update(status=status,summary=summary,tags=record['tags'])
        result.append(row)
    return {'files':result}


async def api_get_summary_updates(request):
    try:
        data = await request.json()
        database,queue = request_services(request)
        return web.json_response(await asyncio.to_thread(summary_updates,data,database,queue))
    except (ValueError,TypeError,KeyError):
        return web.Response(status=400,text='Invalid summary request')


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
    data=await request.json()
    try:
        target=await asyncio.to_thread(resolve_folder_path,data.get('folder_type','outputs'),data.get('folder_path',''))
        if not await asyncio.to_thread(path.isdir,target):
            return web.Response(status=404,text='Folder not found')
        opened=await asyncio.to_thread(open_system_folder,target)
        return web.json_response({'opened':opened,'path':target},status=200 if opened else 500)
    except (ValueError,TypeError):
        return web.Response(status=400,text='Invalid path')


async def api_reindex_files(request):
    try:
        data = await request.json()
        if not isinstance(data,dict):
            raise ValueError('Invalid request')
        folder_type = data.get('folder_type','outputs')
        paths = data.get('folder_paths')
        if not isinstance(paths,list) or not paths or not all(isinstance(value,str) for value in paths):
            raise ValueError('Invalid folders')
        folders = tuple(sorted(set(normalize_folder_path(value) for value in paths)))
        for folder in folders:
            target=await asyncio.to_thread(resolve_folder_path,folder_type,folder)
            if not await asyncio.to_thread(path.isdir,target):
                return web.Response(status=404,text='Target path not found')
        database,queue = request_services(request)
        # 重建范围固定为显式指定目录的当前层。
        def enumerate_folders():
            yield from folders
        def scanner(folder,force):
            return synchronize_folder(folder,folder_type,metadata_queue=queue,database=database,reindex=force)
        scope = (folder_type,folders,id(database))
        job_id = reindex_service.submit(scope,enumerate_folders,scanner,database,queue)
        return web.json_response({'job_id':job_id,'status':reindex_service.get(job_id)['status']},status=202)
    except (ValueError,TypeError):
        return web.Response(status=400,text='Invalid reindex request')


async def api_get_reindex_job(request):
    job = reindex_service.get(request.match_info['job_id'])
    return web.json_response(job if job else {'error':'job_expired'},status=200 if job else 404)


async def shutdown_file_services(app):
    await asyncio.to_thread(reindex_service.shutdown)
    await asyncio.to_thread(directory_scan_service.shutdown)
    queue = app.get('file_metadata_queue',metadata_index_queue)
    if queue:
        await asyncio.to_thread(queue.shutdown)


def file_operation(handler):
    """统一处理文件操作的路径和文件系统错误。"""
    async def wrapped(request):
        try:
            return await handler(request)
        except (ValueError,TypeError,KeyError):
            return web.json_response({'error':'invalid_path'},status=400)
        except (FileNotFoundError,NotADirectoryError):
            return web.json_response({'error':'missing'},status=404)
        except PermissionError:
            return web.json_response({'error':'permission_denied'},status=403)
    return wrapped


def file_request(data):
    folder_type=data.get('folder_type','outputs')
    folder_path=normalize_folder_path(data.get('folder_path',''))
    filename=data.get('filename')
    target=resolve_file_path(folder_type,folder_path,filename)
    return folder_type,folder_path,filename,target


@file_operation
async def api_delete_file(request):
    data=await request.json()
    folder_type,folder_path,filename,target=await asyncio.to_thread(file_request,data)
    sidecar=await asyncio.to_thread(resolve_sidecar_path,folder_type,folder_path,filename)
    database,_=request_services(request)
    def remove():
        with file_locks([target,sidecar]):
            if path.isdir(target):
                shutil.rmtree(target)
                database.clear_records(folder_type,'/'.join(filter(None,[folder_path,filename])))
            else:
                os.remove(target)
                database.delete_files(folder_path,folder_type,[filename])
            if path.exists(sidecar):
                os.remove(sidecar)
    await asyncio.to_thread(remove)
    return web.Response(status=201)


async def change_tag(request,remove=False):
    data=await request.json()
    folder_type,folder_path,filename,target=await asyncio.to_thread(file_request,data)
    sidecar=await asyncio.to_thread(resolve_sidecar_path,folder_type,folder_path,filename)
    tag=data.get('tag')
    if not isinstance(tag,str) or not tag:
        raise ValueError('Invalid tag')
    database,_=request_services(request)
    def update():
        with file_locks([target,sidecar]):
            if not path.isfile(target):
                raise FileNotFoundError(target)
            record=database.get_file(filename,folder_path,folder_type)
            if not record:
                raise FileNotFoundError(target)
            tags=record.get('tags',[])
            if remove:
                tags=[value for value in tags if value!=tag]
            elif tag not in tags:
                tags.append(tag)
            database.update_file_tags(filename,folder_path,folder_type,tags)
            update_file_info(sidecar,tags=tags)
            return tags
    tags=await asyncio.to_thread(update)
    return web.json_response({'tags':tags})


@file_operation
async def api_add_tag_to_file(request):
    return await change_tag(request)


@file_operation
async def api_remove_tag_from_file(request):
    return await change_tag(request,remove=True)


@file_operation
async def api_update_file(request):
    data=await request.json()
    folder_type,folder_path,filename,target=await asyncio.to_thread(file_request,data)
    changes=data.get('new_data')
    if not isinstance(changes,dict) or not changes:
        raise ValueError('Invalid update')
    new_name=changes.get('filename') or filename
    destination,old_sidecar,new_sidecar=await asyncio.to_thread(lambda:(
        resolve_file_path(folder_type,folder_path,new_name),
        resolve_sidecar_path(folder_type,folder_path,filename),
        resolve_sidecar_path(folder_type,folder_path,new_name)))
    database,_=request_services(request)
    def update():
        with file_locks([target,destination,old_sidecar,new_sidecar]):
            if not path.exists(target):
                raise FileNotFoundError(target)
            if new_name!=filename:
                if path.exists(destination) or (new_sidecar!=old_sidecar and path.exists(new_sidecar)):
                    raise ValueError('Destination exists')
                shutil.move(target,destination)
                if path.exists(old_sidecar):
                    shutil.move(old_sidecar,new_sidecar)
                with database.connection() as connection:
                    connection.execute('UPDATE files SET filename=?,index_generation=index_generation+1 WHERE filename=? AND folder_path=? AND folder_type=?',(new_name,filename,folder_path,folder_type))
            notes,tags=changes.get('notes'),changes.get('tags')
            if notes is not None or tags is not None:
                update_file_info(new_sidecar,notes=notes,tags=tags)
            if notes is not None:
                database.update_file_notes(new_name,folder_path,folder_type,notes)
            if tags is not None:
                database.update_file_tags(new_name,folder_path,folder_type,tags)
    await asyncio.to_thread(update)
    return web.Response(status=201)


@file_operation
async def api_view_file(request):
    _,_,filename,target=await asyncio.to_thread(file_request,request.query)
    if not await asyncio.to_thread(path.isfile,target):
        return web.Response(status=404)
    # FileResponse 分块发送原图、视频和 JSON 工作流，沿用统一注册目录校验。
    return web.FileResponse(target)


# filename, folder_path, folder_type
async def api_get_image_metadata(request):
    """文件读取及数据库查询放入工作线程，保持服务事件循环可响应。"""
    return await asyncio.to_thread(get_image_metadata, request)


def get_image_metadata(request):
    folder_type = request.query.get('folder_type','outputs')
    folder_path = normalize_folder_path(request.query.get('folder_path',''))
    filename = request.query.get('filename')
    try:
        full_path = resolve_file_path(folder_type,folder_path,filename)
    except (ValueError,TypeError):
        return web.Response(status=400,text='Invalid file identity')
    database,queue = request_services(request)
    record = database.get_file(filename,folder_path,folder_type)
    if not record:
        return web.Response(status=404)
    expected = request.query.get('file_version')
    generation = request.query.get('index_generation')
    if (expected is not None and expected!=record['file_version']) or (generation is not None and generation!=str(record['index_generation'])):
        return web.json_response({'error':'stale'},status=409)
    try:
        with file_lock(full_path):
            stat = os.stat(full_path)
        if record.get('mtime_ns')!=stat.st_mtime_ns or record['bytes']!=stat.st_size:
            if expected is not None or generation is not None or request.query.get('poll')=='1':
                return web.json_response({'error':'stale'},status=409)
            item = dict(name=filename,bytes=stat.st_size,created_at=stat.st_ctime,mtime=stat.st_mtime,mtime_ns=stat.st_mtime_ns,hash=f'{full_path}{stat.st_mtime_ns}{stat.st_size}')
            database.sync_identities(folder_path,folder_type,[(item,record)])
            record = database.get_file(filename,folder_path,folder_type)
        if request.query.get('refresh')=='1':
            from ..timing import storage as timing_storage
            if timing_storage.store:
                timing_storage.store.retry_file(full_path)
        if request.query.get('poll')=='1':
            task = create_metadata_task(record,full_path,folder_path,folder_type)
            info = record.get('formatted_info') or {}
            status = (queue.status(task) if queue else None) or info.get('index_status','waiting' if info.get('parser_version')!=PARSER_VERSION else 'complete')
        else:
            status = schedule_file_metadata(record,full_path,folder_path,folder_type,queue,force=request.query.get('refresh')=='1')
        record = database.get_file(filename,folder_path,folder_type)
        if not record:
            return web.Response(status=404)
        if (expected is not None and expected!=record['file_version']) or (generation is not None and generation!=str(record['index_generation'])):
            return web.json_response({'error':'stale'},status=409)
        info = record.get('formatted_info') or {}
        timing,pending = read_summary(full_path)
        if timing:
            info['generation_timing'] = timing
        else:
            info.pop('generation_timing',None)
        info['timing_pending'] = pending
        return web.json_response({'positive':info.get('positive_prompt',''),'negative':info.get('negative_prompt',''),
            'has_metadata':info.get('has_metadata',False),'formatted_info':info,'tags':record.get('tags',[]),
            'index_status':status,'metadata_pending':status in {'waiting','processing'},'timing_pending':pending,
            'file_version':record['file_version'],'index_generation':record['index_generation']})
    except FileNotFoundError:
        return web.Response(status=404)


# All tags
async def api_get_all_tags(request):
    """获取所有已使用的唯一标签"""
    database,_ = request_services(request)
    def response():
        return web.json_response({'all_tags':database.get_all_tags()})
    return await asyncio.to_thread(response)


def refresh_timed_file(full_path):
    """计时提交复用数据库服务，并以旧身份保护并发重建结果。"""
    base = path.realpath(get_parent_path('outputs'))
    if path.commonpath([base,path.realpath(full_path)])!=base:
        return
    relative = path.relpath(full_path,base)
    folder = normalize_folder_path(path.dirname(relative))
    filename = path.basename(full_path)
    record = db_service.get_file(filename,folder,'outputs')
    if not record:
        return
    with file_lock(full_path):
        stat = os.stat(full_path)
        info = extract_detailed_metadata(full_path)
        info['index_status'] = 'complete'
        db_service.refresh_timed_file(record,stat,info,f'{full_path}{stat.st_mtime_ns}{stat.st_size}')
