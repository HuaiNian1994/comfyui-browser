"""以独立包加载插件模块，测试过程无需启动 ComfyUI。"""
import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    for package, directory in [("browser_test", ROOT), ("browser_test.utils", ROOT / "utils"), ("browser_test.services", ROOT / "services")]:
        if package not in sys.modules:
            module = types.ModuleType(package)
            module.__path__ = [str(directory)]
            sys.modules[package] = module
    return importlib.import_module("browser_test." + name)
