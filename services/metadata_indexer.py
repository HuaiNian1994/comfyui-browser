"""异步补齐文件元数据的任务队列"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from queue import Queue
from typing import Callable, List, Optional, Set, Tuple

from .db_service import DBService


@dataclass
class MetadataIndexTask:
    """待补齐元数据的文件任务描述"""
    filename: str
    folder_path: str
    folder_type: str
    file_path: str
    bytes_size: int
    created_at: float
    mtime: float
    hash_val: str
    tags: Optional[List[str]] = None


class MetadataIndexQueue:
    """串行执行的元数据补齐队列，避免阻塞主事件循环。"""

    def __init__(self, db_service: DBService, metadata_extractor: Callable[[str], dict], max_workers: int = 1):
        self.db_service = db_service
        self.metadata_extractor = metadata_extractor
        self.max_workers = max_workers
        self.task_queue: Queue[MetadataIndexTask] = Queue()
        self.scheduled_keys: Set[Tuple[str, str, str, str]] = set()
        self.workers: List[threading.Thread] = []

        for _ in range(max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)

    def _worker(self) -> None:
        while True:
            task = self.task_queue.get()
            if task is None:
                self.task_queue.task_done()
                break

            task_key = self._task_key(task)
            try:
                metadata = self.metadata_extractor(task.file_path)
                self.db_service.upsert_file(
                    filename=task.filename,
                    folder_path=task.folder_path,
                    folder_type=task.folder_type,
                    bytes_size=task.bytes_size,
                    created_at=task.created_at,
                    mtime=task.mtime,
                    hash_val=task.hash_val,
                    formatted_info=metadata,
                    tags=task.tags
                )
            except Exception as exc:  # pragma: no cover - 记录异常但不中断队列
                print(f"[MetadataIndexQueue] Failed to index {task.file_path}: {exc}")
            finally:
                self.scheduled_keys.discard(task_key)
                self.task_queue.task_done()

    def _task_key(self, task: MetadataIndexTask) -> Tuple[str, str, str, str]:
        return task.folder_type, task.folder_path, task.filename, task.hash_val

    def enqueue(self, task: MetadataIndexTask) -> bool:
        """
        将任务加入队列，基于路径+文件名+hash去重。
        返回True表示成功加入，False表示已存在同任务。
        """
        task_key = self._task_key(task)
        if task_key in self.scheduled_keys:
            return False
        self.scheduled_keys.add(task_key)
        self.task_queue.put(task)
        return True

    def wait_until_idle(self, timeout: Optional[float] = None) -> bool:
        """
        等待队列为空。timeout为None时阻塞等待。
        返回True表示完成，False表示超时未完成。
        """
        if timeout is None:
            self.task_queue.join()
            return True

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.task_queue.unfinished_tasks == 0:
                return True
            time.sleep(0.05)
        return False



