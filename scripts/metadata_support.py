"""生成维护清单，并检查当前 ComfyUI 的节点契约变化。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from metadata.registry import ATTRIBUTES, CONTRACTS, CONTRACT_PATH, DIRECT_FIELDS, NODES, PARSER_VERSION, TEXT_FIELDS, property_ids

DOCUMENT = ROOT / 'docs' / 'METADATA_SUPPORT.md'
RULES = {
    'sample': '读取采样字段并沿条件、模型、噪声、调度器和潜空间输入追踪；阶段步数单独推导。',
    'output': '从图片输入识别输出分支，多输出保留未确定关联。',
    'encoder': '沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。',
    'checkpoint': '按输出端口区分模型、内置编码器与内置 VAE；随机选模结果未保存时标未知。',
    'loader': '读取加载文件字段及显式设置，按资源端口追踪。',
    'lora': '读取启用项、名称及双权重，保留重复应用顺序。',
    'guider': '按输入角色追踪模型和正反向条件，保留多组 CFG。',
    'noise': '读取噪声种子或禁用噪声状态；种子以字符串返回。',
    'sigmas': '追踪上游调度设置，并按切分端口计算可以确定的序列长度。',
    'scheduler': '读取调度设置；配置步数和下游阶段步数分别展示。',
    'sampler': '读取采样器名称或专用采样器类型及参数。',
    'primitive': '读取标量输出；特殊随机占位值标未知。',
    'config': '按固定输出端口映射步数、CFG、采样器和调度器。',
    'context': '按上下文输出端口、字段覆盖关系追踪；选择结果依赖运行时非空值时标未知。',
    'transform': '按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。',
    'auxiliary': '保留辅助模型文件和作用设置。',
    'lora_stack': '组合显式 LoRA 列表；随机和循环选取结果未保存时标未知。',
    'value': '按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。',
    'external': '记录外部数据引用，内容未嵌入执行图时标未知。',
}


def render_document():
    baseline = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    lines = ['# 图片属性与节点支持清单', '', '由 `python scripts/metadata_support.py --write` 从节点注册表生成。', '',
             f'解析版本：{PARSER_VERSION}；契约快照：{len(CONTRACTS)} 个节点；登记适配：{len(NODES)} 个节点。', '',
             '## 适配基线', '', '| 来源 | 版本 / 源码指纹 |', '|---|---|']
    for name, version in baseline['versions'].items():
        lines.append(f'| {name} | `{json.dumps(version, ensure_ascii=False) if isinstance(version, dict) else version}` |')
    lines += ['', '扩展以安装包发布版本及 Python 源码 SHA-256 标识；运行时使用项目内冻结规则。', '',
              '## 数据与展示约定', '',
              '- 读取 PNG 文本、APNG comf 块、WebP EXIF 中的执行图。其他现有图片格式显示基础信息和封装支持状态。',
              '- 值区分已记录、确定性推导、未知；每项保留节点、字段和传递来源。',
              '- 正反向由条件连接用途确定；多输出关联未确定时旧提示词摘要为空。',
              '- 采样种子属于采样节点；批量工作流的单张图片种子以保存证据为准。',
              '- 图内资源名表示执行图配置；外部模型内容、输入图片像素、通配词库和运行时选择结果由未知状态说明。',
              '- 模型与采样资源沿各自端口追踪；注册之外的节点返回局部诊断。', '',
              '## 属性 → 节点', '', '| 属性 | 标识 | 直接适配节点（传递节点见下表） |', '|---|---|---|']
    for attr, (_, label, _) in ATTRIBUTES.items():
        names = [name for name,spec in NODES.items() if attr in property_ids(name,spec)]
        lines.append(f'| {label} | `{attr}` | '+', '.join(f'`{name}`' for name in sorted(names))+' |')
    lines += ['', '## 节点 → 属性与端口', '', '| 节点 / 来源 | 属性 | 输入字段 | 输出端口 | 解析规则与限制 |', '|---|---|---|---|---|']
    for name, spec in sorted(NODES.items()):
        c = CONTRACTS[name]
        inputs = ', '.join(f'`{f}`' for f in c['inputs'])
        outputs = ', '.join(f'{i}: `{t}`' for i,t in enumerate(c['outputs']))
        attrs = ', '.join(f'`{a}`' for a in property_ids(name,spec)) or '向消费节点传递属性'
        lines.append(f"| `{name}`<br>{c['module']} | {attrs} | {inputs} | {outputs} | {RULES[spec['kind']]}<br>{spec['limitation']}<br>测试：`{spec['tests'][0]}` |")
    lines += ['', '## 节点运行计时', '', '| 节点 | 计时类别 | 内部计时范围 |', '|---|---|---|']
    for name, spec in sorted(NODES.items()):
        timing = spec['timing']
        lines.append(f"| `{name}` | `{timing['category']}` | {timing['limitation']} |")
    lines += ['', '## 核查与测试', '',
              '- `python scripts/metadata_support.py --check`：检查生成清单与注册表一致。',
              '- `python scripts/metadata_support.py --compare-url http://127.0.0.1:8000`：检查节点增减、输入类型和输出端口变化。',
              '- `python -m unittest discover -s tests -v`：验证属性、阶段、图片封装、任务状态与数据库并发。',
              '- `tests/test_execution_graph.py` 覆盖节点语义与连接；`tests/test_image_utils.py` 覆盖封装；`tests/test_metadata_indexer.py` 覆盖缓存提交。',
              '- 新增节点适配时更新注册表、契约快照、语义测试，再重新生成本清单。', '',
              '## 范围', '',
              '快照同时保留官方在线服务、视频、音频和三维节点用于版本对比。本轮登记以本地图片参数及其传递节点为对象，未登记节点通过侧边栏诊断显示。', '']
    return '\n'.join(lines)


def compact_contract(raw):
    return {'module': raw.get('python_module', ''),
            'inputs': {name: {'type': 'COMBO' if isinstance(value[0], list) else value[0], 'optional': section == 'optional'}
                       for section in ('required', 'optional') for name,value in raw.get('input', {}).get(section, {}).items()},
            'outputs': ['COMBO' if isinstance(value, list) else value for value in raw.get('output', [])],
            'output_names': raw.get('output_name', []), 'output_node': raw.get('output_node', False)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--compare-url')
    args = parser.parse_args()
    document = render_document()
    if args.write:
        DOCUMENT.parent.mkdir(exist_ok=True)
        DOCUMENT.write_text(document, encoding='utf-8')
        print(f'已生成清单：{len(NODES)} 个登记节点')
    if args.check:
        if not DOCUMENT.exists() or DOCUMENT.read_text(encoding='utf-8') != document:
            print('清单需要重新生成'); return 1
        print('清单与注册表一致')
    if args.compare_url:
        with urlopen(args.compare_url.rstrip('/') + '/object_info', timeout=15) as response:
            current = {k: compact_contract(v) for k,v in json.load(response).items()}
        differences = {'added': sorted(set(current)-set(CONTRACTS)), 'removed': sorted(set(CONTRACTS)-set(current)),
                       'changed': sorted(k for k in set(current)&set(CONTRACTS) if current[k] != CONTRACTS[k])}
        print(json.dumps(differences, ensure_ascii=False, indent=2))
        return int(any(differences.values()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
