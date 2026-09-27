"""单工作线程元数据队列，可见优先且每四项前台任务让出一项后台任务。"""
from __future__ import annotations
import logging
import os
import threading
import time
from dataclasses import dataclass
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
    tags: object = None
    record_id: object = None
    mtime_ns: object = None
    parser_version: int = PARSER_VERSION
    index_generation: object = None

class MetadataIndexQueue:
    def __init__(self,db_service,metadata_extractor):
        self.db_service = db_service
        self.metadata_extractor = metadata_extractor
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.states = {}
        self.latest = {}
        self.outcomes = {}
        self.pending = {}
        self.sessions = {}
        self.stopping = False
        self.active = 0
        self.front_streak = 0
        worker = threading.Thread(target=self._worker,daemon=True,name='browser-metadata')
        self.workers = [worker]
        worker.start()

    @staticmethod
    def _identity(task):
        return task.folder_type,task.folder_path,task.filename

    def _task_key(self,task):
        return (*self._identity(task),task.record_id,task.mtime_ns or task.mtime,task.bytes_size,task.parser_version,task.index_generation)

    def status(self,task):
        with self.lock:
            return self.states.get(self._task_key(task))

    def outcome(self,task):
        with self.lock:
            return self.outcomes.get(self._task_key(task))

    def update_visible(self,session_id,tasks):
        with self.condition:
            now = time.monotonic()
            self.sessions = {key:value for key,value in self.sessions.items() if value[0]>now}
            if session_id:
                self.sessions[session_id] = (now+15,{self._task_key(task) for task in tasks})
            self.condition.notify()

    @staticmethod
    def _newer(candidate,reference):
        """记录自增身份与索引代次组成单调顺序，时间戳仅表示内容版本。"""
        if candidate[3] is not None and reference[3] is None:
            return True
        if candidate[3] is not None and reference[3] is not None and candidate[3]!=reference[3]:
            return candidate[3]>reference[3]
        if candidate[7] is not None and reference[7] is None:
            return True
        if candidate[7] is not None and reference[7] is not None:
            return candidate[7]>reference[7]
        return False

    def forget_folder(self,folder_type,folder_path,valid_tasks,observed_tasks=None):
        valid = {self._task_key(task) for task in valid_tasks}
        observed = {self._identity(task):self._task_key(task) for task in (observed_tasks or [])}
        observed.update({self._identity(task):self._task_key(task) for task in valid_tasks})
        def obsolete(key):
            reference = observed.get(key[:3])
            return key[:2]==(folder_type,folder_path) and key not in valid and reference is not None and not self._newer(key,reference)
        with self.condition:
            for key in list(self.states):
                if obsolete(key):
                    self.states.pop(key,None)
                    self.pending.pop(key,None)
                    self.outcomes.pop(key,None)
            for identity,key in list(self.latest.items()):
                if obsolete(key):
                    self.latest.pop(identity,None)
            self.condition.notify_all()

    def enqueue(self,task,force=False,priority=False):
        key = self._task_key(task)
        with self.condition:
            if self.stopping:
                return False
            previous = self.latest.get(self._identity(task))
            if previous and self._newer(previous,key):
                return False
            if previous and previous[3]==key[3] and previous[7] is not None and previous[7]==key[7] and previous[4:6]!=key[4:6]:
                return False
            if self.states.get(key) in {'waiting','processing'}:
                if priority and key in self.pending:
                    self.pending[key] = (task,True)
                return False
            if self.states.get(key) in {'complete','failed'} and not force:
                return False
            identity = self._identity(task)
            previous = self.latest.get(identity)
            if previous and previous != key:
                self.states.pop(previous,None)
                self.pending.pop(previous,None)
            self.latest[identity] = key
            self.outcomes.pop(key,None)
            self.states[key] = 'waiting'
            self.pending[key] = (task,priority)
            self.condition.notify()
            return True

    @staticmethod
    def _matches_file(task):
        try:
            stat = os.stat(task.file_path)
            return stat.st_size==task.bytes_size and stat.st_mtime==task.mtime and (task.mtime_ns is None or stat.st_mtime_ns==task.mtime_ns)
        except OSError:
            return False

    def _take(self):
        now = time.monotonic()
        self.sessions = {key:value for key,value in self.sessions.items() if value[0]>now}
        visible = set().union(*(value[1] for value in self.sessions.values())) if self.sessions else set()
        foreground = [key for key,(_,priority) in self.pending.items() if priority or key in visible]
        background = [key for key in self.pending if key not in visible and not self.pending[key][1]]
        if foreground and (self.front_streak<4 or not background):
            key = foreground[0]
            self.front_streak += 1
        else:
            key = background[0]
            self.front_streak = 0
        task,_ = self.pending.pop(key)
        self.states[key] = 'processing'
        self.active += 1
        return key,task

    def _worker(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda:self.stopping or bool(self.pending))
                if self.stopping:
                    return
                key,task = self._take()
            state = None
            try:
                with file_lock(task.file_path):
                    valid = self._matches_file(task)
                if valid:
                    try:
                        info = self.metadata_extractor(task.file_path)
                        info.setdefault('parser_version',task.parser_version)
                        info['index_status'] = 'complete'
                        state = 'complete'
                    except Exception as exc:
                        info = {'parser_version':task.parser_version,'index_status':'failed','parse_status':'failed','error_code':type(exc).__name__,'has_metadata':False}
                        state = 'failed'
                    # 文件锁在队列锁外取得；数据库条件负责最后的身份和代次核验。
                    with file_lock(task.file_path):
                        with self.lock:
                            current = self.latest.get(self._identity(task))==key
                        if not current or not self._matches_file(task) or not self.db_service.update_metadata_if_current(task,info):
                            state = None
            except Exception as exc:
                logger.warning('元数据提交失败 filename=%s error=%s',task.filename,type(exc).__name__)
                state = 'failed'
            finally:
                with self.condition:
                    self.outcomes[key] = state or 'superseded'
                    while len(self.outcomes)>10000:
                        self.outcomes.pop(next(iter(self.outcomes)))
                    if self.latest.get(self._identity(task))==key:
                        if state:
                            self.states[key] = state
                        else:
                            self.states.pop(key,None)
                            self.latest.pop(self._identity(task),None)
                    self.active -= 1
                    self.condition.notify_all()

    def wait_until_idle(self,timeout=None):
        with self.condition:
            return self.condition.wait_for(lambda:not self.pending and self.active==0,timeout)

    def shutdown(self):
        with self.condition:
            self.stopping = True
            self.pending.clear()
            self.condition.notify_all()
        for worker in self.workers:
            worker.join()
        with self.condition:
            self.states.clear()
            self.latest.clear()
            self.outcomes.clear()
            self.sessions.clear()
