"""后台解析图片，并按文件版本条件提交结果。"""
from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from queue import Queue
from typing import Callable, Optional

from .db_service import DBService
from ..metadata.registry import PARSER_VERSION
from ..timing.storage import file_lock

logger = logging.getLogger(__name__)


@dataclass
class MetadataIndexTask:
    filename: str
    folder_path: str
    folder_type: str
    file_path: str
    bytes_size: int
    created_at: float
    mtime: float
    hash_val: str
    tags: Optional[list[str]] = None
    record_id: Optional[int] = None
    mtime_ns: Optional[int] = None
    parser_version: int = PARSER_VERSION


class MetadataIndexQueue:
    def __init__(self, db_service: DBService, metadata_extractor: Callable[[str], dict], max_workers: int = 1):
        self.db_service = db_service
        self.metadata_extractor = metadata_extractor
        self.task_queue = Queue()
        self.lock = threading.RLock()
        self.states = {}
        self.latest = {}
        self.generation = 0
        self.workers = []
        for _ in range(max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)

    @staticmethod
    def _identity(task):
        return task.folder_type, task.folder_path, task.filename

    def _task_key(self, task):
        return (*self._identity(task), task.record_id, task.mtime_ns or task.mtime, task.bytes_size, task.parser_version)

    def status(self, task):
        with self.lock:
            return self.states.get(self._task_key(task))

    def enqueue(self, task, force=False):
        key = self._task_key(task)
        with self.lock:
            if self.states.get(key) in {"waiting", "processing"}:
                return False
            if self.states.get(key) in {"complete", "failed"} and not force:
                return False
            self.generation += 1
            generation = self.generation
            self.latest[self._identity(task)] = generation
            self.states[key] = "waiting"
            self.task_queue.put((task, generation))
            return True

    @staticmethod
    def _matches_file(task):
        try:
            stat = os.stat(task.file_path)
            return stat.st_size == task.bytes_size and stat.st_mtime == task.mtime and (task.mtime_ns is None or stat.st_mtime_ns == task.mtime_ns)
        except OSError:
            return False

    def _worker(self):
        while True:
            item = self.task_queue.get()
            if item is None:
                self.task_queue.task_done()
                return
            task, generation = item
            key = self._task_key(task)
            try:
                with self.lock:
                    if self.latest.get(self._identity(task)) != generation:
                        self.states.pop(key, None)
                        continue
                    self.states[key] = "processing"
                if not self._matches_file(task):
                    with self.lock:
                        self.states.pop(key, None)
                    continue
                try:
                    info = self.metadata_extractor(task.file_path)
                    info["index_status"] = "complete"
                    status = "complete"
                except Exception as exc:
                    logger.warning("图片元数据解析失败 filename=%s error=%s", task.filename, type(exc).__name__)
                    info = {"parser_version": task.parser_version, "index_status": "failed", "error_code": type(exc).__name__, "has_metadata": False}
                    status = "failed"
                with file_lock(task.file_path), self.lock:
                    if self.latest.get(self._identity(task)) == generation and self._matches_file(task):
                        committed = self.db_service.update_metadata_if_current(task, info)
                        if committed:
                            self.states[key] = status
                        else:
                            self.states.pop(key, None)
                    else:
                        self.states.pop(key, None)
            except Exception as exc:
                with self.lock:
                    self.states[key] = "failed"
                logger.warning("图片元数据提交失败 filename=%s error=%s", task.filename, type(exc).__name__)
            finally:
                self.task_queue.task_done()

    def wait_until_idle(self, timeout=None):
        if timeout is None:
            self.task_queue.join()
            return True
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.task_queue.unfinished_tasks == 0:
                return True
            time.sleep(0.01)
        return False
