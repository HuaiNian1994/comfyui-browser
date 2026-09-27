"""缩略图使用独立临时目录，覆盖像素、并发、缓存及 HTTP 契约。"""
import asyncio
import importlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image, PngImagePlugin
from module_loader import ROOT

for name, directory in [('thumbnail_test', ROOT), ('thumbnail_test.services', ROOT / 'services'),
                        ('thumbnail_test.utils', ROOT / 'utils')]:
    package = ModuleType(name)
    package.__path__ = [str(directory)]
    sys.modules[name] = package
config = ModuleType('thumbnail_test.config')
config.get_collections_path = config.get_sources_path = config.get_outputs_path = lambda: ''
sys.modules['thumbnail_test.config'] = config
module = importlib.import_module('thumbnail_test.services.thumbnail_service')
spec = importlib.util.spec_from_file_location('thumbnail_test.routes.thumbnails', ROOT / 'routes/thumbnails.py')
routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routes)


class ThumbnailTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.service = module.ThumbnailService(self.root / 'cache')
        self.file = self.root / 'source.png'
        with Image.new('RGB', (800, 400), 'red') as image:
            image.save(self.file)

    async def asyncTearDown(self):
        await self.service.shutdown()
        self.directory.cleanup()

    def version(self):
        return module.file_version_from_stat(self.file.stat())

    async def get(self, size=256):
        return await self.service.get(str(self.file), self.version(), size)

    async def immediate_cache_key(self, callback, *args):
        # 完成任务边界测试固定键计算的交接时序；慢路径由独立响应性测试覆盖。
        self.assertEqual(callback, self.service.cache_key)
        return callback(*args)

    async def test_dimensions_metadata_and_no_upscale(self):
        info = PngImagePlugin.PngInfo()
        info.add_text('workflow', 'secret graph')
        with Image.new('RGBA', (40, 20), (10, 20, 30, 90)) as image:
            image.save(self.file, pnginfo=info)
        result = await self.get()
        with Image.open(io.BytesIO(result.body)) as image:
            self.assertEqual(image.size, (40, 20))
            self.assertEqual(image.convert('RGBA').getpixel((0, 0))[3], 90)
            self.assertNotIn('workflow', image.info)
            self.assertFalse(image.getexif())

    async def test_exif_orientation(self):
        self.file = self.root / 'rotated.jpg'
        with Image.new('RGB', (600, 300), 'red') as image:
            exif = Image.Exif()
            exif[274] = 6
            image.save(self.file, exif=exif)
        result = await self.get()
        with Image.open(io.BytesIO(result.body)) as image:
            self.assertEqual(image.size, (128, 256))
            self.assertFalse(image.getexif())

    async def test_animation_first_frame(self):
        self.file = self.root / 'animated.gif'
        with Image.new('RGB', (30, 20), 'red') as first, Image.new('RGB', (30, 20), 'blue') as second:
            first.save(self.file, save_all=True, append_images=[second], duration=100)
        result = await self.get()
        with Image.open(io.BytesIO(result.body)) as image:
            self.assertEqual(image.convert('RGB').getpixel((0, 0)), (255, 0, 0))
            self.assertEqual(getattr(image, 'n_frames', 1), 1)

    async def test_png_fallback(self):
        with patch.object(module.features, 'check', return_value=False):
            result = await self.get()
        self.assertEqual(result.content_type, 'image/png')
        self.assertTrue(result.body.startswith(b'\x89PNG'))

    async def test_singleflight_and_cancelled_waiter(self):
        entered, release = threading.Event(), threading.Event()
        original = self.service._generate
        count = []
        def generate(*args):
            count.append(1)
            entered.set()
            release.wait(3)
            return original(*args)
        with patch.object(self.service, '_generate', side_effect=generate):
            first = asyncio.create_task(self.get())
            self.assertTrue(await asyncio.to_thread(entered.wait, 2))
            second = asyncio.create_task(self.get())
            await asyncio.sleep(0)
            first.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await first
            release.set()
            result = await second
        self.assertEqual(len(count), 1)
        self.assertTrue(result.body)

    async def test_source_version_race_and_deleted_source(self):
        original = module.Image.Image.save
        def save(image, *args, **kwargs):
            original(image, *args, **kwargs)
            self.file.write_bytes(b'changed')
        with patch.object(module.Image.Image, 'save', new=save):
            with self.assertRaises(module.StaleThumbnail):
                await self.get()
        self.assertEqual(list((self.root / 'cache').glob('*.thumb')), [])
        version = self.version()
        self.file.unlink()
        with self.assertRaises(FileNotFoundError):
            await self.service.get(str(self.file), version)

    async def test_two_workers_and_cancel_queued_job(self):
        release = threading.Event()
        two_started = threading.Event()
        started = []
        original = self.service._generate
        def generate(*args):
            started.append(args[2])
            if len(started) == 2:
                two_started.set()
            release.wait(3)
            return original(*args)
        with patch.object(self.service, '_generate', side_effect=generate):
            first = asyncio.create_task(self.get(256))
            second = asyncio.create_task(self.get(512))
            self.assertTrue(await asyncio.to_thread(two_started.wait, 2))
            queued = asyncio.create_task(self.get(1024))
            await asyncio.sleep(0)
            queued.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await queued
            release.set()
            await asyncio.gather(first, second)
        self.assertCountEqual(started, [256, 512])

    async def test_finished_future_rechecks_version_before_old_waiter_releases(self):
        version = self.version()
        entered, release = threading.Event(), threading.Event()
        original = self.service._generate
        def generate(*args):
            entered.set()
            release.wait(3)
            return original(*args)
        with patch.object(self.service, '_generate', side_effect=generate):
            first = asyncio.create_task(self.service.get(str(self.file), version, 256))
            self.assertTrue(await asyncio.to_thread(entered.wait, 2))
        key = self.service.cache_key(str(self.file), version, 256)
        old_entry = self.service.inflight[key]
        # 暂停事件循环，确定工作线程已完成而首个等待者仍未进入 finally。
        release.set()
        old_entry[0].result(timeout=3)
        self.assertEqual(old_entry[1], 1)
        self.file.write_bytes(b'changed after completion')
        with patch.object(module.asyncio, 'to_thread', side_effect=self.immediate_cache_key):
            with self.assertRaises(module.StaleThumbnail):
                await self.service.get(str(self.file), version, 256)
        await first
        self.assertNotIn(key, self.service.inflight)

    async def test_old_waiter_cleanup_preserves_replacement_entry(self):
        version = self.version()
        entered, first_release = threading.Event(), threading.Event()
        original = self.service._generate
        def first_generate(*args):
            entered.set()
            first_release.wait(3)
            return original(*args)
        with patch.object(self.service, '_generate', side_effect=first_generate):
            first = asyncio.create_task(self.service.get(str(self.file), version, 256))
            self.assertTrue(await asyncio.to_thread(entered.wait, 2))
        key = self.service.cache_key(str(self.file), version, 256)
        old_entry = self.service.inflight[key]
        first_release.set()
        old_entry[0].result(timeout=3)
        release = threading.Event()
        original = self.service._generate
        def generate(*args):
            release.wait(3)
            return original(*args)
        async def observe_cleanup():
            try:
                await first
                self.assertIn(key, self.service.inflight)
                self.assertIsNot(self.service.inflight[key], old_entry)
            finally:
                release.set()
        observer = asyncio.create_task(observe_cleanup())
        with patch.object(self.service, '_generate', side_effect=generate), \
                patch.object(module.asyncio, 'to_thread', side_effect=self.immediate_cache_key):
            await self.service.get(str(self.file), version, 256)
        await observer

    async def test_cancelled_generation_failure_is_consumed(self):
        entered, release = threading.Event(), threading.Event()
        def generate(*args):
            entered.set()
            release.wait(2)
            raise module.StaleThumbnail()
        errors = []
        asyncio.get_running_loop().set_exception_handler(lambda loop, context: errors.append(context))
        with patch.object(self.service, '_generate', side_effect=generate):
            task = asyncio.create_task(self.get())
            self.assertTrue(await asyncio.to_thread(entered.wait, 2))
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            release.set()
            await self.service.shutdown()
            await asyncio.sleep(0)
        self.assertEqual(errors, [])

    async def test_unwritable_cache_falls_back(self):
        await asyncio.to_thread(self.service.cache.ready.wait)
        with patch.object(module.tempfile, 'NamedTemporaryFile', side_effect=PermissionError):
            result = await self.get()
        self.assertTrue(result.body)
        self.assertFalse(self.service.cache.writable)
        self.assertFalse(list((self.root / 'cache').glob('*.tmp')))

    async def test_lru_restore_and_budget(self):
        await self.service.shutdown()
        cache = self.root / 'restored'
        cache.mkdir()
        old = cache / ('a' * 64 + '.thumb')
        new = cache / ('b' * 64 + '.thumb')
        old.write_bytes(b'x' * 50)
        new.write_bytes(b'y' * 50)
        os.utime(old, ns=(100, 100))
        os.utime(new, ns=(200, 200))
        self.service = module.ThumbnailService(cache, budget=60)
        self.assertTrue(await asyncio.to_thread(self.service.cache.ready.wait, 2))
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())
        self.service.cache.put('c' * 64, b'z' * 50)
        deadline = time.monotonic() + 2
        while new.exists() and time.monotonic() < deadline:
            await asyncio.sleep(.01)
        self.assertFalse(new.exists())

    async def test_slow_path_resolution_keeps_event_loop_responsive(self):
        entered, release = threading.Event(), threading.Event()
        loop_thread = threading.get_ident()
        resolver_threads = []
        request = SimpleNamespace(query={'filename': self.file.name, 'file_version': self.version(), 'size': '256'},
                                  app={routes.SERVICE_KEY: self.service}, headers={})
        def slow_resolve(*args):
            resolver_threads.append(threading.get_ident())
            entered.set()
            release.wait(2)
            return str(self.file)
        with patch.object(routes, 'resolve_file_path', side_effect=slow_resolve):
            task = asyncio.create_task(routes.api_get_thumbnail(request))
            try:
                self.assertTrue(await asyncio.to_thread(entered.wait, 1))
                # 路径解析仍在等待时，另一个协程能够完成。
                heartbeat = asyncio.create_task(asyncio.sleep(0, result='responsive'))
                self.assertEqual(await asyncio.wait_for(heartbeat, .5), 'responsive')
                self.assertNotIn(loop_thread, resolver_threads)
                self.assertFalse(task.done())
            finally:
                release.set()
                response = await task
        self.assertEqual(response.status, 200)

    async def test_slow_cache_key_keeps_event_loop_responsive(self):
        entered, release = threading.Event(), threading.Event()
        loop_thread = threading.get_ident()
        key_threads = []
        original = self.service.cache_key
        def slow_cache_key(*args):
            key_threads.append(threading.get_ident())
            entered.set()
            release.wait(2)
            return original(*args)
        with patch.object(self.service, 'cache_key', side_effect=slow_cache_key):
            task = asyncio.create_task(self.get())
            try:
                self.assertTrue(await asyncio.to_thread(entered.wait, 1))
                heartbeat = asyncio.create_task(asyncio.sleep(0, result='responsive'))
                self.assertEqual(await asyncio.wait_for(heartbeat, .5), 'responsive')
                self.assertNotIn(loop_thread, key_threads)
                self.assertFalse(task.done())
            finally:
                release.set()
                result = await task
        self.assertTrue(result.body)

    async def test_http_conditional_and_errors(self):
        request = SimpleNamespace(query={'filename': self.file.name, 'file_version': self.version(), 'size': '256'},
                                  app={routes.SERVICE_KEY: self.service}, headers={})
        with patch.object(routes, 'resolve_file_path', return_value=str(self.file)):
            response = await routes.api_get_thumbnail(request)
            self.assertEqual(response.status, 200)
            self.assertIn(response.content_type, {'image/webp', 'image/png'})
            request.headers['If-None-Match'] = '"other", W/' + response.headers['ETag']
            cached = await routes.api_get_thumbnail(request)
            self.assertEqual(cached.status, 304)
            self.assertEqual(cached.headers['Content-Type'], response.headers['Content-Type'])
            request.query['file_version'] = 'old'
            self.assertEqual((await routes.api_get_thumbnail(request)).status, 409)
            self.file.write_bytes(b'broken image')
            request.query['file_version'] = self.version()
            self.assertEqual((await routes.api_get_thumbnail(request)).status, 422)
            self.file.unlink()
            self.assertEqual((await routes.api_get_thumbnail(request)).status, 404)
            request.query['size'] = '1'
            self.assertEqual((await routes.api_get_thumbnail(request)).status, 400)
        with patch.object(routes, 'resolve_file_path', side_effect=ValueError):
            self.assertEqual((await routes.api_get_thumbnail(request)).status, 400)


if __name__ == '__main__':
    unittest.main()
