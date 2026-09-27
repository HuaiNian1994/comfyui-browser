"""独立读取真实验收图片，检查公式、工作流、动画和嵌入前摘要。"""
import argparse
import hashlib
import io
import json
import shutil
import struct
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from module_loader import load_module
containers = load_module('timing.containers')
storage = load_module('timing.storage')


def verify(output, cases):
    artifacts = ROOT / '.timing-e2e'
    isolated = artifacts / 'isolated'
    isolated.mkdir(exist_ok=True)
    results = []
    assert storage.store is None
    for case in cases:
        report = json.loads((artifacts / (case + '-result.json')).read_text(encoding='utf-8'))
        prompt = json.loads((artifacts / (case + '-prompt.json')).read_text(encoding='utf-8'))
        workflow = json.loads((artifacts / (case + '-workflow.json')).read_text(encoding='utf-8'))
        task_values = None
        for node_id, node_output in report['history']['outputs'].items():
            for item in node_output.get('images', []):
                path = output / item.get('subfolder', '') / item['filename']
                data = path.read_bytes()
                timing = containers.read_payload(data)
                assert timing and timing['task_id'] == report['task_id'], path
                assert timing['output_node_id'] == node_id
                loops = [s for s in timing['spans'] if s['category'] == 'sampling_loop']
                assert abs(sum(s['elapsed_ms'] for s in loops) - timing['sampling_ms']) < 0.0001
                assert sum(s['iterations'] for s in loops) == timing['iterations']
                values = [timing[k] for k in ('total_ms', 'sampling_ms', 'iterations')]
                if task_values is not None: assert values == task_values
                task_values = values
                fmt, chunks = containers.chunks(data)
                if fmt == 'PNG':
                    original = data[:8] + b''.join(raw for kind, payload, raw in chunks if not containers.is_timing_chunk(kind, payload))
                    with Image.open(io.BytesIO(data)) as im:
                        raw_prompt = im.info.get('prompt')
                        raw_workflow = im.info.get('workflow')
                    for kind, payload, _ in chunks:
                        if kind == b'comf':
                            key, _, value = payload.partition(b'\0')
                            if key == b'prompt': raw_prompt = value
                            if key == b'workflow': raw_workflow = value
                else:
                    # 本验收使用官方保存节点生成的新 WebP，原文件有 VP8X、无 XMP。
                    body = b'WEBP' + b''.join(containers.riff_chunk(kind, bytes([payload[0] & ~4]) + payload[1:]) if kind == b'VP8X' else raw
                                             for kind, payload, raw in chunks if kind != b'XMP ')
                    original = b'RIFF' + struct.pack('<I', len(body)) + body
                    with Image.open(io.BytesIO(data)) as im:
                        exif = im.getexif()
                        raw_prompt = exif[272][len('prompt:'):]
                        raw_workflow = exif[271][len('workflow:'):]
                assert json.loads(raw_prompt) == prompt
                assert json.loads(raw_workflow) == workflow
                original_verified = 'output' in timing
                if original_verified:
                    assert hashlib.sha256(original).hexdigest() == timing['output']['original_sha256']
                frames = []
                with Image.open(io.BytesIO(data)) as im:
                    for i in range(im.n_frames):
                        im.seek(i)
                        frames.append(hashlib.sha256(im.convert('RGB').tobytes()).hexdigest())
                    if path.name.startswith(('animation_', 'webp_')):
                        assert im.n_frames == 2 and frames[0] != frames[1]
                target = isolated / path.name
                shutil.copy2(path, target)
                summary, pending = storage.read_summary(target)
                assert summary['source'] == 'image' and not pending
                assert summary['total_ms'] == timing['total_ms']
                results.append({'case': case, 'file': path.name, 'task_id': timing['task_id'],
                                'total_ms': timing['total_ms'], 'sampling_ms': timing['sampling_ms'],
                                'iterations': timing['iterations'], 'average_s_it': timing['sampling_ms'] / timing['iterations'] / 1000 if timing['iterations'] else None,
                                'external_elapsed_ms': report['external_elapsed_ms'], 'frames': len(frames),
                                'original_sha256_verified': original_verified, 'copied_source': summary['source']})
    (artifacts / 'verification.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--cases', nargs='+', default=['cold', 'warm', 'batch', 'multi', 'cached', 'formats'])
    args = parser.parse_args()
    verify(args.output, args.cases)
