"""在独立目录与数据库测量目录同步，使用当前接口记录冷、热索引结果。"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import importlib
import io
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time
import types
from unittest.mock import patch


@contextmanager
def in_directory(directory):
    previous = Path.cwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(previous)


def load_backend(repository: Path, output: Path):
    """隔离 ComfyUI 启动，加载真实路由及其实际依赖。"""
    name = "directory_benchmark"
    package = types.ModuleType(name)
    package.__path__ = [str(repository)]
    sys.modules[name] = package
    config = types.ModuleType(f"{name}.config")
    config.BROWSER_PATH = repository
    config.get_outputs_path = lambda: str(output)
    config.get_collections_path = lambda: str(output)
    config.get_sources_path = lambda: str(output)
    sys.modules[config.__name__] = config
    for child in ("utils", "services", "routes"):
        module = types.ModuleType(f"{name}.{child}")
        module.__path__ = [str(repository / child)]
        sys.modules[module.__name__] = module
    utilities = sys.modules[f"{name}.utils"]
    for module_name, symbols in (
        ("utils.file_utils", ("get_target_folder_files",)),
        ("utils.path_utils", ("get_parent_path", "get_info_filename")),
        ("utils.image_utils", ("extract_comfyui_png_metadata", "extract_detailed_metadata")),
    ):
        module = importlib.import_module(f"{name}.{module_name}")
        for symbol in symbols:
            setattr(utilities, symbol, getattr(module, symbol))
    return importlib.import_module(f"{name}.routes.files")


def run(repository: Path, counts: list[int], repeats: int, scenarios: list[str]):
    from PIL import Image
    stream = io.BytesIO()
    image = Image.new("RGB", (840, 1256), (80, 120, 160))
    image.save(stream, format="PNG")
    image.close()
    image_bytes = stream.getvalue()
    results = []
    with tempfile.TemporaryDirectory(prefix="directory-benchmark-") as temporary, in_directory(temporary):
        working = Path(temporary)
        output = working / "outputs"
        output.mkdir()
        routes = load_backend(repository, output)
        for scenario in scenarios:
            for count in counts:
                folders = [f"{scenario}-{count}/part-{i}" for i in range(2 if scenario == "multiple" else 1)]
                for folder in folders:
                    (output / folder).mkdir(parents=True)
                for i in range(count):
                    folder = output / folders[i % len(folders)]
                    (folder / f"image_{i:05d}.png").write_bytes(image_bytes)
                    if scenario == "paired":
                        (folder / f"image_{i:05d}.json").write_text('{"nodes": []}', encoding="utf-8")
                samples = {"cold": [], "warm": []}
                for repetition in range(repeats):
                    db = routes.DBService(str(working / f"{scenario}-{count}-{repetition}.db"))
                    for phase in ("cold", "warm"):
                        if phase == "warm":
                            # 完整执行图仅作响应成本夹具，不运行图片解析队列。
                            info = {"parser_version": routes.PARSER_VERSION, "index_status": "complete",
                                    "parse_status": "complete", "width": 840, "height": 1256,
                                    "models": ["fixture-model"], "loras": []}
                            if scenario == "metadata":
                                info.update(positive_prompt="fixture prompt " * 1000,
                                            stages=[{"id": "sampler", "properties": [{"value": "value " * 1000}]}])
                            connection = db._get_connection()
                            try:
                                connection.execute("UPDATE files SET formatted_info=?", (json.dumps(info),))
                                summary = {key: value for key, value in info.items() if key in
                                           ('width', 'height', 'models', 'loras', 'parser_version', 'parse_status')}
                                connection.execute("UPDATE files SET summary=?", (json.dumps(summary),))
                                connection.commit()
                            finally:
                                connection.close()
                        started = time.perf_counter()
                        with patch.object(db, "_get_connection", wraps=db._get_connection) as connections:
                            files = []
                            for folder in folders:
                                files.extend(routes.synchronize_folder(folder, "outputs", database=db, metadata_queue=None))
                            query_seconds = time.perf_counter() - started
                            response_bytes = len(json.dumps({"files": files}, ensure_ascii=False).encode())
                        samples[phase].append({"seconds": query_seconds, "connections": connections.call_count,
                                               "response_bytes": response_bytes})
                record = {"scenario": scenario, "images": count, "repeats": repeats,
                          **{phase: {key: round(statistics.median(sample[key] for sample in entries), 6)
                                     for key in entries[0]} for phase, entries in samples.items()}}
                results.append(record)
                print(json.dumps(record), flush=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--counts", type=int, nargs="+", default=[1000, 2000, 5000])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--scenarios", nargs="+", default=["plain", "paired", "metadata", "multiple"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    measured = run(args.repository.resolve(), args.counts, args.repeats, args.scenarios)
    if args.output:
        args.output.write_text(json.dumps(measured, ensure_ascii=False, indent=2), encoding="utf-8")
