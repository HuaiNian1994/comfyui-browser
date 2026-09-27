"""持久化计时及可恢复的嵌入任务；磁盘文件版本参与每次写入。"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from .containers import fingerprint, load_bytes, read_payload, write_payload
from .recording import summary

logger = logging.getLogger(__name__)
_locks = [threading.RLock() for _ in range(128)]
store = None
pending_outputs = {}
pending_lock = threading.Lock()


def _file_lock_slot(path):
    key = os.path.normcase(os.path.realpath(path)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:2], "big") % len(_locks)


def file_lock(path):
    return _locks[_file_lock_slot(path)]


@contextmanager
def file_locks(paths):
    """多文件操作按去重后的锁槽顺序获取，所有调用者保持同一锁顺序。"""
    slots = sorted({_file_lock_slot(path) for path in paths})
    acquired = []
    try:
        for slot in slots:
            _locks[slot].acquire()
            acquired.append(slot)
        yield
    finally:
        for slot in reversed(acquired):
            _locks[slot].release()


class TimingStore:
    def __init__(self, db_path, on_written=None, start_worker=True):
        self.db_path = str(db_path)
        self.on_written = on_written
        self.wake = threading.Event()
        with self.connect() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS timing_tasks (
                    task_id TEXT PRIMARY KEY, payload TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS timing_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                    path TEXT NOT NULL, identity TEXT NOT NULL, payload TEXT NOT NULL,
                    state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, error TEXT,
                    UNIQUE(task_id, path));
                CREATE INDEX IF NOT EXISTS timing_files_path ON timing_files(path);
            ''')
            columns = {r['name'] for r in conn.execute('PRAGMA table_info(timing_files)')}
            if 'next_attempt' not in columns:
                conn.execute('ALTER TABLE timing_files ADD COLUMN next_attempt REAL NOT NULL DEFAULT 0')
            conn.execute("UPDATE timing_files SET state='pending',attempts=MAX(0,attempts-1),next_attempt=0 WHERE state='writing'")
        if start_worker:
            threading.Thread(target=self._worker, daemon=True, name="browser-timing-writer").start()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def persist(self, record, outputs, embed=True):
        with self.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO timing_tasks VALUES (?, ?, ?)",
                         (record['task_id'], json.dumps(record), time.time()))
            for path, node_id, expected in outputs:
                payload = {**record, "output_node_id": node_id,
                           "output": {"node_id": node_id, "filename": Path(path).name, "original_sha256": expected['sha256']}}
                state = "pending" if embed and Path(path).suffix.lower() in ('.png', '.webp') else "database_only"
                conn.execute("INSERT OR IGNORE INTO timing_files(task_id,path,identity,payload,state) VALUES(?,?,?,?,?)",
                             (record['task_id'], os.path.realpath(path), json.dumps(expected), json.dumps(payload), state))
        self.wake.set()

    def lookup(self, path):
        """数据库回退依赖完整文件身份，拒绝同名替换或内容变更。"""
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM timing_files WHERE path=? ORDER BY id DESC LIMIT 4", (os.path.realpath(path),)).fetchall()
        if not rows:
            return None, False
        identity = fingerprint(path)
        for row in rows:
            if json.loads(row['identity']) == identity:
                return summary(json.loads(row['payload']), 'database'), row['state'] in ('pending', 'writing')
        return None, False

    def process_one(self):
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute("SELECT * FROM timing_files WHERE state='pending' AND attempts < 5 AND next_attempt<=? ORDER BY id LIMIT 1", (time.time(),)).fetchone()
            if not row:
                return False
            conn.execute("UPDATE timing_files SET state='writing', attempts=attempts+1 WHERE id=?", (row['id'],))
        start = time.perf_counter()
        state, error = 'complete', None
        identity = json.loads(row['identity'])
        payload = json.loads(row['payload'])
        try:
            with file_lock(row['path']):
                current = fingerprint(row['path'])
                # 原子替换成功但数据库提交前退出时，可识别已写入的同一记录。
                if current != identity:
                    if read_payload(load_bytes(row['path'])) != payload:
                        raise ValueError('file_changed')
                    identity = current
                else:
                    existing = read_payload(load_bytes(row['path']))
                    if existing and existing.get('task_id') != payload['task_id']:
                        raise ValueError('existing_task_timing')
                    identity = write_payload(row['path'], payload, identity)
                if self.on_written:
                    self.on_written(row['path'])
        except OSError as exc:
            error = type(exc).__name__
            state = 'pending' if row['attempts'] + 1 < 5 and not isinstance(exc, FileNotFoundError) else 'failed'
        except Exception as exc:
            error = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            state = 'failed'
        with self.connect() as conn:
            retry_at = time.time() + 2 ** (row['attempts'] + 1) if state == 'pending' else 0
            conn.execute("UPDATE timing_files SET state=?,error=?,identity=?,next_attempt=? WHERE id=?", (state, error, json.dumps(identity), retry_at, row['id']))
        logger.info("生成计时嵌入 file=%s state=%s elapsed_ms=%.2f reason=%s", Path(row['path']).name, state, (time.perf_counter()-start)*1000, error)
        return True

    def retry_file(self, path):
        """用户刷新后复用原记录；真正写入前仍验证完整文件身份。"""
        with self.connect() as conn:
            conn.execute("UPDATE timing_files SET state='pending',attempts=0,next_attempt=0 WHERE path=? AND state='failed' AND error IN ('PermissionError','OSError')",
                         (os.path.realpath(path),))
        self.wake.set()

    def _worker(self):
        while True:
            try:
                if self.process_one():
                    continue
            except Exception:
                logger.exception("生成计时后台写入异常")
            self.wake.wait(2)
            self.wake.clear()


def read_summary(path):
    """嵌入字段优先，损坏的耗时块不影响图片执行图的解析。"""
    try:
        if Path(path).suffix.lower() in ('.png', '.webp'):
            result = summary(read_payload(load_bytes(path)))
            if result:
                return result, False
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        pass
    if store:
        try:
            value, pending = store.lookup(path)
            if value or pending:
                return value, pending
        except OSError:
            pass
    with pending_lock:
        identity = pending_outputs.get(os.path.realpath(path))
    if identity:
        try:
            return None, fingerprint(path) == identity[1]
        except OSError:
            pass
    return None, False
