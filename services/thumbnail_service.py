"""有界图片工作池及插件专用缩略图缓存。"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time

from PIL import Image, ImageOps, UnidentifiedImageError, features

from ..utils.path_utils import file_version_from_stat

ALGORITHM_VERSION = 'pixels-v1'
SIZES = {256, 512, 1024}


class StaleThumbnail(Exception):
    """源文件版本已经变化。"""


class InvalidImage(Exception):
    """源文件无法解码。"""


@dataclass(frozen=True)
class Thumbnail:
    body: bytes
    content_type: str
    etag: str


class ThumbnailCache:
    """通过文件修改时间持久化 LRU；仅维护线程扫描目录和淘汰。"""
    def __init__(self, directory, budget):
        self.directory = Path(directory)
        self.budget = budget
        self.records = {}
        self.lock = threading.RLock()
        self.ready = threading.Event()
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.writable = True
        self.thread = threading.Thread(target=self._maintain, name='thumbnail-cache', daemon=True)
        self.thread.start()

    def _maintain(self):
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            for entry in self.directory.iterdir():
                if entry.suffix == '.thumb' and len(entry.stem) == 64:
                    stat = entry.stat()
                    self.records[entry.stem] = (stat.st_size, stat.st_mtime_ns)
                elif entry.name.startswith('thumbnail-') and entry.suffix == '.tmp':
                    entry.unlink(missing_ok=True)
        except OSError:
            self.writable = False
        finally:
            self._evict()
            self.ready.set()
        while not self.stop.is_set():
            self.wake.wait(1)
            self.wake.clear()
            self._evict()

    def _evict(self):
        with self.lock:
            total = sum(value[0] for value in self.records.values())
            if total <= self.budget:
                return
            for key, (size, _) in sorted(self.records.items(), key=lambda item: item[1][1]):
                if total <= self.budget:
                    break
                try:
                    (self.directory / (key + '.thumb')).unlink(missing_ok=True)
                except OSError:
                    continue
                self.records.pop(key, None)
                total -= size

    def get(self, key):
        self.ready.wait()
        with self.lock:
            if key not in self.records:
                return None
            target = self.directory / (key + '.thumb')
            try:
                data = target.read_bytes()
                now = time.time_ns()
                os.utime(target, ns=(now, now))
                self.records[key] = (len(data), now)
                return data
            except OSError:
                self.records.pop(key, None)
                return None

    def put(self, key, data):
        self.ready.wait()
        if not self.writable or len(data) > self.budget:
            return
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.directory, prefix='thumbnail-', suffix='.tmp', delete=False) as output:
                temporary = Path(output.name)
                output.write(data)
            with self.lock:
                target = self.directory / (key + '.thumb')
                os.replace(temporary, target)
                self.records[key] = (len(data), target.stat().st_mtime_ns)
            self.wake.set()
        except OSError:
            self.writable = False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def close(self):
        self.stop.set()
        self.wake.set()
        self.thread.join()


class ThumbnailService:
    def __init__(self, cache_path=None, budget=512 * 1024 * 1024):
        self.cache = ThumbnailCache(cache_path or Path(__file__).resolve().parents[1] / '.cache' / 'thumbnails', budget)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='thumbnail')
        self.lock = threading.RLock()
        self.inflight = {}
        self.closed = False

    @staticmethod
    def _check_version(path, version):
        if file_version_from_stat(os.stat(path)) != version:
            raise StaleThumbnail()

    @staticmethod
    def cache_key(path, version, size):
        return hashlib.sha256(json.dumps([os.path.realpath(path), version, size, ALGORITHM_VERSION], ensure_ascii=False).encode()).hexdigest()

    def _generate(self, path, version, size, key):
        self._check_version(path, version)
        data = self.cache.get(key)
        if data is None:
            try:
                with Image.open(path) as source:
                    source.seek(0)
                    with ImageOps.exif_transpose(source) as oriented:
                        mode = 'RGBA' if 'A' in oriented.getbands() or 'transparency' in oriented.info else 'RGB'
                        with oriented.convert(mode) as pixels:
                            pixels.thumbnail((size, size), Image.Resampling.LANCZOS)
                            # 清空继承的元数据，只把像素传入编码器。
                            pixels.info.clear()
                            with io.BytesIO() as output:
                                if features.check('webp'):
                                    pixels.save(output, format='WEBP', lossless=True)
                                else:
                                    pixels.save(output, format='PNG')
                                data = output.getvalue()
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
                self._check_version(path, version)
                raise InvalidImage() from error
            self._check_version(path, version)
            self.cache.put(key, data)
        self._check_version(path, version)
        content_type = 'image/png' if data.startswith(b'\x89PNG') else 'image/webp'
        return Thumbnail(data, content_type, '"' + hashlib.sha256(data).hexdigest() + '"')

    async def get(self, path, version, size=512):
        if size not in SIZES or not version:
            raise ValueError('无效缩略图参数')
        key = await asyncio.to_thread(self.cache_key, path, version, size)
        with self.lock:
            if self.closed:
                raise RuntimeError('缩略图服务已经关闭')
            entry = self.inflight.get(key)
            if entry is None or entry[0].done():
                entry = [self.executor.submit(self._generate, path, version, size, key), 0]
                self.inflight[key] = entry
            entry[1] += 1
        try:
            wrapped = asyncio.wrap_future(entry[0])
            wrapped.add_done_callback(lambda future: future.exception() if not future.cancelled() else None)
            return await asyncio.shield(wrapped)
        finally:
            with self.lock:
                entry[1] -= 1
                if entry[1] == 0:
                    # 只取消尚未开始且没有等待者的工作；运行中的生成仍可写入缓存。
                    entry[0].cancel()
                    if entry[0].done():
                        if self.inflight.get(key) is entry:
                            self.inflight.pop(key, None)
                    else:
                        entry[0].add_done_callback(lambda future: self._forget(key, entry))

    def _forget(self, key, entry):
        with self.lock:
            if self.inflight.get(key) is entry and entry[1] == 0:
                self.inflight.pop(key, None)

    async def shutdown(self):
        with self.lock:
            self.closed = True
        await asyncio.to_thread(self.executor.shutdown, wait=True, cancel_futures=True)
        await asyncio.to_thread(self.cache.close)
