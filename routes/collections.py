from os import path, makedirs
from aiohttp import web
import shutil
import asyncio
from ..timing.storage import file_lock, file_locks
from ..utils.path_utils import resolve_file_path, resolve_folder_path, resolve_sidecar_path
import time

from ..config import get_collections_path, get_config, CONFIG_PATH
from ..utils import get_parent_path, add_uuid_to_filename, git_init, run_git_command
from ..constants import GIT_REMOTE_NAME



async def api_add_to_collections(request):
    """从经过校验的登记目录复制文件与侧车到收藏根。"""
    try:
        data=await request.json()
        folder_type=data.get('folder_type','outputs')
        folder=data.get('folder_path','')
        filename=data.get('filename')
        source=await asyncio.to_thread(resolve_file_path,folder_type,folder,filename)
        sidecar=await asyncio.to_thread(resolve_sidecar_path,folder_type,folder,filename)
        new_name=add_uuid_to_filename(filename)
        destination=await asyncio.to_thread(resolve_file_path,'collections','',new_name)
        new_sidecar=await asyncio.to_thread(resolve_sidecar_path,'collections','',new_name)
        def copy():
            makedirs(resolve_folder_path('collections'),exist_ok=True)
            with file_locks([source,sidecar,destination,new_sidecar]):
                if path.exists(destination) or path.exists(new_sidecar):
                    raise FileExistsError(destination)
                if path.isdir(source):
                    # 目录收藏保留链接而不跟随链接读取外部文件。
                    shutil.copytree(source,destination,symlinks=True)
                else:
                    shutil.copy2(source,destination)
                if path.isfile(sidecar):
                    shutil.copy2(sidecar,new_sidecar)
        await asyncio.to_thread(copy)
        return web.Response(status=201)
    except (ValueError,TypeError):
        return web.Response(status=400,text='Invalid path')
    except FileNotFoundError:
        return web.Response(status=404)
    except FileExistsError:
        return web.Response(status=409,text='Destination exists')


async def api_create_new_workflow(request):
    try:
        data=await request.json()
        filename=data.get('filename')
        content=data.get('content')
        if not isinstance(content,str) or not content:
            return web.Response(status=400)
        await asyncio.to_thread(resolve_file_path,'collections','',filename)
        destination=await asyncio.to_thread(resolve_file_path,'collections','',add_uuid_to_filename(filename))
        def write():
            makedirs(resolve_folder_path('collections'),exist_ok=True)
            with file_lock(destination):
                with open(destination,'x',encoding='utf-8') as stream:
                    stream.write(content)
        await asyncio.to_thread(write)
        return web.Response(status=201)
    except (ValueError,TypeError):
        return web.Response(status=400,text='Invalid path')
    except FileExistsError:
        return web.Response(status=409,text='Destination exists')

async def api_sync_my_collections(_):
    """同步我的收藏夹"""
    if not path.exists(CONFIG_PATH):
        return web.Response(status=404)

    config = get_config()
    git_repo = config.get('git_repo')
    if not git_repo:
        return web.Response(status=404)

    git_init()

    collections_dir = get_collections_path()
    cmd = 'git status -s'
    ret = run_git_command(cmd, collections_dir)
    if len(ret.stdout) > 0:
        cmd = f'git add . && git commit -m "sync by comfyui-browser at {int(time.time())}"'
        ret = run_git_command(cmd, collections_dir)
        if not ret.returncode == 0:
            return web.json_response(
                { 'message': "\n".join([ret.stdout, ret.stderr]) },
                status=500,
            )

    cmd = f'git fetch {GIT_REMOTE_NAME} -v'
    ret = run_git_command(cmd, collections_dir)
    if not ret.returncode == 0:
        return web.json_response(
            { 'message': "\n".join([ret.stdout, ret.stderr]) },
            status=500,
        )

    cmd = 'git branch --show-current'
    ret = run_git_command(cmd, collections_dir)
    branch = ret.stdout.replace('\n', '')

    cmd = f'git merge {GIT_REMOTE_NAME}/{branch}'
    ret = run_git_command(cmd, collections_dir, log_code=False)

    cmd = f'git push {GIT_REMOTE_NAME} {branch}'
    ret = run_git_command(cmd, collections_dir)
    if not ret.returncode == 0:
        return web.json_response(
            { 'message': "\n".join([ret.stdout, ret.stderr]) },
            status=500,
        )

    return web.Response(status=200)
