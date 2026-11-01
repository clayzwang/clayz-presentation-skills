"""Measured wrapping with atomic finance tokens and Chinese punctuation rules.

Does not change wording or shrink type. Oversize atoms return to Art.
"""
import re

ATOM = re.compile(r"\d{4}-\d{2}-\d{2}|[+−-]?\d[\d,]*(?:\.\d+)?%?|[A-Za-z][A-Za-z0-9]*(?:[-_/.][A-Za-z0-9]+)*|.")
CLOSING = set('，。、；：？！）》】〕〉」』,.!?:;%)]}')
OPENING = set('（《【〔〈「『([{')

FINANCE_TERMS = ("经营现金流", "固定资产", "自由现金流", "资产负债", "重要原因", "正值", "筹资活动", "受限现金", "营业利润", "资本开支", "净利润", "融资租赁", "十亿美元")

def wrap(text, font, width, *, minimum_tail_em=4, protected_terms=FINANCE_TERMS):
    if width <= 0:
        raise ValueError('non-positive usable text width')
    result=[]
    for paragraph in str(text).split('\n'):
        lines=[]; current=[]
        pattern = re.compile('|'.join(re.escape(v) for v in sorted(protected_terms,key=len,reverse=True))+'|'+ATOM.pattern) if protected_terms else ATOM
        for token in pattern.findall(paragraph):
            if font.getlength(token)>width:
                raise ValueError('unbreakable text atom exceeds width: '+token)
            if current and font.getlength(''.join(current)+token)>width:
                carry=[]
                if token[0] in CLOSING:
                    carry.insert(0,current.pop())
                    while current and current[-1][-1] in OPENING:
                        carry.insert(0,current.pop())
                elif current[-1][-1] in OPENING:
                    carry.insert(0,current.pop())
                if current: lines.append(current)
                current=carry
            if font.getlength(''.join(current)+token)>width:
                raise ValueError('punctuation-bound text exceeds width; revise Art')
            current.append(token)
        lines.append(current)
        # Rebalance a short final line, preserving exact original characters.
        tail_min=font.getlength('汉')*minimum_tail_em
        if len(lines)>1:
            while len(lines[-2])>1 and font.getlength(''.join(lines[-1]))<tail_min:
                moved=lines[-2][-1]
                if font.getlength(moved+''.join(lines[-1]))>width: break
                lines[-2].pop(); lines[-1].insert(0,moved)
            while lines[-2] and lines[-2][-1][-1] in OPENING:
                lines[-1].insert(0,lines[-2].pop())
        for line in lines:
            value=''.join(line)
            if font.getlength(value)>width:
                raise ValueError('rebalanced line exceeds width; revise Art')
            result.append(value)
    return result
