"""目录同步批量查询，并在工作线程执行阻塞操作。"""
import ast
import asyncio
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from module_loader import load_module, ROOT

DBService = load_module('services.db_service').DBService
indexer = load_module('services.metadata_indexer')
storage = load_module('timing.storage')
PARSER_VERSION = load_module('metadata.registry').PARSER_VERSION


def load_routes(namespace):
    # 隔离 ComfyUI 启动副作用，直接执行被测路由函数的原始 AST。
    tree = ast.parse((ROOT / 'routes/files.py').read_text(encoding='utf-8'))
    names = {'normalize_folder_path', 'create_metadata_task', 'schedule_file_metadata',
             'synchronize_folder', '_synchronize_folder_locked', 'api_get_files', 'api_get_image_metadata', 'request_services', 'summary_updates'}
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
    scope = {'asyncio': asyncio, 'os': os, 'path': os.path, 'DBService': DBService,
             'metadata_index_queue': None, 'db_service': None,
             'file_lock': storage.file_lock, 'PARSER_VERSION': PARSER_VERSION,
             'IMAGE_EXTENSIONS': {'.png'}, 'MetadataIndexTask': indexer.MetadataIndexTask,
             'MetadataIndexQueue': indexer.MetadataIndexQueue, 'resolve_folder_path': lambda *args: '.',
             'resolve_file_path': lambda kind,folder,name: os.path.join(namespace.get('get_parent_path',lambda _:'.')(kind),folder,name),
             'resolve_sidecar_path': lambda kind,folder,name: namespace.get('get_info_filename',lambda p:p+'.info')(os.path.join(namespace.get('get_parent_path',lambda _:'.')(kind),folder,name)),
             'directory_scan_service': load_module('services.directory_service').DirectoryScanService(),
             'directory_sync_lock': load_module('services.directory_service').directory_sync_lock, **namespace}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(ROOT / 'routes/files.py'), 'exec'), scope)
    return scope


class DirectoryPerformanceTests(unittest.TestCase):
    def test_large_folder_queries_summary_twice_without_per_file_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = DBService(str(root / 'test.db'))
            files = []
            for i in range(80):
                file = root / f'{i}.png'
                file.write_bytes(b'fixture')
                stat = file.stat()
                files.append({'type': 'file', 'name': file.name, 'mtime': stat.st_mtime,
                              'bytes': stat.st_size, 'created_at': stat.st_ctime})
                db.upsert_file(file.name, '', 'outputs', stat.st_size, stat.st_ctime, stat.st_mtime, 'hash',
                               {'parser_version': PARSER_VERSION, 'positive_prompt': 'text' * 5000}, ['kept'])
            routes = load_routes({'get_target_folder_files': lambda *a, **kw: files,
                                  'get_parent_path': lambda _: directory,
                                  'get_info_filename': lambda p: p + '.info'})
            with patch.object(db, 'get_files_in_folder', wraps=db.get_files_in_folder) as folder_reads, \
                    patch.object(db, 'get_file', wraps=db.get_file) as file_reads:
                result = routes['synchronize_folder']('', 'outputs', database=db)
            self.assertEqual(folder_reads.call_count, 2)
            self.assertEqual(file_reads.call_count, 0)
            self.assertEqual(len(result), 80)
            self.assertTrue(all('formatted_info' not in item for item in result))
            self.assertEqual(result[0]['tags'], ['kept'])
            self.assertIsNone(db.get_file('missing.png', '', 'outputs'))

    def test_routes_keep_blocking_work_off_event_loop(self):
        main_thread = threading.get_ident()
        def scan(*args, **kwargs):
            self.assertNotEqual(threading.get_ident(), main_thread)
            return []
        def metadata(request):
            self.assertNotEqual(threading.get_ident(), main_thread)
            return {'complete': True}
        routes = load_routes({'get_parent_path': lambda _: '.', 'get_image_metadata': metadata,
                              'web': SimpleNamespace(json_response=lambda result: result)})
        routes['synchronize_folder'] = scan
        request = SimpleNamespace(query={})
        self.assertEqual(asyncio.run(routes['api_get_files'](request)), {'files': []})
        self.assertEqual(asyncio.run(routes['api_get_image_metadata'](request)), {'complete': True})
