"""用执行器契约替身验证包装层，真实模型验收另见验收报告。"""
import asyncio
import contextvars
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from module_loader import load_module

hooks = load_module('timing.hooks')
recording = load_module('timing.recording')
storage = load_module('timing.storage')


class HookTests(unittest.TestCase):
    def test_calls_async_dynamic_cache_failure_and_sampler_notifications(self):
        context = contextvars.ContextVar('fake_node_context', default=None)
        class SyncNode:
            FUNCTION = 'run'
            def run(self, value): return (value,)
        class AsyncNode:
            FUNCTION = 'run'
            async def run(self, value):
                await asyncio.sleep(0.002)
                return (value,)
        class TaskNode:
            FUNCTION = 'run'
            def run(self):
                async def work():
                    await asyncio.sleep(0.002)
                    return ('task result',)
                return asyncio.create_task(work())
        class Sampler:
            def __init__(self, function): self.function = function
        class Queue:
            def put(self, item): return item
        class Executor:
            success = True
            history_result = {'outputs': {}}
            status_messages = [('execution_cached', {'nodes': ['cached']})]
            def execute(self, prompt, prompt_id, extra_data, execute_outputs):
                def use(node, index=0):
                    context.set(types.SimpleNamespace(prompt_id=prompt_id, node_id=node, list_index=index))
                use('1')
                self.values = [SyncNode().run(0)]
                use('1', 1)
                self.values.append(SyncNode().run(False))
                async def asynchronous():
                    use('dynamic.1')
                    value = await AsyncNode().run('done')
                    use('dynamic.2')
                    assert await TaskNode().run() == ('task result',)
                    return value
                self.values.append(asyncio.run(asynchronous()))
                use('sample')
                def algorithm(callback):
                    for i in [0, 0, 1, 2]: callback({'i': i})
                    return 'sampled'
                self.notifications = []
                self.values.append(Sampler(algorithm).function(callback=self.notifications.append))
                if extra_data.get('fail'):
                    self.success = False
                    raise RuntimeError('original error')
                return 'original return'
        comfy = types.ModuleType('comfy')
        comfy.samplers = types.SimpleNamespace(KSAMPLER=Sampler)
        comfy.model_management = types.SimpleNamespace(load_models_gpu=lambda: None)
        comfy.utils = types.SimpleNamespace(load_torch_file=lambda: None)
        comfy.sd = types.SimpleNamespace()
        execution = types.SimpleNamespace(PromptQueue=Queue, PromptExecutor=Executor,
                                          get_output_from_returns=lambda *a: ([], {}, False))
        modules = {'execution': execution, 'nodes': types.SimpleNamespace(NODE_CLASS_MAPPINGS={
            'CLIPTextEncode': SyncNode, 'DynamicTestNode': AsyncNode, 'TaskTestNode': TaskNode}), 'comfy': comfy,
            'comfy.samplers': comfy.samplers, 'comfy.model_management': comfy.model_management,
            'comfy.utils': comfy.utils, 'comfy.sd': comfy.sd,
            'comfy.cli_args': types.SimpleNamespace(args=types.SimpleNamespace(disable_metadata=False)),
            'comfy_execution.utils': types.SimpleNamespace(get_executing_context=context.get),
            'folder_paths': types.SimpleNamespace(get_output_directory=lambda: '.')}
        with tempfile.TemporaryDirectory() as folder:
            real_store = storage.TimingStore(Path(folder) / 'test.db', start_worker=False)
            with patch.dict('sys.modules', modules), patch.object(hooks, '_installed', False), \
                    patch.object(storage, 'store', None), patch.object(storage, 'TimingStore', return_value=real_store):
                hooks.install('unused')
                installed = Executor.execute
                hooks.install('unused')
                self.assertIs(Executor.execute, installed)
                Queue().put((1, 'task'))
                executor = Executor()
                self.assertEqual(executor.execute({'cached': {}}, 'task'), 'original return')
                self.assertEqual(executor.values, [(0,), (False,), ('done',), 'sampled'])
                self.assertEqual(len(executor.notifications), 4)
                import json
                with real_store.connect() as conn:
                    result = json.loads(conn.execute('SELECT payload FROM timing_tasks').fetchone()[0])
                calls = [s for s in result['spans'] if s.get('kind') == 'node']
                self.assertEqual([s['list_index'] for s in calls[:2]], [0, 1])
                self.assertGreaterEqual(calls[2]['elapsed_ms'], 1)
                self.assertEqual(calls[2]['node_id'], 'dynamic.1')
                self.assertEqual(calls[3]['status'], 'complete')
                self.assertGreaterEqual(calls[3]['elapsed_ms'], 1)
                loop = next(s for s in result['spans'] if s['category'] == 'sampling_loop')
                self.assertEqual(loop['iterations'], 3)
                self.assertFalse(result['sampling_complete'])  # 未登记节点可能自行采样。
                self.assertEqual(result['nodes'][0]['status'], 'cached')
                self.assertIsNone(recording.active_session.get())
                with self.assertRaisesRegex(RuntimeError, 'original error'):
                    executor.execute({}, 'failure', {'fail': True})
                with real_store.connect() as conn:
                    failed = json.loads(conn.execute("SELECT payload FROM timing_tasks WHERE task_id='failure'").fetchone()[0])
                self.assertEqual(failed['status'], 'failed')
                self.assertIsNone(recording.summary(failed))
