#!/usr/bin/env python3
"""Scope the existing neutral brief to the visible reading phase.

This does not judge content, change findings, or replace any reader gate.
"""
import argparse
import json
from pathlib import Path


TASKS = {
    'title': (
        '只根据提供的标题序列，说明你理解的主要判断、论证路线及关键对象范围。'
        '任务目的说明整份材料的主题，不要求标题独自回答整份材料的所有细节。'
        '完整历史节点、业务清单、数字证明、定义及专业算法可以属于正文。'
        '区分标题中的实际矛盾、误导或无法辨认的核心判断，与尚待正文解释的细节；'
        '后者如实记入不确定性，不因仅未展开细节就认定标题有缺陷。'
        '若主要判断本身无法理解或必须猜测对象、方向或范围，记录具体问题。'
        '独立报告实际理解，不推测未见正文已经充分，也不为通过而压下实际缺陷。'
    ),
    'content': (
        '阅读提供的完整可见文案，说明对主题、变化、依据与实际影响的理解。'
        '检查正文是否完成标题承诺和整份材料的任务，必要概念是否足以支持当前判断。'
        '区分影响该判断的解释缺口，与还希望了解更多专业细则的兴趣；'
        '后者可记入不确定性，不自动要求读者掌握完整算法。'
        '对稿中主动突出的重要变化，说明已看懂的原因或已披露的解释边界；'
        '仅能指出变化发生在哪个业务，不一定已回答变化原因。'
        '判断一个疑问时，说明缺少它会使哪个任务结论无法理解、容易误判或必须猜测；'
        '若仍能解释主要判断，进一步的技术细节可以保留为不确定性。'
        '这不预先认定疑问轻微，也不要求给出通过结论；实际缺口仍须如实记录。'
        '事实、范围、因果强度或必要解释存在问题时，保留具体发现。'
    ),
    'final': (
        '独立阅读提供的真实页面，说明你的理解、实际阅读路径和仍不清楚之处。'
        '观察结论入口、信息主次、数字与解释的对应、文字可读性、分组和跨页衔接。'
        '按实际可见证据报告问题；不要推定未见设计理由或研究笔记已经消除了问题。'
    ),
}


def scoped_brief(base, phase):
    if set(base) != {'audience', 'purpose', 'task'}:
        raise ValueError('Expected the existing three-field neutral reader brief')
    if any(not isinstance(v, str) or not v.strip() for v in base.values()):
        raise ValueError('Brief fields must be nonempty strings')
    return {**base, 'task': TASKS[phase]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--brief', type=Path, required=True)
    parser.add_argument('--phase', choices=TASKS, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = scoped_brief(json.loads(args.brief.read_text()), args.phase)
    if args.output.exists():
        if json.loads(args.output.read_text()) != result:
            raise ValueError('Existing scoped brief differs; preserve it and use a new revision')
    else:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'saved': str(args.output.resolve()), 'phase': args.phase,
                      'scope': 'Neutral task framing only; no quality verdict'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
