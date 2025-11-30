from os import path, scandir, makedirs
import json
from aiohttp import web, ClientSession, ClientTimeout
import shutil
import os, stat, errno

from ..config import get_sources_path, BROWSER_PATH
from ..services import GitService
from ..constants import GIT_REMOTE_NAME



def handle_remove_readonly(func, path, exc):
    excvalue = exc[1]
    if excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise

async def api_get_sources(_):
    """获取所有源列表"""
    sources_dir = get_sources_path()
    if not path.exists(sources_dir):
        return web.json_response({'sources': []})

    sources = []
    source_list = scandir(sources_dir)
    source_list = sorted(source_list, key=lambda f: (-f.stat().st_ctime))
    
    for item in source_list:
        if not path.exists(item.path):
            continue
        if item.is_file():
            continue

        # 使用GitService获取远程URL
        url = GitService.get_remote_url(item.path)
        if not url:
            continue

        name = path.basename(item.path)
        created_at = item.stat().st_ctime
        sources.append({
            "name": name,
            "created_at": created_at,
            "url": url
        })

    return web.json_response({'sources': sources})


async def api_create_source(request):
    """创建新源"""
    json_data = await request.json()
    repo_url = json_data.get('repo_url')

    if not repo_url:
        return web.Response(status=400, text='repo_url is required')

    sources_dir = get_sources_path()
    makedirs(sources_dir, exist_ok=True)

    # 使用GitService解析URL
    parsed = GitService.parse_repo_url(repo_url)
    if not parsed:
        return web.Response(status=400, text='invalid repo url')
    
    author, name = parsed
    target_dir = path.join(sources_dir, f'{author}-{name}')
    
    # 使用GitService克隆仓库
    success, error_msg = GitService.clone_repo(repo_url, target_dir, depth=1)
    if not success:
        return web.Response(status=400, text=error_msg)

    return web.Response(status=201)


async def api_delete_source(request):
    """删除源"""
    name = request.match_info.get('name', None)

    if not name:
        return web.Response(status=401)

    sources_dir = get_sources_path()
    target_path = path.join(sources_dir, name)
    if not path.exists(target_path):
        return web.Response(status=404)

    shutil.rmtree(target_path, onerror=handle_remove_readonly)
    return web.Response(status=200)

async def api_sync_source(request):
    """同步源"""
    name = request.match_info.get('name', None)

    if not name:
        return web.Response(status=401)
    
    sources_dir = get_sources_path()
    repo_path = path.join(sources_dir, name)
    if not path.exists(repo_path):
        return web.Response(status=404)

    # 使用GitService拉取更新
    success, error_msg = GitService.pull(repo_path)
    if success:
        return web.Response(status=200)
    return web.Response(status=400, text=error_msg)

async def api_get_all_sources(_):
    """获取所有推荐源列表"""
    source_url = 'https://github.com/talesofai/comfyui-browser/raw/main/data/sources.json'
    file_path = path.join(str(BROWSER_PATH), 'data/sources.json')
    timeout = ClientTimeout(connect=2, total=4)

    sources = {"sources": []}
    try:
        async with ClientSession(timeout=timeout) as session:
            async with session.get(source_url) as resp:
                if resp.ok:
                    ret = await resp.text()
                    sources = json.loads(ret)
    except:
        with open(file_path, 'r', encoding="utf-8") as f:
            sources = json.load(f)

    return web.json_response(sources)
