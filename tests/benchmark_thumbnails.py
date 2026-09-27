"""测量二十张可见图片的缩略图冷缓存与热缓存，五次取中位数。"""
import asyncio
import importlib
import json
from pathlib import Path
import statistics
import tempfile
import time

from PIL import Image

from benchmark_directory_loading import in_directory, load_backend


async def measure():
    with tempfile.TemporaryDirectory(prefix='thumbnail-benchmark-') as temporary:
        root = Path(temporary)
        output = root / 'outputs'
        output.mkdir()
        with in_directory(root):
            routes = load_backend(Path(__file__).resolve().parents[1], output)
        module = importlib.import_module('directory_benchmark.services.thumbnail_service')
        images = []
        for index in range(20):
            target = output / f'{index}.png'
            with Image.effect_noise((840, 1256), 70).convert('RGB') as source:
                source.save(target)
            stat = target.stat()
            images.append((str(target), f'{stat.st_mtime_ns}:{stat.st_size}'))
        measured = {'cold': [], 'warm': []}
        for repetition in range(5):
            service = module.ThumbnailService(cache_path=root / f'cache-{repetition}')
            try:
                for phase in measured:
                    started = time.perf_counter()
                    tasks = [asyncio.create_task(service.get(filename, version, 512)) for filename, version in images]
                    first = None
                    length = 0
                    for future in asyncio.as_completed(tasks):
                        result = await future
                        if first is None:
                            first = (time.perf_counter() - started) * 1000
                        length += len(result.body)
                    measured[phase].append({'first_ms': first, 'all_20_ms': (time.perf_counter() - started) * 1000,
                                             'bytes': length})
            finally:
                await service.shutdown()
        print(json.dumps({'original_bytes': sum(Path(name).stat().st_size for name, _ in images),
            'repeats': 5, 'visible_images': 20, 'size': 512,
            **{phase: {key: round(statistics.median(row[key] for row in rows), 3) for key in rows[0]}
               for phase, rows in measured.items()}}), flush=True)
        await routes.shutdown_file_services({})


if __name__ == '__main__':
    asyncio.run(measure())
