"""批量索引、摘要轮询和扫描生命周期回归。"""
import asyncio
import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from test_directory_performance import load_routes
from module_loader import load_module

DBService = load_module('services.db_service').DBService
DirectoryScanService = load_module('services.directory_service').DirectoryScanService
MetadataIndexQueue = load_module('services.metadata_indexer').MetadataIndexQueue
ReindexService = load_module('services.reindex_service').ReindexService
PARSER_VERSION = load_module('metadata.registry').PARSER_VERSION


class FileServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.file = self.root/'image.png'
        self.file.write_bytes(b'image')
        self.db = DBService(str(self.root/'index.db'))
        self.routes = load_routes({'get_target_folder_files':self.files,'get_parent_path':lambda _:str(self.root),
                                  'get_info_filename':lambda value:value+'.info','json':json})
        self.addCleanup(self.routes['directory_scan_service'].shutdown)

    def files(self,*args,**kwargs):
        stat = self.file.stat()
        return [dict(type='file',name=self.file.name,bytes=stat.st_size,mtime=stat.st_mtime,created_at=stat.st_ctime)]

    def scan(self,queue=None,reindex=False):
        return self.routes['synchronize_folder']('','outputs',database=self.db,metadata_queue=queue,reindex=reindex)

    def queue(self,extractor):
        queue = MetadataIndexQueue(self.db,extractor)
        self.addCleanup(queue.shutdown)
        return queue

    def test_summary_poll_reads_only_database_and_reports_stale(self):
        row = self.scan()[0]
        item = {key:row[key] for key in ('name','folder_path','file_version','index_generation')}
        with patch('os.stat',side_effect=AssertionError('摘要轮询不可读文件')),patch('builtins.open',side_effect=AssertionError('摘要轮询不可读文件')):
            result = self.routes['summary_updates']({'files':[item],'visible_files':[item],'session_id':'s'},self.db,None)
        self.assertEqual(result['files'][0]['status'],'waiting')
        item['index_generation'] += 1
        result = self.routes['summary_updates']({'files':[item]},self.db,None)
        self.assertEqual(result['files'][0]['status'],'stale')
        with self.assertRaises(ValueError):
            self.routes['summary_updates']({'files':[item]*201},self.db,None)

    def test_content_change_preserves_user_tags_and_notes(self):
        (self.root/'image.png.info').write_text(json.dumps({'tags':['sidecar'],'notes':'备注'}),encoding='utf-8')
        self.scan()
        self.db.update_file_tags('image.png','','outputs',['用户修改'])
        self.db.update_file_notes('image.png','','outputs','用户备注')
        self.file.write_bytes(b'changed image')
        row = self.scan()[0]
        self.assertEqual(row['tags'],['用户修改'])
        self.assertEqual(row['notes'],'用户备注')
        self.assertNotIn('formatted_info',row)
        self.assertEqual(row['file_version'],f'{self.file.stat().st_mtime_ns}:{self.file.stat().st_size}')

    def test_failed_parse_survives_queue_restart_without_retry(self):
        calls=[]
        def fail(_):
            calls.append(1)
            raise ValueError('bad image')
        queue=self.queue(fail)
        self.scan(queue)
        self.assertTrue(queue.wait_until_idle(2))
        queue.shutdown()
        replacement=self.queue(fail)
        row=self.scan(replacement)[0]
        self.assertEqual(row['index_status'],'failed')
        self.assertEqual(calls,[1])

    def test_stale_scan_cannot_overwrite_timing_or_rebuild(self):
        self.scan()
        old=self.db.get_file('image.png','','outputs')
        item=dict(name='image.png',bytes=10,created_at=old['created_at'],mtime=old['mtime']+1,mtime_ns=old['mtime_ns']+1,hash='old scan')
        self.db.bump_generation('','outputs')
        self.db.sync_identities('','outputs',[(item,old)])
        latest=self.db.get_file('image.png','','outputs')
        self.assertEqual(latest['bytes'],old['bytes'])
        self.assertEqual(latest['index_generation'],old['index_generation']+1)

    def test_enumeration_failure_preserves_records(self):
        self.scan()
        self.routes['get_target_folder_files']=lambda *args,**kwargs:(_ for _ in ()).throw(OSError('unreadable'))
        with self.assertRaises(OSError):
            self.scan()
        self.assertIsNotNone(self.db.get_file('image.png','','outputs'))

    def test_reindex_waits_for_terminal_and_reuses_scope(self):
        entered,release=threading.Event(),threading.Event()
        def extract(_):
            entered.set()
            release.wait(3)
            return {'parser_version':PARSER_VERSION,'models':['ok']}
        queue=self.queue(extract)
        service=ReindexService()
        self.addCleanup(service.shutdown)
        scanner=lambda folder,force:self.scan(queue,reindex=force)
        scope=('outputs',('',),id(self.db))
        job=service.submit(scope,lambda:[''],scanner,self.db,queue)
        self.assertTrue(entered.wait(2))
        self.assertEqual(service.submit(scope,lambda:[''],scanner,self.db,queue),job)
        self.assertEqual(service.get(job)['status'],'running')
        release.set()
        deadline=time.monotonic()+3
        while service.get(job)['status']=='running' and time.monotonic()<deadline:
            time.sleep(.02)
        result=service.get(job)
        self.assertEqual(result['status'],'complete')
        self.assertEqual(result['success_count'],1)
        service.jobs[job]['_finished']=time.monotonic()-3601
        self.assertIsNone(service.get(job))
        self.assertNotIn(scope,service.scopes)

    def test_reindex_deleted_file_finishes_as_superseded(self):
        entered,release=threading.Event(),threading.Event()
        def extract(_):
            entered.set();release.wait(3)
            return {'parser_version':PARSER_VERSION}
        queue=self.queue(extract)
        service=ReindexService()
        self.addCleanup(service.shutdown)
        job=service.submit(('outputs',('',)),lambda:[''],lambda folder,force:self.scan(queue,True),self.db,queue)
        self.assertTrue(entered.wait(2))
        self.file.unlink();release.set()
        deadline=time.monotonic()+3
        while service.get(job)['status']=='running' and time.monotonic()<deadline:
            time.sleep(.02)
        self.assertEqual(service.get(job)['status'],'complete')
        self.assertEqual(service.get(job)['superseded_count'],1)


    def test_paused_directory_scan_serializes_rebuild_before_new_generation(self):
        self.scan()
        queue=self.queue(lambda _: {'parser_version':PARSER_VERSION})
        service=ReindexService()
        self.addCleanup(service.shutdown)
        paused,release,bumped=threading.Event(),threading.Event(),threading.Event()
        original_read=self.db.get_files_in_folder
        original_bump=self.db.bump_generation
        reads=[]
        failures=[]
        def read(*args,**kwargs):
            records=original_read(*args,**kwargs)
            if threading.current_thread().name=='ordinary-scan':
                reads.append(1)
                if len(reads)==2:
                    paused.set()
                    release.wait(3)
            return records
        def bump(*args,**kwargs):
            bumped.set()
            return original_bump(*args,**kwargs)
        def scan():
            try:
                self.scan(queue)
            except Exception as exc:
                failures.append(exc)
        with patch.object(self.db,'get_files_in_folder',side_effect=read),patch.object(self.db,'bump_generation',side_effect=bump):
            thread=threading.Thread(target=scan,name='ordinary-scan')
            thread.start()
            try:
                self.assertTrue(paused.wait(2))
                job=service.submit(('outputs',('',)),lambda:[''],lambda folder,force:self.scan(queue,True),self.db,queue)
                self.assertFalse(bumped.wait(.1))
            finally:
                release.set()
                thread.join(3)
            self.assertFalse(thread.is_alive())
            deadline=time.monotonic()+3
            while service.get(job)['status'] in {'queued','running'} and time.monotonic()<deadline:
                time.sleep(.02)
        self.assertEqual(failures,[])
        self.assertTrue(bumped.is_set())
        self.assertEqual(service.get(job)['status'],'complete')
        self.assertEqual(service.get(job)['success_count'],1)
        self.assertEqual(self.db.get_file('image.png','','outputs')['index_generation'],2)

    def test_queue_rejects_old_generation_and_preserves_newer_task_on_cleanup(self):
        self.scan()
        old=self.db.get_file('image.png','','outputs')
        make_task=self.routes['create_metadata_task']
        old_task=make_task(old,str(self.file),'','outputs')
        self.db.bump_generation('','outputs')
        current=self.db.get_file('image.png','','outputs')
        new_task=make_task(current,str(self.file),'','outputs')
        entered,release=threading.Event(),threading.Event()
        def extract(_):
            entered.set();release.wait(3)
            return {'parser_version':PARSER_VERSION}
        queue=self.queue(extract)
        try:
            self.assertTrue(queue.enqueue(new_task))
            self.assertTrue(entered.wait(2))
            self.assertFalse(queue.enqueue(old_task))
            queue.forget_folder('outputs','',[old_task],observed_tasks=[old_task])
            self.assertEqual(queue.status(new_task),'processing')
            release.set()
            self.assertTrue(queue.wait_until_idle(2))
            self.assertEqual(queue.status(new_task),'complete')
        finally:
            release.set()

    def test_reindex_database_write_failure_reaches_failed_terminal_count(self):
        queue=self.queue(lambda _: {'parser_version':PARSER_VERSION})
        service=ReindexService()
        self.addCleanup(service.shutdown)
        with patch.object(self.db,'update_metadata_if_current',side_effect=sqlite3.OperationalError('write failed')):
            job=service.submit(('outputs',('',)),lambda:[''],lambda folder,force:self.scan(queue,True),self.db,queue)
            deadline=time.monotonic()+3
            while service.get(job)['status'] in {'queued','running'} and time.monotonic()<deadline:
                time.sleep(.02)
        self.assertEqual(service.get(job)['status'],'complete')
        self.assertEqual(service.get(job)['failed_count'],1)


    def test_summary_snapshot_waits_when_worker_completes_after_batch_read(self):
        row=self.scan()[0]
        item={key:row[key] for key in ('name','folder_path','file_version','index_generation')}
        entered,release=threading.Event(),threading.Event()
        def extract(_):
            entered.set();release.wait(3)
            return {'parser_version':PARSER_VERSION,'models':['finished']}
        queue=self.queue(extract)
        self.scan(queue)
        self.assertTrue(entered.wait(2))
        original=self.db.get_summary_batch
        def snapshot(*args,**kwargs):
            result=original(*args,**kwargs)
            self.assertEqual(result[('','image.png')]['summary'],{})
            release.set()
            self.assertTrue(queue.wait_until_idle(2))
            return result
        try:
            with patch.object(self.db,'get_summary_batch',side_effect=snapshot) as batches,patch.object(self.db,'get_file',side_effect=AssertionError('保持批量查询')):
                result=self.routes['summary_updates']({'files':[item]},self.db,queue)['files'][0]
            self.assertEqual(batches.call_count,1)
            self.assertEqual(result['status'],'waiting')
            self.assertEqual(result['summary'],{})
            fresh=self.routes['summary_updates']({'files':[item]},self.db,queue)['files'][0]
            self.assertEqual(fresh['status'],'complete')
            self.assertEqual(fresh['summary']['models'],['finished'])
        finally:
            release.set()

    def test_directory_snapshot_waits_when_worker_completes_after_batch_read(self):
        self.scan()
        entered,release=threading.Event(),threading.Event()
        def extract(_):
            entered.set();release.wait(3)
            return {'parser_version':PARSER_VERSION,'models':['finished']}
        queue=self.queue(extract)
        self.scan(queue)
        self.assertTrue(entered.wait(2))
        original=self.db.get_files_in_folder
        reads=[]
        def snapshot(*args,**kwargs):
            result=original(*args,**kwargs)
            reads.append(1)
            if len(reads)==2:
                self.assertEqual(result['image.png']['summary'],{})
                release.set()
                self.assertTrue(queue.wait_until_idle(2))
            return result
        try:
            with patch.object(self.db,'get_files_in_folder',side_effect=snapshot),patch.object(self.db,'get_file',side_effect=AssertionError('保持批量查询')):
                result=self.scan(queue)[0]
            self.assertEqual(len(reads),2)
            self.assertEqual(result['index_status'],'waiting')
            self.assertTrue(result['metadata_pending'])
            self.assertEqual(result['summary'],{})
            fresh=self.scan(queue)[0]
            self.assertEqual(fresh['index_status'],'complete')
            self.assertEqual(fresh['summary']['models'],['finished'])
        finally:
            release.set()


class ScanLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_waiter_keeps_shared_scan_and_cleans_finished_entries(self):
        service=DirectoryScanService()
        entered,release=threading.Event(),threading.Event()
        calls=[]
        def scan():
            calls.append(1);entered.set();release.wait(3);return ['ok']
        try:
            first=asyncio.create_task(service.scan('same',scan))
            second=asyncio.create_task(service.scan('same',scan))
            await asyncio.to_thread(entered.wait,1)
            first.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await first
            release.set()
            self.assertEqual(await second,['ok'])
            self.assertEqual(calls,[1])
            self.assertEqual(service.inflight,{})
        finally:
            release.set();service.shutdown()

    async def test_unstarted_scan_is_cancelled_when_last_waiter_leaves(self):
        service=DirectoryScanService()
        release=threading.Event()
        called=[]
        try:
            blockers=[asyncio.create_task(service.scan(str(i),lambda:release.wait(3))) for i in range(2)]
            await asyncio.sleep(.03)
            queued=asyncio.create_task(service.scan('queued',lambda:called.append(1)))
            await asyncio.sleep(.03)
            queued.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await queued
            release.set()
            await asyncio.gather(*blockers)
            self.assertEqual(called,[])
            self.assertEqual(service.inflight,{})
        finally:
            release.set();service.shutdown()

