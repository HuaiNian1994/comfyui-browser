"""在真实 aiohttp 路由与独立数据库中验证目录、摘要、重建和缩略图。"""
import asyncio
import importlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import uuid
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from PIL import Image

from benchmark_directory_loading import load_backend, in_directory


class DirectoryIntegrationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='directory-integration-')
        cls.root = Path(cls.temporary.name)
        cls.output = cls.root / 'outputs'
        cls.output.mkdir()
        with in_directory(cls.root):
            cls.routes = load_backend(Path(__file__).resolve().parents[1], cls.output)
        cls.thumbnails = importlib.import_module('directory_benchmark.routes.thumbnails')
        cls.directories = importlib.import_module('directory_benchmark.routes.directories')
        cls.path_utils = importlib.import_module('directory_benchmark.utils.path_utils')
        cls.registry_module = importlib.import_module('directory_benchmark.services.directory_registry')
        cls.previous_registry = cls.path_utils.directory_registry
        cls.path_utils.directory_registry = cls.registry_module.DirectoryRegistry(cls.root / 'directories.json')

    @classmethod
    def tearDownClass(cls):
        cls.routes.reindex_service.shutdown()
        cls.routes.directory_scan_service.shutdown()
        cls.routes.metadata_index_queue.shutdown()
        cls.path_utils.directory_registry = cls.previous_registry
        cls.temporary.cleanup()

    async def asyncSetUp(self):
        self.folder = uuid.uuid4().hex
        self.directory = self.output / self.folder
        self.directory.mkdir()
        self.db = self.routes.DBService(str(self.root / (self.folder + '.db')))
        self.release = threading.Event()
        self.release.set()

        def extract(_):
            self.release.wait(5)
            return {'parser_version': self.routes.PARSER_VERSION, 'parse_status': 'complete',
                    'width': 840, 'height': 1256, 'models': ['integration-model'], 'loras': [],
                    'positive_prompt': '完整详情内容' * 1000, 'stages': [{'id': 'fixture-stage'}]}

        self.queue = self.routes.MetadataIndexQueue(self.db, extract)
        self.app = web.Application()
        self.app['file_database'] = self.db
        self.app['file_metadata_queue'] = self.queue
        self.app[self.thumbnails.SERVICE_KEY] = self.thumbnails.ThumbnailService(cache_path=self.root / ('cache-' + self.folder))

        async def ping(_):
            return web.json_response({'alive': True})

        self.app.add_routes([
            web.get('/directories', self.directories.api_get_directories),
            web.post('/directories', self.directories.api_register_directory),
            web.get('/files', self.routes.api_get_files),
            web.get('/files/view', self.routes.api_view_file),
            web.post('/files/summary-updates', self.routes.api_get_summary_updates),
            web.get('/files/metadata', self.routes.api_get_image_metadata),
            web.post('/files/reindex', self.routes.api_reindex_files),
            web.get('/files/reindex/{job_id}', self.routes.api_get_reindex_job),
            web.get('/files/thumbnail', self.thumbnails.api_get_thumbnail),
            web.get('/ping', ping),
        ])
        self.app.on_cleanup.append(self.thumbnails.shutdown_thumbnail_service)
        self.client = TestClient(TestServer(self.app))
        await self.client.start_server()

    async def asyncTearDown(self):
        self.release.set()
        await asyncio.to_thread(self.queue.wait_until_idle, 5)
        await self.client.close()
        await asyncio.to_thread(self.queue.shutdown)

    def make_image(self, name='image #1.png', folder=None):
        target = (folder or self.directory) / name
        with Image.new('RGBA', (840, 1256), (50, 100, 150, 100)) as image:
            image.save(target)
        return target

    async def listing(self):
        response = await self.client.get('/files', params={'folder_type': 'outputs', 'folder_path': self.folder})
        self.assertEqual(response.status, 200)
        return (await response.json())['files']

    @staticmethod
    def identity(file):
        return {key: file[key] for key in ('folder_path', 'name', 'file_version', 'index_generation')}

    async def test_lightweight_then_completed_summary_and_original_details(self):
        self.make_image()
        self.release.clear()
        file = (await self.listing())[0]
        self.assertNotIn('formatted_info', file)
        self.assertTrue(file['metadata_pending'])
        self.release.set()
        self.assertTrue(await asyncio.to_thread(self.queue.wait_until_idle, 5))
        payload = {'folder_type': 'outputs', 'files': [self.identity(file)], 'visible_files': [], 'session_id': 'integration'}
        # 缓存已完成时补齐只使用轻量数据库字段，不访问图片或全目录扫描。
        with patch.object(self.routes, 'get_target_folder_files', side_effect=AssertionError('不应扫描目录')), \
             patch.object(self.routes, 'extract_detailed_metadata', side_effect=AssertionError('不应读取图片')):
            response = await self.client.post('/files/summary-updates', json=payload)
        self.assertEqual(response.status, 200)
        item = (await response.json())['files'][0]
        self.assertEqual(item['status'], 'complete')
        self.assertEqual(item['summary']['models'], ['integration-model'])
        self.assertNotIn('positive_prompt', item['summary'])
        completed = (await self.listing())[0]
        self.assertNotIn('formatted_info', completed)
        self.assertEqual(completed['summary']['models'], ['integration-model'])
        response = await self.client.get('/files/metadata', params={'folder_type': 'outputs', 'folder_path': self.folder,
            'filename': file['name'], 'file_version': file['file_version'], 'index_generation': file['index_generation']})
        self.assertEqual(response.status, 200)
        self.assertTrue((await response.json())['positive'])
        response = await self.client.post('/files/summary-updates', json={**payload, 'files': payload['files'] * 201})
        self.assertEqual(response.status, 400)

    async def test_stale_summary_and_thumbnail_version_are_rejected(self):
        image = self.make_image()
        file = (await self.listing())[0]
        await asyncio.to_thread(self.queue.wait_until_idle, 5)
        query = {'folder_type': 'outputs', 'folder_path': self.folder, 'filename': file['name'],
                 'file_version': file['file_version'], 'size': '256'}
        first = await self.client.get('/files/thumbnail', params=query)
        self.assertEqual(first.status, 200)
        etag = first.headers['ETag']
        await first.read()
        cached = await self.client.get('/files/thumbnail', params=query, headers={'If-None-Match': etag})
        self.assertEqual(cached.status, 304)
        with Image.new('RGB', (32, 32), 'red') as replacement:
            replacement.save(image)
        await self.listing()
        response = await self.client.post('/files/summary-updates', json={'folder_type': 'outputs',
            'files': [self.identity(file)], 'visible_files': [], 'session_id': 'version'})
        self.assertEqual((await response.json())['files'][0]['status'], 'stale')
        response = await self.client.get('/files/thumbnail', params=query, headers={'If-None-Match': etag})
        self.assertEqual(response.status, 409)

    async def test_reindex_scope_and_completion_preserve_tags(self):
        self.make_image()
        nested = self.directory / 'child'
        nested.mkdir()
        self.make_image('nested.png', nested)
        file = next(row for row in await self.listing() if row['type'] == 'file')
        await asyncio.to_thread(self.queue.wait_until_idle, 5)
        self.db.update_file_tags(file['name'], self.folder, 'outputs', ['保留标签'])
        self.release.clear()
        response = await self.client.post('/files/reindex', json={'folder_type': 'outputs', 'folder_paths': [self.folder]})
        self.assertEqual(response.status, 202)
        job_id = (await response.json())['job_id']
        for _ in range(100):
            status = await (await self.client.get('/files/reindex/' + job_id)).json()
            if status['scan_complete']:
                break
            await asyncio.sleep(.02)
        self.assertTrue(status['scan_complete'])
        self.assertEqual(status['status'], 'running')
        self.assertEqual(status['indexed_folders'], 1)
        self.assertEqual(status['indexed_files'], 1)
        self.release.set()
        for _ in range(100):
            status = await (await self.client.get('/files/reindex/' + job_id)).json()
            if status['status'] == 'complete':
                break
            await asyncio.sleep(.02)
        self.assertEqual(status['status'], 'complete')
        record = self.db.get_file(file['name'], self.folder, 'outputs')
        self.assertEqual(record['tags'], ['保留标签'])
        self.assertGreater(record['index_generation'], file['index_generation'])
        self.assertEqual(self.db.get_files_in_folder(self.folder + '/child', 'outputs'), {})

    async def test_slow_directory_scan_keeps_other_requests_responsive(self):
        self.make_image()
        entered = threading.Event()
        finish = threading.Event()
        original = self.routes.synchronize_folder

        def slow(*args, **kwargs):
            entered.set()
            finish.wait(3)
            return original(*args, **kwargs)

        with patch.object(self.routes, 'synchronize_folder', side_effect=slow):
            loading = asyncio.create_task(self.listing())
            self.assertTrue(await asyncio.to_thread(entered.wait, 2))
            started = time.perf_counter()
            try:
                response = await asyncio.wait_for(self.client.get('/ping'), timeout=1)
                self.assertEqual(response.status, 200)
                self.assertLess(time.perf_counter() - started, 1)
            finally:
                finish.set()
            await loading

    async def test_registered_external_directory_supports_original_thumbnail_and_summary(self):
        external = self.root / ('外部目录 # ' + self.folder)
        external.mkdir()
        image = self.make_image('图像 #1.png', external)
        nested = external / 'child'
        nested.mkdir()
        self.make_image('nested.png', nested)
        response = await self.client.post('/directories', json={'path': str(external)})
        self.assertIn(response.status, (200, 201))
        directory = (await response.json())['directory']
        self.assertTrue(directory['path'].startswith('@external/'))
        duplicate = await self.client.post('/directories', json={'path': str(external)})
        self.assertEqual((await duplicate.json())['directory']['path'], directory['path'])
        saved = (await (await self.client.get('/directories')).json())['directories']
        self.assertIn(directory, saved)
        response = await self.client.get('/files', params={'folder_type': 'outputs',
            'folder_path': directory['path']})
        self.assertEqual(response.status, 200)
        rows = (await response.json())['files']
        file = next(row for row in rows if row['name'] == image.name)
        self.assertNotIn('nested.png', [row['name'] for row in rows])
        self.assertTrue(await asyncio.to_thread(self.queue.wait_until_idle, 5))
        updates = await self.client.post('/files/summary-updates', json={'folder_type': 'outputs',
            'files': [self.identity(file)], 'visible_files': [], 'session_id': 'external'})
        self.assertEqual((await updates.json())['files'][0]['status'], 'complete')
        query = {'folder_type': 'outputs', 'folder_path': directory['path'], 'filename': image.name}
        original = await self.client.get('/files/view', params=query)
        self.assertEqual(original.status, 200)
        self.assertEqual(await original.read(), image.read_bytes())
        workflow = external / '图像 #1.json'
        workflow.write_text('{"nodes": []}', encoding='utf-8')
        workflow_response = await self.client.get('/files/view', params={**query, 'filename': workflow.name})
        self.assertEqual(workflow_response.status, 200)
        self.assertEqual(await workflow_response.json(), {'nodes': []})
        thumbnail = await self.client.get('/files/thumbnail', params={**query,
            'file_version': file['file_version'], 'size': '256'})
        self.assertEqual(thumbnail.status, 200)
        self.assertTrue((await thumbnail.read()))
        metadata = await self.client.get('/files/metadata', params=query)
        self.assertEqual(metadata.status, 200)
        self.assertTrue((await metadata.json())['positive'])
        invalid = await self.client.post('/directories', json={'path': str(external / 'missing')})
        self.assertIn(invalid.status, (400, 404))


if __name__ == '__main__':
    unittest.main()
