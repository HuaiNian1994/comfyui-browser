"""目录扫描合并：两个线程，共享同目录正在执行的扫描。"""
import asyncio
import threading
import os
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor

# 同目录同步覆盖扫描、数据库提交和排队，调用者取得锁时尚未持有数据库或队列锁。
_sync_guard = threading.Lock()
_sync_locks = {}


@contextmanager
def directory_sync_lock(database,folder_type,folder_path):
    database_key = os.path.normcase(os.path.realpath(database.db_path)) if database.db_path!=':memory:' else id(database)
    key = (database_key,folder_type,os.path.normcase(os.path.normpath(folder_path)))
    with _sync_guard:
        entry = _sync_locks.setdefault(key,[threading.RLock(),0])
        entry[1] += 1
    try:
        with entry[0]:
            yield
    finally:
        with _sync_guard:
            entry[1] -= 1
            if entry[1]==0:
                _sync_locks.pop(key,None)


class DirectoryScanService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2,thread_name_prefix='browser-directory')
        self.lock = threading.RLock()
        self.inflight = {}

    def _done(self,key,entry):
        with self.lock:
            if entry[1]==0 and self.inflight.get(key) is entry:
                self.inflight.pop(key,None)

    async def scan(self,key,callback):
        with self.lock:
            entry = self.inflight.get(key)
            if entry is None or entry[0].done():
                entry = [self.executor.submit(callback),0]
                self.inflight[key] = entry
            entry[1] += 1
        entry[0].add_done_callback(lambda future:self._done(key,entry))
        wrapper = asyncio.wrap_future(entry[0])
        wrapper.add_done_callback(lambda future: future.exception() if not future.cancelled() else None)
        try:
            return await asyncio.shield(wrapper)
        finally:
            with self.lock:
                entry[1] -= 1
                if entry[1]==0:
                    entry[0].cancel()
                    if entry[0].done() and self.inflight.get(key) is entry:
                        self.inflight.pop(key,None)

    def shutdown(self):
        self.executor.shutdown(wait=True,cancel_futures=True)
