"""持久保存用户显式登记的服务器目录，独立于已有配置。"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading


class DirectoryRegistry:
    def __init__(self,config_path=None):
        self.config_path=Path(config_path or Path(__file__).resolve().parents[1]/'.browser-directories.json')
        self.lock=threading.RLock()
        self._directories=None

    @staticmethod
    def _contains(base,target):
        try:
            return os.path.normcase(os.path.commonpath([base,target]))==os.path.normcase(base)
        except ValueError:
            return False

    def _load(self):
        if self._directories is None:
            try:
                with self.config_path.open(encoding='utf-8') as stream:
                    data=json.load(stream)
            except FileNotFoundError:
                data={'directories':[]}
            if not isinstance(data,dict) or not isinstance(data.get('directories'),list):
                raise ValueError('目录注册配置格式无效')
            self._directories={entry['path']:dict(entry) for entry in data['directories']
                               if isinstance(entry,dict) and all(isinstance(entry.get(key),str) for key in ('path','absolute_path','name'))}
        return self._directories

    def list(self):
        with self.lock:
            return [dict(value) for value in self._load().values()]

    def external_root(self,identifier):
        with self.lock:
            entry=self._load().get('@external/'+identifier)
            if entry is None:
                raise ValueError('目录尚未登记')
            root=entry['absolute_path']
        if os.path.normcase(os.path.realpath(root))!=os.path.normcase(root):
            raise ValueError('登记目录的路径边界已经变化')
        return root

    def register(self,value,outputs_root):
        if not isinstance(value,str) or not value.strip() or '\x00' in value:
            raise ValueError('请输入目录路径')
        value=value.strip()
        if os.name=='nt':
            drive,tail=os.path.splitdrive(value)
            if drive and not os.path.isabs(value):
                raise ValueError('请使用完整盘符路径')
        elif '\\' in value or (len(value)>1 and value[1]==':'):
            raise ValueError('请使用服务器操作系统支持的路径')
        base=os.path.realpath(outputs_root)
        target=os.path.realpath(value if os.path.isabs(value) else os.path.join(base,value))
        if not os.path.isdir(target):
            raise FileNotFoundError('目录不存在')
        if self._contains(base,target):
            relative=os.path.relpath(target,base).replace('\\','/')
            virtual='' if relative=='.' else relative
            # 保留虚拟命名空间；同名物理目录也通过稳定ID登记。
            external=virtual=='@external' or virtual.startswith('@external/')
        else:
            external=True
        if external:
            identifier=hashlib.sha256(os.path.normcase(target).encode('utf-8')).hexdigest()[:32]
            virtual='@external/'+identifier
        entry={'path':virtual,'absolute_path':target,'name':os.path.basename(target.rstrip('/\\')) or target}
        with self.lock:
            current=self._load()
            for existing in current.values():
                if os.path.normcase(existing['absolute_path'])==os.path.normcase(target):
                    return dict(existing)
            updated=dict(current)
            updated[virtual]=entry
            self.config_path.parent.mkdir(parents=True,exist_ok=True)
            temporary=None
            try:
                with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.config_path.parent,prefix='directories-',suffix='.tmp',delete=False) as stream:
                    temporary=stream.name
                    json.dump({'directories':list(updated.values())},stream,ensure_ascii=False,indent=2)
                os.replace(temporary,self.config_path)
                self._directories=updated
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        return dict(entry)
