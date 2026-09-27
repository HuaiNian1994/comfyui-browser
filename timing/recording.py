"""隔离任务的单调时钟区间，保留嵌套关系及未覆盖原因。"""
from __future__ import annotations

import contextvars
import threading
import time
from contextlib import contextmanager

VERSION = 1
active_session = contextvars.ContextVar("browser_timing_session", default=None)
active_span = contextvars.ContextVar("browser_timing_span", default=None)


def union_duration(intervals):
    end = None
    total = 0
    for start, stop in sorted(intervals):
        if stop <= start:
            continue
        total += stop - max(start, end if end is not None else start) if end is None or stop > end else 0
        end = max(stop, end if end is not None else stop)
    return total


class Session:
    def __init__(self, task_id, prompt, queued_ns=None, clock=time.perf_counter_ns):
        self.clock = clock
        self.start = clock()
        self.task_id = task_id
        self.prompt = prompt
        self.queue_ms = max(0, (self.start - queued_ns) / 1e6) if queued_ns is not None else None
        self.spans = []
        self.cached = set()
        self.issues = []
        self.closed = False
        self.lock = threading.RLock()

    @contextmanager
    def span(self, category, **metadata):
        with self.lock:
            record = dict(id=str(len(self.spans)), parent_id=active_span.get(), category=category,
                          start_ms=(self.clock() - self.start) / 1e6, status="running", **metadata)
            self.spans.append(record)
        token = active_span.set(record["id"])
        try:
            yield record
        except BaseException:
            record["status"] = "failed"
            raise
        else:
            record["status"] = "complete"
        finally:
            record["end_ms"] = (self.clock() - self.start) / 1e6
            active_span.reset(token)

    def finish(self, success, total_end_ns=None):
        total_ms = ((total_end_ns if total_end_ns is not None else self.clock()) - self.start) / 1e6
        self.closed = True
        spans = self.spans
        for item in spans:
            end = item.get("end_ms", total_ms)
            item["elapsed_ms"] = max(0, end - item["start_ms"])
            children = [(max(item["start_ms"], c["start_ms"]), min(end, c.get("end_ms", end)))
                        for c in spans if c["parent_id"] == item["id"]]
            item["self_ms"] = max(0, item["elapsed_ms"] - union_duration(children))
            if item["status"] == "running":
                self.issues.append("unfinished_span:" + item["id"])
        nodes = [s for s in spans if s.get("kind") == "node"]
        executed = {s["node_id"] for s in nodes}
        failed = {s["node_id"] for s in nodes if s['status'] != 'complete'}
        sampling = [s for s in spans if s["category"] == "sampling_loop"]
        by_id = {s['id']: s for s in spans}
        def belongs_to(loop, call):
            parent = loop.get('parent_id')
            while parent in by_id:
                if parent == call['id']:
                    return True
                parent = by_id[parent].get('parent_id')
            return False
        for node in nodes:
            if node["category"] == "sampling" and not any(belongs_to(s, node) for s in sampling):
                self.issues.append("sampling_not_observed:" + node["node_id"])
        complete = not any(x.startswith(("sampling_", "unfinished_span", "unclassified_node")) for x in self.issues)
        iterations_known = all(s.get("iterations_known", False) for s in sampling)
        sampling_ms = sum(s["elapsed_ms"] for s in sampling) if complete else None
        iterations = sum(s.get("iterations", 0) for s in sampling) if complete and iterations_known else None
        node_states = [{"node_id": key, "class_type": node.get("class_type", ""),
                        "status": "failed" if key in failed else "executed" if key in executed else "cached" if key in self.cached else "not_executed"}
                       for key, node in self.prompt.items()]
        for node_id in sorted(executed - set(self.prompt)):
            call = next(s for s in nodes if s['node_id'] == node_id)
            node_states.append({'node_id': node_id, 'class_type': call.get('class_type', ''),
                                'status': 'failed' if node_id in failed else 'executed', 'dynamic': True})
        return {"version": VERSION, "recorder_version": 1, "task_id": self.task_id,
                "status": "success" if success else "failed", "clock": "monotonic_wall",
                "scope": "whole_task", "total_ms": total_ms, "queue_ms": self.queue_ms,
                "sampling_ms": sampling_ms, "iterations": iterations,
                "sampling_complete": complete, "iterations_complete": iterations_known,
                "spans": spans, "nodes": node_states, "coverage_issues": sorted(set(self.issues)),
                "unattributed_ms": max(0, total_ms - union_duration([(s["start_ms"], s.get("end_ms", total_ms)) for s in nodes]))}


def summary(payload, source="image"):
    """仅返回有界汇总；完整明细留在图片和计时存储中。"""
    import math
    if not isinstance(payload, dict) or payload.get("version") != VERSION or payload.get("status") != "success":
        return None
    def valid_number(value):
        try:
            return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
        except OverflowError:
            return False
    if not valid_number(payload.get("total_ms")):
        return None
    result = {"version": VERSION, "total_ms": payload["total_ms"], "source": source, "scope": "whole_task",
              "sampling_complete": payload.get('sampling_complete') is True,
              "iterations_complete": payload.get('iterations_complete') is True}
    value = payload.get("sampling_ms")
    if payload.get("sampling_complete") is True and valid_number(value) and value > 0:
        result["sampling_ms"] = value
        count = payload.get("iterations")
        if payload.get("iterations_complete") is True and isinstance(count, int) and not isinstance(count, bool) and count > 0:
            result["iterations"] = count
    return result
