import os
import tempfile
import threading
import unittest
from pathlib import Path
from module_loader import load_module

DBService = load_module('services.db_service').DBService
module = load_module('services.metadata_indexer')
MetadataIndexQueue = module.MetadataIndexQueue
MetadataIndexTask = module.MetadataIndexTask

class MetadataIndexQueueTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.file = Path(self.directory.name) / 'sample.png'
        self.file.write_bytes(b'example')
        self.db = DBService(str(Path(self.directory.name)/'test.db'))
        self.insert_file()
        self.queues = []
        self.addCleanup(self.stop_workers)

    def stop_workers(self):
        for queue in self.queues:
            queue.shutdown()
            self.assertTrue(all(not worker.is_alive() for worker in queue.workers))

    def insert_file(self):
        stat = self.file.stat()
        self.db.upsert_file(self.file.name, '', 'outputs', stat.st_size, stat.st_ctime, stat.st_mtime, 'hash', {}, ['original'])

    def task(self):
        record = self.db.get_file(self.file.name, '', 'outputs')
        return MetadataIndexTask(self.file.name, '', 'outputs', str(self.file), record['bytes'], record['created_at'], record['mtime'], record['hash'], record_id=record['id'], mtime_ns=self.file.stat().st_mtime_ns)

    def create_queue(self, extractor):
        queue = MetadataIndexQueue(self.db, extractor)
        self.queues.append(queue)
        return queue

    def test_background_metadata_preserves_current_tags(self):
        entered, release = threading.Event(), threading.Event()
        def extract(_):
            entered.set(); release.wait(2)
            return {'parser_version': 1, 'models': ['new']}
        queue = self.create_queue(extract)
        queue.enqueue(self.task()); self.assertTrue(entered.wait(1))
        self.db.update_file_tags(self.file.name, '', 'outputs', ['edited'])
        release.set(); self.assertTrue(queue.wait_until_idle(2))
        record = self.db.get_file(self.file.name, '', 'outputs')
        self.assertEqual(record['tags'], ['edited'])
        self.assertEqual(record['formatted_info']['models'], ['new'])

    def test_deleted_record_stays_deleted(self):
        entered, release = threading.Event(), threading.Event()
        def extract(_):
            entered.set(); release.wait(2); return {'parser_version': 1}
        queue = self.create_queue(extract); queue.enqueue(self.task()); self.assertTrue(entered.wait(1))
        self.db.delete_files('', 'outputs', [self.file.name])
        release.set(); self.assertTrue(queue.wait_until_idle(2))
        self.assertEqual(self.db.get_files_in_folder('', 'outputs'), {})

    def test_modified_file_discards_old_result(self):
        entered, release = threading.Event(), threading.Event()
        def extract(_):
            entered.set(); release.wait(2); return {'models': ['stale']}
        queue = self.create_queue(extract); queue.enqueue(self.task()); self.assertTrue(entered.wait(1))
        self.file.write_bytes(b'changed-file'); self.insert_file()
        release.set(); self.assertTrue(queue.wait_until_idle(2))
        self.assertEqual(self.db.get_file(self.file.name, '', 'outputs')['formatted_info'], {})

    def test_recreated_record_rejects_old_identity(self):
        task = self.task()
        self.db.delete_files('', 'outputs', [self.file.name]); self.insert_file()
        self.assertFalse(self.db.update_metadata_if_current(task, {'models': ['stale']}))

    def test_concurrent_enqueue_deduplicates(self):
        entered, release = threading.Event(), threading.Event()
        calls = []
        def extract(_):
            calls.append(1); entered.set(); release.wait(2); return {'parser_version': 1}
        queue = self.create_queue(extract); task = self.task()
        threads = [threading.Thread(target=queue.enqueue, args=(task,)) for _ in range(15)]
        for thread in threads: thread.start()
        self.assertTrue(entered.wait(1))
        for thread in threads: thread.join()
        release.set(); self.assertTrue(queue.wait_until_idle(2))
        self.assertEqual(len(calls), 1)

    def test_failure_requires_explicit_retry(self):
        calls = []
        def extract(_):
            calls.append(1)
            if len(calls) == 1: raise OSError('fixture failure')
            return {'parser_version': 1}
        queue = self.create_queue(extract); task = self.task()
        queue.enqueue(task); self.assertTrue(queue.wait_until_idle(2))
        self.assertEqual(queue.status(task), 'failed')
        self.assertFalse(queue.enqueue(task))
        self.assertTrue(queue.enqueue(task, force=True)); self.assertTrue(queue.wait_until_idle(2))
        self.assertEqual(queue.status(task), 'complete')

    def test_shutdown_waits_for_active_worker_and_releases_queue_resources(self):
        entered, release, closed = threading.Event(), threading.Event(), threading.Event()
        def extract(_):
            entered.set()
            release.wait(2)
            return {'parser_version': 1}
        queue = self.create_queue(extract)
        task = self.task()
        queue.enqueue(task)
        self.assertTrue(entered.wait(1))
        def close():
            queue.shutdown()
            closed.set()
        closer = threading.Thread(target=close)
        closer.start()
        try:
            self.assertFalse(closed.wait(.05))
            release.set()
            self.assertTrue(closed.wait(2))
            self.assertTrue(all(not worker.is_alive() for worker in queue.workers))
            self.assertEqual(queue.pending, {})
            self.assertEqual(queue.states, {})
            self.assertEqual(queue.sessions, {})
            self.assertFalse(queue.enqueue(task, force=True))
        finally:
            release.set()
            closer.join(2)
