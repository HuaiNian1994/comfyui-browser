"""按文件版本提供缩略图及条件缓存响应。"""
import asyncio
from aiohttp import web

from ..services.thumbnail_service import ThumbnailService, StaleThumbnail, InvalidImage
from ..utils.path_utils import resolve_file_path

SERVICE_KEY = 'browser_thumbnail_service'


async def api_get_thumbnail(request):
    try:
        query = request.query
        target = await asyncio.to_thread(resolve_file_path, query.get('folder_type', 'outputs'), query.get('folder_path', ''), query.get('filename', ''))
        version = query.get('file_version', '')
        size = int(query.get('size', '512'))
        if SERVICE_KEY not in request.app:
            request.app[SERVICE_KEY] = ThumbnailService()
        result = await request.app[SERVICE_KEY].get(target, version, size)
        headers = {'ETag': result.etag, 'Cache-Control': 'private, max-age=31536000, immutable', 'Content-Type': result.content_type}
        tags = [tag.strip().removeprefix('W/') for tag in request.headers.get('If-None-Match', '').split(',')]
        if '*' in tags or result.etag in tags:
            return web.Response(status=304, headers=headers)
        return web.Response(body=result.body, headers=headers)
    except ValueError:
        return web.json_response({'error': 'invalid_parameters'}, status=400)
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError):
        return web.json_response({'error': 'missing'}, status=404)
    except StaleThumbnail:
        return web.json_response({'error': 'stale'}, status=409)
    except InvalidImage:
        return web.json_response({'error': 'invalid_image'}, status=422)


async def shutdown_thumbnail_service(app):
    service = app.get(SERVICE_KEY)
    if service is not None:
        await service.shutdown()
