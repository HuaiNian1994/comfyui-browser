"""文件索引数据库：轻量摘要、批量身份同步和版本条件提交。"""
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from ..constants import WHITE_EXTENSIONS

SUMMARY_FIELDS = ('width', 'height', 'models', 'loras', 'parser_version', 'parse_status')


def make_summary(info):
    summary = {key: info[key] for key in SUMMARY_FIELDS if key in info}
    if info.get('index_status') == 'failed':
        summary['parse_status'] = 'failed'
    return summary


class DBService:
    def __init__(self, db_path='comfyui_browser.db'):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def connection(self):
        conn = self._get_connection()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self.connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL,
                folder_path TEXT NOT NULL, folder_type TEXT NOT NULL, bytes INTEGER,
                created_at REAL, mtime REAL, hash TEXT, formatted_info TEXT, tags TEXT,
                UNIQUE(filename,folder_path,folder_type))''')
            columns = {row['name'] for row in conn.execute('PRAGMA table_info(files)')}
            for name, definition in [('mtime_ns', 'INTEGER'), ('summary', 'TEXT'),
                                     ('index_generation', 'INTEGER NOT NULL DEFAULT 0'),
                                     ('notes', "TEXT NOT NULL DEFAULT ''"), ('notes_initialized', 'INTEGER NOT NULL DEFAULT 0')]:
                if name not in columns:
                    conn.execute(f'ALTER TABLE files ADD COLUMN {name} {definition}')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_folder ON files(folder_path,folder_type)')
            # 清理所有目录的历史非媒体索引，磁盘文件保持原样。
            media_conditions = ' OR '.join('LOWER(SUBSTR(filename, ?)) = ?' for _ in WHITE_EXTENSIONS)
            media_params = [value for extension in WHITE_EXTENSIONS for value in (-len(extension), extension)]
            conn.execute(f'DELETE FROM files WHERE NOT ({media_conditions})', media_params)

    @staticmethod
    def decode(row):
        if row is None:
            return None
        result = dict(row)
        for key, fallback in [('formatted_info', {}), ('summary', {}), ('tags', [])]:
            if key in result:
                try:
                    result[key] = json.loads(result[key]) if result[key] else fallback
                except (TypeError, ValueError):
                    result[key] = fallback
        if 'mtime_ns' in result:
            result['file_version'] = f"{result['mtime_ns']}:{result['bytes']}"
        return result

    def get_files_in_folder(self, folder_path, folder_type):
        with self.connection() as conn:
            # 旧记录按访问目录补摘要，复用已有解析结果。
            backfilled = 0
            for row in conn.execute('SELECT id,formatted_info FROM files WHERE folder_path=? AND folder_type=? AND summary IS NULL', (folder_path,folder_type)).fetchall():
                try:
                    info = json.loads(row['formatted_info'] or '{}')
                except ValueError:
                    info = {}
                conn.execute('UPDATE files SET summary=? WHERE id=? AND summary IS NULL', (json.dumps(make_summary(info)),row['id']))
                backfilled += 1
                if backfilled % 100 == 0:
                    conn.commit()
            fields = 'id,filename,folder_path,folder_type,bytes,created_at,mtime,mtime_ns,hash,tags,notes,notes_initialized,summary,index_generation'
            return {row['filename']: self.decode(row) for row in conn.execute(f'SELECT {fields} FROM files WHERE folder_path=? AND folder_type=?',(folder_path,folder_type))}

    def get_file(self, filename, folder_path, folder_type):
        with self.connection() as conn:
            return self.decode(conn.execute('SELECT * FROM files WHERE filename=? AND folder_path=? AND folder_type=?',(filename,folder_path,folder_type)).fetchone())

    def get_summary_batch(self, folder_type, items):
        """一个连接内批量仅读取轻量列，不触碰文件系统。"""
        result = {}
        with self.connection() as conn:
            for offset in range(0,len(items),100):
                chunk = items[offset:offset+100]
                if not chunk:
                    continue
                predicates = ' OR '.join('(folder_path=? AND filename=?)' for _ in chunk)
                params = [folder_type]
                for item in chunk:
                    params.extend([item['folder_path'],item['name']])
                for row in conn.execute('SELECT id,filename,folder_path,folder_type,bytes,created_at,mtime,mtime_ns,hash,tags,summary,index_generation FROM files WHERE folder_type=? AND ('+predicates+')',params):
                    result[(row['folder_path'],row['filename'])] = self.decode(row)
        return result

    def sync_identities(self, folder_path, folder_type, changes, removed=()):
        """每一百项提交一次；旧快照通过身份和代次条件避免覆盖新写入。"""
        conn = self._get_connection()
        try:
            operations = 0
            for item, old in changes:
                if Path(item['name']).suffix.lower() not in WHITE_EXTENSIONS:
                    continue
                values = (item['bytes'],item['created_at'],item['mtime'],item['mtime_ns'],item['hash'])
                if old:
                    if old.get('mtime_ns') is None and old['mtime']==item['mtime'] and old['bytes']==item['bytes']:
                        conn.execute('UPDATE files SET mtime_ns=? WHERE id=? AND mtime_ns IS NULL AND mtime=? AND bytes=?', (item['mtime_ns'],old['id'],old['mtime'],old['bytes']))
                    else:
                        conn.execute('''UPDATE files SET bytes=?,created_at=?,mtime=?,mtime_ns=?,hash=?,formatted_info='{}',summary='{}',index_generation=index_generation+1 WHERE id=? AND index_generation=? AND mtime=? AND bytes=?''',values+(old['id'],old['index_generation'],old['mtime'],old['bytes']))
                else:
                    conn.execute('''INSERT OR IGNORE INTO files(filename,folder_path,folder_type,bytes,created_at,mtime,mtime_ns,hash,formatted_info,summary,tags,notes,index_generation,notes_initialized) VALUES(?,?,?,?,?,?,?,?,'{}','{}',?,?,1,1)''',(item['name'],folder_path,folder_type)+values+(json.dumps(item.get('tags',[])),item.get('notes','')))
                operations += 1
                if operations % 100 == 0:
                    conn.commit()
            for old in removed:
                conn.execute('DELETE FROM files WHERE id=? AND index_generation=? AND mtime=? AND bytes=?',(old['id'],old['index_generation'],old['mtime'],old['bytes']))
                operations += 1
                if operations % 100 == 0:
                    conn.commit()
            conn.commit()
        finally:
            conn.close()

    def upsert_file(self,filename,folder_path,folder_type,bytes_size,created_at,mtime,hash_val,formatted_info,tags=None,mtime_ns=None):
        if Path(filename).suffix.lower() not in WHITE_EXTENSIONS:
            return
        with self.connection() as conn:
            conn.execute('''INSERT INTO files(filename,folder_path,folder_type,bytes,created_at,mtime,mtime_ns,hash,formatted_info,summary,tags,index_generation) VALUES(?,?,?,?,?,?,?,?,?,?,?,1)
                ON CONFLICT(filename,folder_path,folder_type) DO UPDATE SET bytes=excluded.bytes,created_at=excluded.created_at,mtime=excluded.mtime,mtime_ns=excluded.mtime_ns,hash=excluded.hash,formatted_info=excluded.formatted_info,summary=excluded.summary,tags=COALESCE(?,files.tags),index_generation=files.index_generation+1''',
                (filename,folder_path,folder_type,bytes_size,created_at,mtime,mtime_ns,hash_val,json.dumps(formatted_info),json.dumps(make_summary(formatted_info)),json.dumps(tags or []),json.dumps(tags) if tags is not None else None))

    def update_metadata_if_current(self,task,formatted_info):
        with self.connection() as conn:
            return conn.execute('''UPDATE files SET formatted_info=?,summary=? WHERE filename=? AND folder_path=? AND folder_type=? AND mtime=? AND bytes=? AND hash=? AND (? IS NULL OR id=?) AND (? IS NULL OR mtime_ns IS NULL OR mtime_ns=?) AND (? IS NULL OR index_generation=?)''',
                (json.dumps(formatted_info),json.dumps(make_summary(formatted_info)),task.filename,task.folder_path,task.folder_type,task.mtime,task.bytes_size,task.hash_val,task.record_id,task.record_id,task.mtime_ns,task.mtime_ns,task.index_generation,task.index_generation)).rowcount==1

    def bump_generation(self,folder_path,folder_type):
        with self.connection() as conn:
            conn.execute("UPDATE files SET index_generation=index_generation+1,formatted_info='{}',summary='{}' WHERE folder_path=? AND folder_type=?",(folder_path,folder_type))

    def refresh_timed_file(self,record,stat,info,hash_val):
        with self.connection() as conn:
            return conn.execute('''UPDATE files SET bytes=?,mtime=?,mtime_ns=?,hash=?,formatted_info=?,summary=?,index_generation=index_generation+1 WHERE id=? AND index_generation=? AND mtime=? AND bytes=?''',(stat.st_size,stat.st_mtime,stat.st_mtime_ns,hash_val,json.dumps(info),json.dumps(make_summary(info)),record['id'],record['index_generation'],record['mtime'],record['bytes'])).rowcount==1

    def update_file_tags(self,filename,folder_path,folder_type,tags):
        with self.connection() as conn:
            conn.execute('UPDATE files SET tags=? WHERE filename=? AND folder_path=? AND folder_type=?',(json.dumps(tags),filename,folder_path,folder_type))

    def initialize_notes(self,items):
        with self.connection() as conn:
            for offset in range(0,len(items),100):
                conn.executemany('UPDATE files SET notes=?,notes_initialized=1 WHERE id=? AND notes_initialized=0',items[offset:offset+100])
                conn.commit()

    def update_file_notes(self,filename,folder_path,folder_type,notes):
        with self.connection() as conn:
            conn.execute('UPDATE files SET notes=?,notes_initialized=1 WHERE filename=? AND folder_path=? AND folder_type=?',(notes,filename,folder_path,folder_type))

    def delete_files(self,folder_path,folder_type,filenames):
        with self.connection() as conn:
            conn.executemany('DELETE FROM files WHERE folder_path=? AND folder_type=? AND filename=?',[(folder_path,folder_type,name) for name in filenames])

    def get_all_tags(self):
        with self.connection() as conn:
            tags = set()
            for row in conn.execute('SELECT tags FROM files'):
                try:
                    tags.update(json.loads(row['tags'] or '[]'))
                except (TypeError, ValueError):
                    pass
            return sorted(tags)

    def clear_records(self,folder_type,folder_path=None):
        with self.connection() as conn:
            if folder_path:
                conn.execute('DELETE FROM files WHERE folder_type=? AND (folder_path=? OR folder_path LIKE ?)',(folder_type,folder_path,folder_path.rstrip('/')+'/%'))
            else:
                conn.execute('DELETE FROM files WHERE folder_type=?',(folder_type,))
