"""显式外部目录登记、边界校验和文件操作回归。"""
import asyncio
import importlib
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from aiohttp import web
from aiohttp.test_utils import TestClient,TestServer
from module_loader import ROOT


class ExternalDirectoryTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory(prefix='external-directories-')
        cls.root=Path(cls.temporary.name)
        cls.outputs=cls.root/'outputs';cls.outputs.mkdir()
        cls.collections=cls.root/'collections';cls.collections.mkdir()
        prefix='external_directory_tests'
        for name,directory in [(prefix,ROOT),(prefix+'.utils',ROOT/'utils'),(prefix+'.services',ROOT/'services'),(prefix+'.routes',ROOT/'routes')]:
            module=types.ModuleType(name);module.__path__=[str(directory)];sys.modules[name]=module
        config=types.ModuleType(prefix+'.config')
        config.get_outputs_path=lambda:str(cls.outputs)
        config.get_sources_path=lambda:str(cls.outputs)
        config.get_collections_path=lambda:str(cls.collections)
        config.get_config=lambda:{}
        config.CONFIG_PATH=str(cls.root/'unused-config.json')
        sys.modules[config.__name__]=config
        utility=sys.modules[prefix+'.utils']
        cls.paths=importlib.import_module(prefix+'.utils.path_utils')
        cls.registry_module=importlib.import_module(prefix+'.services.directory_registry')
        cls.paths.directory_registry=cls.registry_module.DirectoryRegistry(cls.root/'registered.json')
        for module_name,symbols in [('utils.path_utils',['get_parent_path','get_info_filename','add_uuid_to_filename']),('utils.file_utils',['get_target_folder_files']),('utils.image_utils',['extract_comfyui_png_metadata','extract_detailed_metadata'])]:
            module=importlib.import_module(prefix+'.'+module_name)
            for symbol in symbols:setattr(utility,symbol,getattr(module,symbol))
        utility.git_init=lambda:None;utility.run_git_command=lambda *args:None
        previous=os.getcwd()
        try:
            os.chdir(cls.root)
            cls.files=importlib.import_module(prefix+'.routes.files')
        finally:
            os.chdir(previous)
        cls.directories=importlib.import_module(prefix+'.routes.directories')
        cls.favorites=importlib.import_module(prefix+'.routes.collections')

    @classmethod
    def tearDownClass(cls):
        cls.files.metadata_index_queue.shutdown()
        cls.files.directory_scan_service.shutdown()
        cls.files.reindex_service.shutdown()
        cls.temporary.cleanup()

    async def asyncSetUp(self):
        self.temporary_dir=tempfile.TemporaryDirectory(dir=self.root)
        self.external=Path(self.temporary_dir.name)
        self.db=self.files.DBService(str(self.external/'test.db'))
        self.queue=self.files.MetadataIndexQueue(self.db,lambda _: {'parser_version':self.files.PARSER_VERSION,'models':['external']})
        app=web.Application()
        app['file_database']=self.db;app['file_metadata_queue']=self.queue
        app.add_routes([web.get('/directories',self.directories.api_get_directories),web.post('/directories',self.directories.api_register_directory),
                        web.get('/files',self.files.api_get_files),web.get('/files/view',self.files.api_view_file),
                        web.post('/files/update',self.files.api_update_file),web.post('/files/delete',self.files.api_delete_file),
                        web.post('/files/tag',self.files.api_add_tag_to_file),web.post('/files/untag',self.files.api_remove_tag_from_file),
                        web.post('/files/open-folder',self.files.api_open_folder),web.post('/files/reindex',self.files.api_reindex_files),
                        web.get('/files/reindex/{job_id}',self.files.api_get_reindex_job),web.post('/collections',self.favorites.api_add_to_collections)])
        self.client=TestClient(TestServer(app));await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        await asyncio.to_thread(self.queue.shutdown)
        self.temporary_dir.cleanup()

    async def register(self,path=None):
        response=await self.client.post('/directories',json={'path':str(path or self.external)})
        self.assertEqual(response.status,201)
        return (await response.json())['directory']

    async def test_registration_persists_and_internal_paths_remain_relative(self):
        first=await self.register()
        second=await self.register()
        self.assertEqual(first,second)
        self.assertTrue(first['path'].startswith('@external/'))
        registry=self.registry_module.DirectoryRegistry(self.root/'registered.json')
        self.assertIn(first,registry.list())
        internal=self.outputs/'内部目录';internal.mkdir(exist_ok=True)
        record=await self.register(internal)
        self.assertEqual(record['path'],'内部目录')
        if os.name=='nt':
            self.assertEqual((await self.register(str(internal).upper()))['path'],record['path'])
        outside_relative=os.path.relpath(self.external,self.outputs)
        self.assertEqual((await self.register(outside_relative))['path'],first['path'])

    async def test_external_json_tags_notes_rename_collection_and_delete(self):
        source=self.external/'工作 流#.json';source.write_text('{"nodes":[]}',encoding='utf-8')
        entry=await self.register()
        identity={'folder_type':'outputs','folder_path':entry['path'],'filename':source.name}
        response=await self.client.get('/files',params={'folder_type':'outputs','folder_path':entry['path']})
        self.assertEqual(response.status,200)
        response=await self.client.post('/files/tag',json=dict(identity,tag='用户标签'))
        self.assertEqual((await response.json())['tags'],['用户标签'])
        response=await self.client.post('/files/update',json=dict(identity,new_data={'filename':'新工作流.json','notes':'用户备注'}))
        self.assertEqual(response.status,201)
        identity['filename']='新工作流.json'
        renamed=self.external/identity['filename']
        self.assertTrue(renamed.exists());self.assertFalse(source.exists())
        record=self.db.get_file(identity['filename'],entry['path'],'outputs')
        self.assertEqual(record['tags'],['用户标签']);self.assertEqual(record['notes'],'用户备注')
        response=await self.client.get('/files/view',params=identity)
        self.assertEqual(await response.read(),renamed.read_bytes())
        response=await self.client.post('/collections',json=identity)
        self.assertEqual(response.status,201)
        copied=list(self.collections.glob('新工作流_*.json'))
        self.assertTrue(copied);self.assertEqual(copied[-1].read_bytes(),renamed.read_bytes())
        response=await self.client.post('/files/untag',json=dict(identity,tag='用户标签'))
        self.assertEqual((await response.json())['tags'],[])
        with patch.object(self.files,'open_system_folder',return_value=True) as opened:
            response=await self.client.post('/files/open-folder',json=identity)
            self.assertEqual(response.status,200);opened.assert_called_once_with(str(self.external))
        response=await self.client.post('/files/delete',json=identity)
        self.assertEqual(response.status,201);self.assertFalse(renamed.exists())
        self.assertIsNone(self.db.get_file(identity['filename'],entry['path'],'outputs'))

    async def test_unregistered_and_traversal_operations_are_rejected(self):
        entry=await self.register()
        for folder,name in [('@external/unknown','x.json'),(entry['path']+'/..','x.json'),(entry['path'],'../escape.json'),(str(self.external),'x.json')]:
            response=await self.client.get('/files/view',params={'folder_type':'outputs','folder_path':folder,'filename':name})
            self.assertEqual(response.status,400)
        with self.assertRaises(ValueError):self.paths.resolve_folder_path('sources',entry['path'])
        with self.assertRaises(ValueError):self.paths.resolve_folder_path('outputs',str(self.external))

    async def test_symlink_escape_is_excluded_from_scan_and_file_access(self):
        outside=self.root/'private.json';outside.write_text('private',encoding='utf-8')
        link=self.external/'escaped.json'
        try:link.symlink_to(outside)
        except OSError as exc:self.skipTest(str(exc))
        entry=await self.register()
        with self.assertRaises(ValueError):self.paths.resolve_file_path('outputs',entry['path'],link.name)
        response=await self.client.get('/files',params={'folder_type':'outputs','folder_path':entry['path']})
        self.assertEqual(response.status,200)
        self.assertNotIn(link.name,[row['name'] for row in (await response.json())['files']])

    async def test_external_reindex_async_only_current_layer(self):
        (self.external/'one.json').write_text('{}')
        child=self.external/'child';child.mkdir();(child/'two.json').write_text('{}')
        entry=await self.register()
        response=await self.client.post('/files/reindex',json={'folder_type':'outputs','folder_paths':[entry['path']]})
        self.assertEqual(response.status,202)
        job=(await response.json())['job_id']
        for _ in range(100):
            result=await (await self.client.get('/files/reindex/'+job)).json()
            if result['status']=='complete':break
            await asyncio.sleep(.02)
        self.assertEqual(result['indexed_folders'],1);self.assertEqual(result['indexed_files'],1)
        self.assertIsNone(self.db.get_file('two.json',entry['path']+'/child','outputs'))

    async def test_concurrent_rename_same_destination_preserves_both_inputs(self):
        (self.external/'first.json').write_text('first')
        (self.external/'second.json').write_text('second')
        entry=await self.register()
        await self.client.get('/files',params={'folder_type':'outputs','folder_path':entry['path']})
        async def rename(name):
            return await self.client.post('/files/update',json={'folder_type':'outputs','folder_path':entry['path'],'filename':name,'new_data':{'filename':'destination.json'}})
        responses=await asyncio.gather(rename('first.json'),rename('second.json'))
        self.assertEqual(sorted(response.status for response in responses),[201,400])
        remaining={file.read_text() for file in self.external.glob('*.json')}
        self.assertEqual(remaining,{'first','second'})

    async def test_concurrent_collection_copy_uses_unique_names_and_rejects_existing(self):
        source=self.external/'same.json';source.write_text('source')
        entry=await self.register()
        identity={'folder_type':'outputs','folder_path':entry['path'],'filename':source.name}
        before=set(self.collections.glob('same_*.json'))
        responses=await asyncio.gather(*(self.client.post('/collections',json=identity) for _ in range(3)))
        self.assertTrue(all(response.status==201 for response in responses))
        created=set(self.collections.glob('same_*.json'))-before
        self.assertEqual(len(created),3)
        existing=self.collections/'fixed-collision.json';existing.write_text('keep')
        with patch.object(self.favorites,'add_uuid_to_filename',return_value=existing.name):
            response=await self.client.post('/collections',json=identity)
        self.assertEqual(response.status,409)
        self.assertEqual(existing.read_text(),'keep')

    async def test_sidecar_symlink_cannot_write_outside_registered_root(self):
        (self.external/'file.json').write_text('{}')
        private=self.root/'private-info.json';private.write_text('keep')
        link=self.external/'file.info'
        try:link.symlink_to(private)
        except OSError as exc:self.skipTest(str(exc))
        entry=await self.register()
        response=await self.client.post('/files/update',json={'folder_type':'outputs','folder_path':entry['path'],'filename':'file.json','new_data':{'notes':'changed'}})
        self.assertEqual(response.status,400)
        self.assertEqual(private.read_text(),'keep')

    async def test_windows_unc_registration(self):
        if os.name!='nt':self.skipTest('Windows 路径仅由 Windows 服务器解释')
        import ntpath
        unc=r'\\fixture-server\share\folder'
        with patch.object(self.registry_module.os.path,'realpath',side_effect=ntpath.normpath),patch.object(self.registry_module.os.path,'isdir',return_value=True):
            entry=self.paths.directory_registry.register(unc,str(self.outputs))
        self.assertEqual(entry['absolute_path'],unc)
        self.assertTrue(entry['path'].startswith('@external/'))
