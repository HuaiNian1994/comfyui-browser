import importlib.util
import sys
import types
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

SERVICES_DIR = Path(__file__).resolve().parents[1] / "services"


def load_metadata_indexer_module():
    """
    在不执行 services/__init__.py 的情况下按需加载 metadata_indexer，
    以避免外部依赖影响单测。
    """
    services_pkg = types.ModuleType("services")
    services_pkg.__path__ = [str(SERVICES_DIR)]
    sys.modules.setdefault("services", services_pkg)

    db_spec = importlib.util.spec_from_file_location("services.db_service", SERVICES_DIR / "db_service.py")
    db_module = importlib.util.module_from_spec(db_spec)
    sys.modules["services.db_service"] = db_module
    assert db_spec.loader is not None
    db_spec.loader.exec_module(db_module)

    metadata_spec = importlib.util.spec_from_file_location("services.metadata_indexer", SERVICES_DIR / "metadata_indexer.py")
    metadata_module = importlib.util.module_from_spec(metadata_spec)
    sys.modules["services.metadata_indexer"] = metadata_module
    assert metadata_spec.loader is not None
    metadata_spec.loader.exec_module(metadata_module)
    return metadata_module


class FakeDBService:
    """最小化的DBService替身,记录入参便于断言。"""

    def __init__(self) -> None:
        self.upsert_calls: List[Dict[str, Any]] = []

    def upsert_file(
        self,
        filename: str,
        folder_path: str,
        folder_type: str,
        bytes_size: int,
        created_at: float,
        mtime: float,
        hash_val: str,
        formatted_info: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> None:
        self.upsert_calls.append({
            "filename": filename,
            "folder_path": folder_path,
            "folder_type": folder_type,
            "bytes_size": bytes_size,
            "created_at": created_at,
            "mtime": mtime,
            "hash_val": hash_val,
            "formatted_info": formatted_info,
            "tags": tags
        })


class MetadataIndexQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        metadata_module = load_metadata_indexer_module()
        cls.MetadataIndexQueue = metadata_module.MetadataIndexQueue
        cls.MetadataIndexTask = metadata_module.MetadataIndexTask

    def test_processes_tasks_in_background(self) -> None:
        fake_db = FakeDBService()
        extracted_paths: List[str] = []

        def capture_extractor(file_path: str) -> Dict[str, Any]:
            extracted_paths.append(file_path)
            return {"path": file_path}

        queue = self.MetadataIndexQueue(fake_db, capture_extractor)

        task = self.MetadataIndexTask(
            filename="sample.png",
            folder_path="",
            folder_type="outputs",
            file_path=str(Path("sample.png")),
            bytes_size=123,
            created_at=1.0,
            mtime=1.0,
            hash_val="h1",
            tags=["tag1"]
        )

        queue.enqueue(task)
        self.assertTrue(queue.wait_until_idle(1.5))
        self.assertEqual(len(fake_db.upsert_calls), 1)
        self.assertEqual(extracted_paths, [str(Path("sample.png"))])
        self.assertEqual(fake_db.upsert_calls[0]["formatted_info"]["path"], str(Path("sample.png")))
        self.assertEqual(fake_db.upsert_calls[0]["tags"], ["tag1"])

    def test_deduplicates_same_task_key(self) -> None:
        fake_db = FakeDBService()
        queue = self.MetadataIndexQueue(fake_db, lambda _: {"path": "x"})

        base_kwargs = dict(
            filename="dup.png",
            folder_path="",
            folder_type="outputs",
            file_path=str(Path("dup.png")),
            bytes_size=100,
            created_at=2.0,
            mtime=2.0,
            tags=None
        )

        first = self.MetadataIndexTask(hash_val="hash-a", **base_kwargs)
        duplicate = self.MetadataIndexTask(hash_val="hash-a", **base_kwargs)
        refreshed = self.MetadataIndexTask(hash_val="hash-b", **base_kwargs)

        queue.enqueue(first)
        queue.enqueue(duplicate)  # 应该被去重
        self.assertTrue(queue.wait_until_idle(1.5))
        self.assertEqual(len(fake_db.upsert_calls), 1)

        queue.enqueue(refreshed)
        self.assertTrue(queue.wait_until_idle(1.5))
        self.assertEqual(len(fake_db.upsert_calls), 2)


if __name__ == '__main__':
    unittest.main()

