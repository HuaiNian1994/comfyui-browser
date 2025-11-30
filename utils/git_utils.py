"""Git操作工具"""
import subprocess
from pathlib import Path
from typing import Optional

from ..config import get_collections_path
from ..constants import GIT_REMOTE_NAME


def log(message: str):
    """打印日志"""
    print(f'[comfyui-browser] {message}')


def run_git_command(
    cmd: str,
    cwd: str,
    log_cmd: bool = True,
    log_code: bool = True,
    log_message: bool = True
) -> subprocess.CompletedProcess:
    """
    执行Git命令
    
    Args:
        cmd: Git命令
        cwd: 工作目录
        log_cmd: 是否打印命令
        log_code: 是否打印返回码
        log_message: 是否打印输出信息
        
    Returns:
        subprocess.CompletedProcess对象
    """
    if log_cmd:
        log(f'running: {cmd}')

    ret = subprocess.run(
        f'cd {cwd} && {cmd}',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="UTF-8"
    )
    
    if log_code:
        log('succeeded' if ret.returncode == 0 else 'failed')
    
    if log_message and (ret.stdout or ret.stderr):
        log(ret.stdout + ret.stderr)

    return ret


def git_init():
    """初始化Git仓库并配置用户信息"""
    collections_path = get_collections_path()
    git_dir = Path(collections_path) / '.git'
    
    if not git_dir.exists():
        run_git_command('git init', collections_path)

    # 配置用户名
    ret = run_git_command(
        'git config user.name',
        collections_path,
        log_cmd=False,
        log_code=False,
        log_message=False
    )
    if not ret.stdout.strip():
        ret = run_git_command(
            'whoami',
            collections_path,
            log_cmd=False,
            log_code=False,
            log_message=False
        )
        username = ret.stdout.strip()
        run_git_command(f'git config user.name "{username}"', collections_path)

    # 配置邮箱
    ret = run_git_command(
        'git config user.email',
        collections_path,
        log_cmd=False,
        log_code=False,
        log_message=False
    )
    if not ret.stdout.strip():
        ret = run_git_command(
            'hostname',
            collections_path,
            log_cmd=False,
            log_code=False,
            log_message=False
        )
        hostname = ret.stdout.strip()
        run_git_command(f'git config user.email "{hostname}"', collections_path)
