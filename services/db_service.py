import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class DBService:
    def __init__(self, db_path="comfyui_browser.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Files table
        # hash: calculated from path + name + created_time + size (as per requirement)
        # remote_info: stores extracted info like models, loras, width, height
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                folder_path TEXT NOT NULL,
                folder_type TEXT NOT NULL,
                bytes INTEGER,
                created_at REAL,
                mtime REAL,
                hash TEXT,
                formatted_info TEXT, -- JSON string: {models: [], loras: [], ...}
                tags TEXT, -- JSON string: ["tag1", "tag2"]
                UNIQUE(filename, folder_path, folder_type)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_folder ON files (folder_path, folder_type)')
        
        conn.commit()
        conn.close()

    def get_files_in_folder(self, folder_path: str, folder_type: str) -> Dict[str, dict]:
        """
        Get all files in a specific folder from DB.
        Returns a dict keyed by filename for easy lookup.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM files WHERE folder_path = ? AND folder_type = ?",
            (folder_path, folder_type)
        )
        
        rows = cursor.fetchall()
        result = {}
        for row in rows:
            file_data = dict(row)
            # Parse JSON fields
            try:
                file_data['formatted_info'] = json.loads(file_data['formatted_info']) if file_data['formatted_info'] else {}
            except:
                file_data['formatted_info'] = {}
                
            try:
                file_data['tags'] = json.loads(file_data['tags']) if file_data['tags'] else []
            except:
                file_data['tags'] = []
                
            result[row['filename']] = file_data
            
        conn.close()
        return result

    def upsert_file(self, 
                    filename: str, 
                    folder_path: str, 
                    folder_type: str, 
                    bytes_size: int, 
                    created_at: float, 
                    mtime: float, 
                    hash_val: str, 
                    formatted_info: Dict[str, Any],
                    tags: List[str] = None):
        """
        Insert or Update a file record.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        formatted_info_json = json.dumps(formatted_info)
        tags_json = json.dumps(tags) if tags is not None else None

        # Check if exists to preserve tags if not provided (though sync logic usually provides full info)
        # For this specific sync logic, we usually re-parse metadata on update, but tags might be user-defined.
        # If tags is None, we should try to keep existing tags.
        
        existing_tags = None
        if tags is None:
            cursor.execute(
                "SELECT tags FROM files WHERE filename=? AND folder_path=? AND folder_type=?",
                (filename, folder_path, folder_type)
            )
            row = cursor.fetchone()
            if row:
                existing_tags = row['tags']
        
        final_tags = tags_json if tags is not None else (existing_tags if existing_tags else '[]')

        cursor.execute('''
            INSERT INTO files (filename, folder_path, folder_type, bytes, created_at, mtime, hash, formatted_info, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(filename, folder_path, folder_type) DO UPDATE SET
                bytes=excluded.bytes,
                created_at=excluded.created_at,
                mtime=excluded.mtime,
                hash=excluded.hash,
                formatted_info=excluded.formatted_info,
                tags=COALESCE(excluded.tags, files.tags)
        ''', (filename, folder_path, folder_type, bytes_size, created_at, mtime, hash_val, formatted_info_json, final_tags))
        
        conn.commit()
        conn.close()

    def delete_files(self, folder_path: str, folder_type: str, filenames: List[str]):
        """
        Delete specific files from DB.
        """
        if not filenames:
            return
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(filenames))
        query = f"DELETE FROM files WHERE folder_path = ? AND folder_type = ? AND filename IN ({placeholders})"
        params = [folder_path, folder_type] + filenames
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    def update_metadata_if_current(self, task, formatted_info: Dict[str, Any]) -> bool:
        """只更新任务仍对应的文件元数据；保留用户字段，删除的记录保持删除。"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """UPDATE files SET formatted_info=?
                WHERE filename=? AND folder_path=? AND folder_type=?
                AND mtime=? AND bytes=? AND hash=? AND (? IS NULL OR id=?)""",
                (json.dumps(formatted_info), task.filename, task.folder_path, task.folder_type,
                 task.mtime, task.bytes_size, task.hash_val, task.record_id, task.record_id),
            )
            return cursor.rowcount == 1

    def update_file_tags(self, filename: str, folder_path: str, folder_type: str, tags: List[str]):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        tags_json = json.dumps(tags)
        cursor.execute('''
            UPDATE files SET tags = ? 
            WHERE filename = ? AND folder_path = ? AND folder_type = ?
        ''', (tags_json, filename, folder_path, folder_type))
        
        conn.commit()
        conn.close()

    def get_all_tags(self) -> List[str]:
        """
        获取数据库中所有文件使用的唯一标签列表。
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT tags FROM files WHERE tags IS NOT NULL AND tags != '[]'")
        
        all_tags = set()
        for row in cursor.fetchall():
            try:
                tags_json = row['tags']
                file_tags = json.loads(tags_json)
                for tag in file_tags:
                    all_tags.add(tag)
            except Exception:
                pass
        
        conn.close()
        return sorted(list(all_tags))

    def clear_records(self, folder_type: str, folder_path: Optional[str] = None):
        """
        删除指定范围的索引记录。如果未提供 folder_path，则清空该 folder_type 下的全部记录。
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if folder_path:
            normalized_folder = folder_path.rstrip('/')
            like_pattern = f"{normalized_folder}/%"
            cursor.execute(
                "DELETE FROM files WHERE folder_type = ? AND (folder_path = ? OR folder_path LIKE ?)",
                (folder_type, normalized_folder, like_pattern)
            )
        else:
            cursor.execute("DELETE FROM files WHERE folder_type = ?", (folder_type,))

        conn.commit()
        conn.close()
