"""HTTP客户端工具"""
import requests
from requests.adapters import HTTPAdapter, Retry


def create_http_client() -> requests.Session:
    """
    创建带重试机制的HTTP客户端
    
    Returns:
        配置了重试机制的requests.Session对象
    """
    adapter = HTTPAdapter(max_retries=Retry(3, backoff_factor=0.1))
    session = requests.Session()
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
