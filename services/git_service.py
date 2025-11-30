"""Git服务"""
import re
from pathlib import Path
from typing import Optional

from ..utils.git_utils import run_git_command
from ..constants import GIT_REMOTE_NAME


class GitService:
    """Git操作服务"""
    
    @staticmethod
    def get_remote_url(repo_path: str) -> Optional[str]:
        """
        获取远程仓库URL
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            远程仓库URL,如果不存在则返回None
        """
        cmd = f'git remote get-url {GIT_REMOTE_NAME}'
        ret = run_git_command(
            cmd,
            repo_path,
            log_cmd=False,
            log_code=False,
            log_message=False
        )
        if ret.returncode == 0 and ret.stdout:
            return ret.stdout.split('\n')[0]
        return None
    
    @staticmethod
    def clone_repo(repo_url: str, target_dir: str, depth: int = 1) -> tuple[bool, str]:
        """
        克隆远程仓库
        
        Args:
            repo_url: 仓库URL
            target_dir: 目标目录(完整路径)
            depth: 克隆深度
            
        Returns:
            (是否成功, 错误信息)
        """
        parent_dir = str(Path(target_dir).parent)
        dir_name = Path(target_dir).name
        cmd = f'git clone --depth {depth} {repo_url} {dir_name}'
        ret = run_git_command(cmd, parent_dir)
        if ret.returncode == 0:
            return True, ""
        return False, ret.stdout + ret.stderr
    
    @staticmethod
    def pull(repo_path: str) -> tuple[bool, str]:
        """
        拉取最新代码
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            (是否成功, 错误信息)
        """
        cmd = 'git pull'
        ret = run_git_command(cmd, repo_path)
        if ret.returncode == 0:
            return True, ""
        return False, ret.stdout + ret.stderr
    
    @staticmethod
    def parse_repo_url(repo_url: str) -> Optional[tuple[str, str]]:
        """
        解析仓库URL,提取author和repo name
        
        支持的格式:
        - https://github.com/author/repo.git
        - https://github.com/author/repo
        - git@github.com:author/repo.git
        
        Args:
            repo_url: 仓库URL
            
        Returns:
            (author, repo_name) 或 None
        """
        pattern = r'[:\\/]([a-zA-Z0-9-_]+)\\/([a-zA-Z0-9-_]+)(\\.git)?'
        match = re.search(pattern, repo_url)
        if match:
            return match.group(1), match.group(2)
        return None
