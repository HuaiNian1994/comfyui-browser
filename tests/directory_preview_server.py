"""使用合成图片和独立数据库启动目录加载验收页面，不连接用户输出目录。"""
import argparse
import importlib
import io
import json
from pathlib import Path
import tempfile
import time

from aiohttp import web
from PIL import Image, PngImagePlugin

from benchmark_directory_loading import load_backend, in_directory


def create_fixtures(output, count):
    for number, folder in enumerate(('A', 'B')):
        directory = output / folder
        directory.mkdir(parents=True, exist_ok=True)
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('prompt', json.dumps({
            '1': {'class_type': 'CheckpointLoaderSimple', 'inputs': {'ckpt_name': f'model-{folder}.safetensors'}},
            '2': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 1], 'text': f'fixture {folder}'}},
            '3': {'class_type': 'EmptyLatentImage', 'inputs': {'width': 840, 'height': 1256, 'batch_size': 1}},
            '4': {'class_type': 'KSampler', 'inputs': {'model': ['1', 0], 'positive': ['2', 0], 'negative': ['2', 0],
                'latent_image': ['3', 0], 'steps': 20, 'cfg': 7, 'seed': 1, 'sampler_name': 'euler', 'scheduler': 'normal', 'denoise': 1}},
            '5': {'class_type': 'VAEDecode', 'inputs': {'samples': ['4', 0], 'vae': ['1', 2]}},
            '6': {'class_type': 'SaveImage', 'inputs': {'images': ['5', 0], 'filename_prefix': 'fixture'}}
        }))
        stream = io.BytesIO()
        with Image.new('RGB', (840, 1256), (50 + number * 110, 110, 180 - number * 60)) as image:
            image.save(stream, format='PNG', pnginfo=metadata)
        for index in range(count):
            target = directory / f'image_{index:05d}.png'
            if not target.exists():
                target.write_bytes(stream.getvalue())


def create_app(repository, working, count):
    output = working / 'outputs'
    create_fixtures(output, count)
    external = working / '外部目录 #1'
    external.mkdir()
    (external / 'image #1.png').write_bytes((output / 'A' / 'image_00000.png').read_bytes())
    (external / 'child').mkdir()
    (external / 'child' / 'nested.png').write_bytes((output / 'A' / 'image_00000.png').read_bytes())
    with in_directory(working):
        files = load_backend(repository, output)
        files.db_service.db_path = str(working / 'comfyui_browser.db')
    thumbnails = importlib.import_module('directory_benchmark.routes.thumbnails')
    directories = importlib.import_module('directory_benchmark.routes.directories')
    path_utils = importlib.import_module('directory_benchmark.utils.path_utils')
    registry_module = importlib.import_module('directory_benchmark.services.directory_registry')
    path_utils.directory_registry = registry_module.DirectoryRegistry(working / 'registered-directories.json')
    timings = []
    opened_folders = []

    @web.middleware
    async def capture(request, handler):
        started = time.perf_counter()
        response = await handler(request)
        if request.path.startswith('/browser/files'):
            timings.append({'path': request.path, 'query': dict(request.query), 'status': response.status,
                            'milliseconds': round((time.perf_counter() - started) * 1000, 3)})
        return response

    app = web.Application(middlewares=[capture])
    app[thumbnails.SERVICE_KEY] = thumbnails.ThumbnailService(cache_path=working / 'thumbnails')

    async def config(_):
        return web.json_response({'outputs': str(output), 'collections': str(output), 'sources': str(output),
                                  'download_logs': str(working), 'git_repo': ''})

    async def sources(_):
        return web.json_response({'sources': [{'name': 'A', 'title': '验收目录 A', 'author': 'fixture', 'url': ''},
                                             {'name': 'B', 'title': '验收目录 B', 'author': 'fixture', 'url': ''}]})

    async def metrics(_):
        return web.json_response({'requests': timings, 'opened_folders': opened_folders})

    async def open_folder(request):
        # 验收只记录打开意图，避免弹出宿主资源管理器。
        opened_folders.append(await request.json())
        return web.json_response({'success': True})

    app.add_routes([
        web.get('/browser/directories', directories.api_get_directories),
        web.post('/browser/directories', directories.api_register_directory),
        web.post('/browser/files/open-folder', open_folder),
        web.get('/browser/files', files.api_get_files),
        web.get('/browser/files/view', files.api_view_file),
        web.post('/browser/files/summary-updates', files.api_get_summary_updates),
        web.get('/browser/files/metadata', files.api_get_image_metadata),
        web.get('/browser/files/thumbnail', thumbnails.api_get_thumbnail),
        web.get('/browser/files/tags', files.api_get_all_tags),
        web.post('/browser/files/reindex', files.api_reindex_files),
        web.get('/browser/files/reindex/{job_id}', files.api_get_reindex_job),
        web.get('/browser/config', config),
        web.get('/browser/sources', sources), web.get('/browser/sources/all', sources),
        web.get('/__test/metrics', metrics),
        web.static('/browser/web', repository / 'web-ui' / 'release'),
        web.static('/browser/s/outputs', output), web.static('/browser/s/collections', output),
        web.static('/browser/s/sources', output),
    ])
    app.on_cleanup.extend([files.shutdown_file_services, thumbnails.shutdown_thumbnail_service])
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--count', type=int, default=1000)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='directory-preview-') as temporary:
        print(json.dumps({'temporary_directory': temporary, 'images_per_directory': args.count}), flush=True)
        app = create_app(Path(__file__).resolve().parents[1], Path(temporary), args.count)
        web.run_app(app, host='127.0.0.1', port=args.port, print=print)
