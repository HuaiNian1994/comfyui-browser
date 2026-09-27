"""ComfyUI 的运行期适配；函数包装保留签名、异常与异步行为。"""
from __future__ import annotations

import contextlib
import functools
import inspect
import logging
import os
import threading
import time

from ..metadata.registry import NODES
from . import storage
from .containers import fingerprint
from .recording import Session, active_session, active_span

logger = logging.getLogger(__name__)
_installed = False
_queued = {}
_queue_lock = threading.Lock()


@contextlib.contextmanager
def safe_span(session, category, **metadata):
    """计时故障只影响覆盖信息，业务函数及其异常保持原样。"""
    manager = session.span(category, **metadata)
    try:
        span = manager.__enter__()
    except Exception as exc:
        session.issues.append('sampling_instrumentation:' + type(exc).__name__)
        yield {}
        return
    try:
        yield span
    except BaseException:
        import sys
        try:
            manager.__exit__(*sys.exc_info())
        except BaseException:
            pass
        raise
    else:
        try:
            manager.__exit__(None, None, None)
        except Exception as exc:
            session.issues.append('sampling_instrumentation:' + type(exc).__name__)


def category_for(class_type):
    return NODES.get(class_type, {}).get('timing', {}).get('category', 'node_other')


def install(db_path, on_written=None):
    global _installed
    if _installed:
        return
    import execution
    import nodes
    import comfy.samplers
    import comfy.model_management
    import comfy.utils
    import comfy.sd
    from comfy_execution.utils import get_executing_context
    import folder_paths
    from comfy.cli_args import args

    storage.store = storage.TimingStore(db_path, on_written)

    def node_scope(class_type):
        session = active_session.get()
        try:
            ctx = get_executing_context()
        except Exception:
            if session: session.issues.append('sampling_context_unavailable')
            return contextlib.nullcontext()
        if session is None or session.closed or ctx is None or ctx.prompt_id != session.task_id:
            return contextlib.nullcontext()
        category = category_for(class_type)
        if class_type not in NODES:
            session.issues.append('unclassified_node:' + str(ctx.node_id))
        return safe_span(session, category, kind='node', node_id=str(ctx.node_id), class_type=class_type,
                            list_index=ctx.list_index, resource=NODES.get(class_type, {}).get('timing', {}).get('resource'),
                            detail_coverage='standard_hooks' if class_type in NODES else 'node_only')

    def timed_function(function, class_type):
        if inspect.iscoroutinefunction(function):
            @functools.wraps(function)
            async def wrapped(*a, **kw):
                with node_scope(class_type):
                    return await function(*a, **kw)
        else:
            @functools.wraps(function)
            def wrapped(*a, **kw):
                session = active_session.get()
                with node_scope(class_type) as span:
                    result = function(*a, **kw)
                if session and span and inspect.isawaitable(result):
                    span['status'] = 'running'
                    span.pop('end_ms', None)
                    if hasattr(result, 'add_done_callback'):
                        def done(future):
                            span['end_ms'] = (session.clock() - session.start) / 1e6
                            span['status'] = 'failed' if future.cancelled() or future.exception() else 'complete'
                        result.add_done_callback(done)
                    else:
                        session.issues.append('unfinished_span:awaitable_without_completion_signal')
                return result
        wrapped._browser_timing = True
        return wrapped

    def install_nodes():
        # 自定义节点在插件之后加载，因此每次任务开始时检查新增节点。
        for name, cls in list(nodes.NODE_CLASS_MAPPINGS.items()):
            field = getattr(cls, 'FUNCTION', None)
            if not field:
                continue
            try:
                descriptor = inspect.getattr_static(cls, field)
                function = descriptor.__func__ if isinstance(descriptor, (classmethod, staticmethod)) else descriptor
                if getattr(function, '_browser_timing', False):
                    continue
                if not callable(function):
                    continue
                wrapped = timed_function(function, name)
                if isinstance(descriptor, classmethod): wrapped = classmethod(wrapped)
                elif isinstance(descriptor, staticmethod): wrapped = staticmethod(wrapped)
                setattr(cls, field, wrapped)
            except Exception as exc:
                logger.warning('节点计时适配不可用 node=%s reason=%s', name, type(exc).__name__)

    original_init = comfy.samplers.KSAMPLER.__init__
    @functools.wraps(original_init)
    def sampler_init(self, sampler_function, *a, **kw):
        @functools.wraps(sampler_function)
        def algorithm(*params, **kwargs):
            session = active_session.get()
            ctx = get_executing_context()
            if session is None or session.closed or ctx is None or ctx.prompt_id != session.task_id:
                return sampler_function(*params, **kwargs)
            callback = kwargs.get('callback')
            seen = set()
            invalid = False
            def completed(info):
                nonlocal invalid
                value = info.get('i') if isinstance(info, dict) else None
                if isinstance(value, int) and value >= 0:
                    seen.add(value)
                else:
                    invalid = True
                if callback is not None:
                    return callback(info)
            kwargs['callback'] = completed
            with safe_span(session, 'sampling_loop', node_id=str(ctx.node_id), algorithm=getattr(sampler_function, '__name__', 'custom')) as span:
                try:
                    return sampler_function(*params, **kwargs)
                finally:
                    # 不假设回调数量等于配置步数；不可靠的自适应算法保留未知。
                    name = getattr(sampler_function, '__name__', '')
                    known = bool(seen) and seen == set(range(len(seen))) and not invalid and 'adaptive' not in name
                    span.update(iterations=len(seen), iterations_known=known)
        return original_init(self, algorithm, *a, **kw)
    comfy.samplers.KSAMPLER.__init__ = sampler_init

    def detail_hook(module, field, category):
        original = getattr(module, field, None)
        if not callable(original):
            logger.warning('内部计时适配不可用 field=%s', field)
            return
        @functools.wraps(original)
        def wrapped(*a, **kw):
            session = active_session.get()
            if session is None or session.closed or active_span.get() is None:
                return original(*a, **kw)
            with safe_span(session, category, operation=field):
                return original(*a, **kw)
        setattr(module, field, wrapped)
    detail_hook(comfy.model_management, 'load_models_gpu', 'device_preparation')
    detail_hook(comfy.utils, 'load_torch_file', 'resource_read')
    detail_hook(comfy.sd, 'load_lora_for_models', 'lora_application')
    detail_hook(comfy.sd, 'load_checkpoint_guess_config', 'model_loading')
    detail_hook(comfy.sd, 'load_diffusion_model', 'model_loading')
    detail_hook(comfy.sd, 'load_clip', 'model_loading')

    original_put = execution.PromptQueue.put
    @functools.wraps(original_put)
    def put(self, item):
        # 同一锁保护提交与开始读取，避免入队和出队之间遗漏时间戳。
        with _queue_lock:
            _queued[item[1]] = time.perf_counter_ns()
            if len(_queued) > 10000:
                _queued.pop(next(iter(_queued)))
            try:
                return original_put(self, item)
            except BaseException:
                _queued.pop(item[1], None)
                raise
    execution.PromptQueue.put = put

    original_execute = execution.PromptExecutor.execute
    original_returns = execution.get_output_from_returns
    @functools.wraps(original_returns)
    def output_returns(*a, **kw):
        result = original_returns(*a, **kw)
        session = active_session.get()
        if session is not None:
            try:
                root = os.path.realpath(folder_paths.get_output_directory())
                for item in result[1].get('images', []):
                    if item.get('type') != 'output': continue
                    file = os.path.realpath(os.path.join(root, item.get('subfolder', ''), item['filename']))
                    if os.path.commonpath([root, file]) == root:
                        identity = fingerprint(file)
                        with storage.pending_lock:
                            storage.pending_outputs[file] = (session.task_id, identity)
            except Exception as exc:
                logger.warning('生成计时输出关联失败 reason=%s', type(exc).__name__)
        return result
    execution.get_output_from_returns = output_returns
    @functools.wraps(original_execute)
    def execute(self, prompt, prompt_id, extra_data=None, execute_outputs=None):
        install_nodes()
        with _queue_lock:
            queued = _queued.pop(prompt_id, None)
        session = Session(prompt_id, prompt, queued)
        token = active_session.set(session)
        parent_token = active_span.set(None)
        success = False
        try:
            result = original_execute(self, prompt, prompt_id, extra_data or {}, execute_outputs or [])
            success = bool(self.success)
            return result
        finally:
            end = time.perf_counter_ns()
            active_session.reset(token)
            active_span.reset(parent_token)
            try:
                for event, info in getattr(self, 'status_messages', []):
                    if event == 'execution_cached': session.cached.update(str(x) for x in info.get('nodes', []))
                record = session.finish(success, end)
                if any(event == 'execution_interrupted' for event, _ in getattr(self, 'status_messages', [])):
                    record['status'] = 'interrupted'
                executed = {s['node_id'] for s in record['spans'] if s.get('kind') == 'node' and s['status'] == 'complete'}
                outputs = []
                root = os.path.realpath(folder_paths.get_output_directory())
                for node_id, output in getattr(self, 'history_result', {}).get('outputs', {}).items():
                    if str(node_id) not in executed:
                        continue
                    for item in output.get('images', []):
                        if item.get('type') != 'output': continue
                        file = os.path.realpath(os.path.join(root, item.get('subfolder', ''), item['filename']))
                        if os.path.commonpath([root, file]) != root: continue
                        try:
                            identity = fingerprint(file)
                            with storage.pending_lock:
                                captured = storage.pending_outputs.get(file)
                            if captured == (session.task_id, identity):
                                outputs.append((file, str(node_id), identity))
                        except OSError:
                            record['coverage_issues'].append('output_missing:' + str(node_id))
                storage.store.persist(record, outputs, embed=not args.disable_metadata)
            except Exception:
                logger.exception('生成计时持久化失败 task=%s', prompt_id)
            finally:
                with storage.pending_lock:
                    for file, (task, _) in list(storage.pending_outputs.items()):
                        if task == prompt_id:
                            storage.pending_outputs.pop(file, None)
    execution.PromptExecutor.execute = execute
    _installed = True
    logger.info('ComfyUI Browser 生成计时已启用，结构版本=1')
