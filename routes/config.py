from aiohttp import web
import json

from ..config import get_config, get_collections_path, CONFIG_PATH
from ..utils import run_git_command, git_init
from ..constants import GIT_REMOTE_NAME

async def api_get_browser_config(_):
    config = get_config()

    return web.json_response(config)

async def api_update_browser_config(request):
    """更新浏览器配置"""
    json_data = await request.json()
    config = get_config()
    git_repo = json_data.get('git_repo', config.get('git_repo'))

    git_init()

    collections_dir = get_collections_path()
    if git_repo == '':
        ret = run_git_command(f'git remote remove {GIT_REMOTE_NAME}', collections_dir)
        if not ret.returncode == 0:
            return web.json_response(
                { 'message': ret.stderr },
                status=500,
            )

        set_config({ 'git_repo': git_repo })
        return web.Response(status=200)

    ret = git_set_remote_url(git_repo)
    if not ret.returncode == 0:
        return web.json_response(
            { 'message': ret.stderr },
            status=500,
        )

    set_config({ 'git_repo': git_repo })
    return web.Response(status=200)


def set_config(config):
    """设置配置"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f)


def git_set_remote_url(remote_url, run_path=None):
    """设置Git远程仓库URL"""
    if run_path is None:
        run_path = get_collections_path()
    
    ret = run_git_command('git remote', run_path)

    if GIT_REMOTE_NAME in ret.stdout.split('\n'):
        return run_git_command(f'git remote set-url {GIT_REMOTE_NAME} {remote_url}', run_path)
    else:
        return run_git_command(f'git remote add {GIT_REMOTE_NAME} {remote_url}', run_path)
