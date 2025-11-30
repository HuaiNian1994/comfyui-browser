from os import path, makedirs
from aiohttp import web
import shutil
import time

from ..config import get_collections_path, get_config, CONFIG_PATH
from ..utils import get_parent_path, add_uuid_to_filename, git_init, run_git_command
from ..constants import GIT_REMOTE_NAME



async def api_add_to_collections(request):
    """添加文件到收藏夹"""
    json_data = await request.json()
    filename = json_data.get('filename')
    if not filename:
        return web.Response(status=404)

    folder_path = json_data.get('folder_path', '')
    folder_type = json_data.get("folder_type", "outputs")
    parent_path = get_parent_path(folder_type)

    collections_dir = get_collections_path()
    makedirs(collections_dir, exist_ok=True)

    source_file_path = path.join(parent_path, folder_path, filename)
    if not path.exists(source_file_path):
        return web.Response(status=404)

    new_filepath = path.join(
        collections_dir,
        add_uuid_to_filename(filename)
    )

    if path.isdir(source_file_path):
        shutil.copytree(source_file_path, new_filepath)
    else:
        shutil.copy(source_file_path, new_filepath)

    return web.Response(status=201)

async def api_create_new_workflow(request):
    """创建新workflow"""
    json_data = await request.json()
    filename = json_data.get('filename')
    content = json_data.get('content')

    if not (filename and content):
        return web.Response(status=404)

    collections_dir = get_collections_path()
    new_filepath = path.join(
        collections_dir,
        add_uuid_to_filename(filename)
    )
    with open(new_filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return web.Response(status=201)

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
