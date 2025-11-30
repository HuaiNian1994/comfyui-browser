"""配置管理模块"""
import json
import functools
from pathlib import Path
from typing import Dict, Any

import folder_paths
from comfy.cli_args import args

# 获取browser路径
BROWSER_PATH = Path(__file__).parent
CONFIG_PATH = BROWSER_PATH / 'config.json'

# 服务器基础URL配置
SERVER_BASE_URL = f'http://{args.listen}:{args.port}'
# 支持IPv6
if ':' in args.listen:
    SERVER_BASE_URL = f'http://[{args.listen}]:{args.port}'


@functools.cache
def get_config() -> Dict[str, Any]:
    """获取完整配置,包含默认配置和用户配置"""
    default_config = {
        "collections": str(BROWSER_PATH / 'collections'),
        "download_logs": str(BROWSER_PATH / 'download_logs'),
        "outputs": get_output_directory(),
        "sources": str(BROWSER_PATH / 'sources'),
    }
    
    user_config = load_user_config()
    return {**default_config, **user_config}


def load_user_config() -> Dict[str, Any]:
    """加载用户配置文件"""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_output_directory() -> str:
    """获取ComfyUI输出目录"""
    if args.output_directory:
        return str(Path(args.output_directory).resolve())
    return folder_paths.get_output_directory()


# 路径获取函数
@functools.cache
def get_collections_path() -> str:
    """获取collections路径"""
    return get_config()['collections']


@functools.cache
def get_sources_path() -> str:
    """获取sources路径"""
    return get_config()['sources']


@functools.cache
def get_outputs_path() -> str:
    """获取outputs路径"""
    return get_config()['outputs']


@functools.cache
def get_download_logs_path() -> str:
    """获取download_logs路径"""
    return get_config()['download_logs']