class DatabaseMigrationTests(unittest.TestCase):
    def test_migration_removes_non_media_from_all_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = str(Path(directory) / 'index.db')
            database = DBService(filename)
            names = ['image.PNG', 'video.MP4', 'parameter-check.json', 'page.HTML', 'notes.txt', 'image.png.info', 'README']
            with database.connection() as conn:
                for folder_type in ('outputs', 'collections', 'sources'):
                    conn.executemany('INSERT INTO files(filename,folder_path,folder_type) VALUES(?,?,?)',
                                     [(name, 'unvisited', folder_type) for name in names])
            for _ in range(2):
                database = DBService(filename)
                with database.connection() as conn:
                    rows = conn.execute('SELECT filename FROM files').fetchall()
                self.assertEqual(sorted(row['filename'] for row in rows), sorted(['image.PNG', 'video.MP4'] * 3))

    def test_write_entries_only_store_media(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DBService(str(Path(directory) / 'index.db'))
            names = ['image.PNG', 'video.MP4', 'workflow.json', 'page.html', 'notes.txt', 'image.png.info']
            for name in names:
                database.upsert_file(name, 'direct', 'outputs', 1, 1, 1, name, {})
            changes = [(dict(name=name, bytes=1, created_at=1, mtime=1, mtime_ns=1, hash=name), None) for name in names]
            database.sync_identities('batch', 'outputs', changes)
            for folder in ('direct', 'batch'):
                self.assertEqual(set(database.get_files_in_folder(folder, 'outputs')), {'image.PNG', 'video.MP4'})

    def test_repeatable_migration_derives_summary_without_reparse(self):
        with tempfile.TemporaryDirectory() as directory:
            filename=str(Path(directory)/'old.db')
            conn=sqlite3.connect(filename)
            conn.execute('CREATE TABLE files(id INTEGER PRIMARY KEY AUTOINCREMENT,filename TEXT,folder_path TEXT,folder_type TEXT,bytes INTEGER,created_at REAL,mtime REAL,hash TEXT,formatted_info TEXT,tags TEXT,UNIQUE(filename,folder_path,folder_type))')
            conn.execute('INSERT INTO files(filename,folder_path,folder_type,formatted_info,tags) VALUES(?,?,?,?,?)',('old.png','','outputs',json.dumps({'models':['kept'],'positive_prompt':'large'*1000,'parser_version':PARSER_VERSION}),'["tag"]'))
            conn.commit();conn.close()
            DBService(filename)
            database=DBService(filename)
            row=database.get_files_in_folder('','outputs')['old.png']
            self.assertNotIn('formatted_info',row)
            self.assertEqual(row['summary']['models'],['kept'])
            self.assertNotIn('positive_prompt',row['summary'])
            self.assertEqual(database.get_file('old.png','','outputs')['formatted_info']['positive_prompt'],'large'*1000)

    def test_identity_changes_share_connection_and_commit_per_hundred(self):
        with tempfile.TemporaryDirectory() as directory:
            database=DBService(str(Path(directory)/'index.db'))
            commits=[]
            class Connection(sqlite3.Connection):
                def commit(self):
                    commits.append(1)
                    return super().commit()
            def connect():
                connection=sqlite3.connect(database.db_path,factory=Connection)
                connection.row_factory=sqlite3.Row
                return connection
            changes=[(dict(name=f'{i}.png',bytes=1,created_at=1,mtime=1,mtime_ns=1,hash=str(i)),None) for i in range(205)]
            with patch.object(database,'_get_connection',side_effect=connect) as opened:
                database.sync_identities('','outputs',changes)
            self.assertEqual(opened.call_count,1)
            self.assertEqual(len(commits),3)
            self.assertEqual(len(database.get_files_in_folder('','outputs')),205)


class QueueFairnessTests(unittest.TestCase):
    def test_four_foreground_tasks_allow_one_background_task(self):
        with tempfile.TemporaryDirectory() as directory:
            entered,release=threading.Event(),threading.Event()
            order=[]
            def extract(filename):
                name=Path(filename).stem
                order.append(name)
                if name=='block':
                    entered.set();release.wait(3)
                return {'parser_version':PARSER_VERSION}
            database=DBService(str(Path(directory)/'index.db'))
            queue=MetadataIndexQueue(database,extract)
            def enqueue(name,priority=False):
                file=Path(directory)/(name+'.png');file.write_bytes(b'x');stat=file.stat()
                database.upsert_file(file.name,'','outputs',1,stat.st_ctime,stat.st_mtime,name,{},mtime_ns=stat.st_mtime_ns)
                record=database.get_file(file.name,'','outputs')
                task=load_module('services.metadata_indexer').MetadataIndexTask(file.name,'','outputs',str(file),1,stat.st_ctime,stat.st_mtime,name,record_id=record['id'],mtime_ns=stat.st_mtime_ns,index_generation=record['index_generation'])
                queue.enqueue(task,priority=priority)
                return task
            try:
                enqueue('block');self.assertTrue(entered.wait(2))
                enqueue('back1');enqueue('back2')
                for i in range(6):
                    enqueue(f'front{i}',priority=True)
                release.set();self.assertTrue(queue.wait_until_idle(3))
                self.assertEqual(order[1:6],['front0','front1','front2','front3','back1'])
                self.assertEqual(order[-1],'back2')
            finally:
                release.set();queue.shutdown()
