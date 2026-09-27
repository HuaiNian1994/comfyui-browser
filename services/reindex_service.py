"""串行重建作业；目录扫描结束后等待本次快照全部进入终态。"""
import threading
import time
import uuid
from .metadata_indexer import MetadataIndexTask
from concurrent.futures import ThreadPoolExecutor

class ReindexService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1,thread_name_prefix='browser-reindex')
        self.lock = threading.Lock()
        self.jobs = {}
        self.scopes = {}
        self.stopping = threading.Event()

    def _prune(self):
        terminal = sorted((job for job in self.jobs.values() if job.get('_finished')),key=lambda job:job['_finished'])
        now = time.monotonic()
        for index,job in enumerate(terminal):
            if now-job['_finished']>3600 or index<len(terminal)-100:
                self.jobs.pop(job['job_id'],None)
                for scope,value in list(self.scopes.items()):
                    if value==job['job_id']:
                        self.scopes.pop(scope,None)

    def get(self,job_id):
        with self.lock:
            self._prune()
            job = self.jobs.get(job_id)
            return {key:value for key,value in job.items() if not key.startswith('_')} if job else None

    def submit(self,scope,folders,scanner,database,queue):
        with self.lock:
            self._prune()
            existing = self.scopes.get(scope)
            if existing and self.jobs[existing]['status'] in {'queued','running'}:
                return existing
            job_id = uuid.uuid4().hex
            job = dict(job_id=job_id,status='queued',scan_complete=False,indexed_folders=0,indexed_files=0,success_count=0,failed_count=0,superseded_count=0)
            self.jobs[job_id] = job
            self.scopes[scope] = job_id
            self.executor.submit(self._run,job,folders,scanner,database,queue,scope[0])
            return job_id

    def _update(self,job,**values):
        with self.lock:
            job.update(values)

    def _run(self,job,folders,scanner,database,queue,folder_type):
        snapshots = []
        try:
            self._update(job,status='running')
            for folder in folders():
                if self.stopping.is_set():
                    return
                rows = scanner(folder,True)
                snapshots.extend((folder,row) for row in rows if row['type']=='file')
                self._update(job,indexed_folders=job['indexed_folders']+1,indexed_files=len(snapshots))
            self._update(job,scan_complete=True)
            pending = snapshots
            success=failed=superseded=0
            while pending and not self.stopping.is_set():
                requests = [{'folder_path':folder,'name':row['name']} for folder,row in pending]
                records = database.get_summary_batch(folder_type,requests)
                waiting = []
                for folder,row in pending:
                    record = records.get((folder,row['name']))
                    if not record or record['file_version']!=row['file_version'] or record['index_generation']!=row['index_generation']:
                        superseded += 1
                    elif self._outcome(queue,record)=='superseded':
                        superseded += 1
                    elif record['summary'].get('parse_status')=='failed' or self._outcome(queue,record)=='failed':
                        failed += 1
                    elif record['summary'].get('parser_version') is not None or row.get('index_status')=='complete':
                        success += 1
                    else:
                        waiting.append((folder,row))
                pending = waiting
                self._update(job,success_count=success,failed_count=failed,superseded_count=superseded)
                if pending:
                    self.stopping.wait(1)
            if not self.stopping.is_set():
                self._update(job,status='complete',_finished=time.monotonic())
        except Exception as exc:
            self._update(job,status='failed',error=type(exc).__name__,_finished=time.monotonic())

    @staticmethod
    def _outcome(queue,record):
        if not queue:
            return None
        task = MetadataIndexTask(record['filename'],record['folder_path'],record['folder_type'],'',record['bytes'],record['created_at'],record['mtime'],record['hash'],record_id=record['id'],mtime_ns=record['mtime_ns'],index_generation=record['index_generation'])
        return queue.outcome(task)

    def shutdown(self):
        self.stopping.set()
        self.executor.shutdown(wait=True,cancel_futures=True)
