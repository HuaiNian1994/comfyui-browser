"""输出页可选服务器目录的登记接口。"""
import asyncio
from aiohttp import web
from ..utils import path_utils


async def api_get_directories(request):
    try:
        directories=await asyncio.to_thread(path_utils.directory_registry.list)
        return web.json_response({'directories':directories})
    except (OSError,ValueError):
        return web.json_response({'error':'registry_unavailable'},status=500)


async def api_register_directory(request):
    try:
        data=await request.json()
        if not isinstance(data,dict):
            raise ValueError('Invalid request')
        directory=await asyncio.to_thread(path_utils.directory_registry.register,data.get('path'),path_utils.get_parent_path('outputs'))
        return web.json_response({'directory':directory},status=201)
    except FileNotFoundError:
        return web.json_response({'error':'directory_not_found'},status=404)
    except (ValueError,TypeError):
        return web.json_response({'error':'invalid_path'},status=400)
    except OSError:
        return web.json_response({'error':'registry_unavailable'},status=500)
