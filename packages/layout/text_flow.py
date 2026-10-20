"""Measured wrapping with atomic finance tokens and Chinese punctuation rules.

Does not change wording or shrink type. Oversize atoms return to Art.
"""
import re

ATOM = re.compile(r"\d{4}-\d{2}-\d{2}|[+−-]?\d[\d,]*(?:\.\d+)?%?|[A-Za-z][A-Za-z0-9]*(?:[-_/.][A-Za-z0-9]+)*|.")
CLOSING = set('，。、；：？！）》】〕〉」』,.!?:;%)]}')
OPENING = set('（《【〔〈「『([{')

FINANCE_TERMS = ("经营现金流", "固定资产", "自由现金流", "资产负债", "重要原因", "正值", "筹资活动", "受限现金", "营业利润", "资本开支", "净利润", "融资租赁", "十亿美元")

def _protected_tokens(paragraph, terms):
    """Compose literal author choices with existing atoms, never replace them.

    Overlapping constraints form one span. Adjacent choices remain separate
    break opportunities. This is not a language tokenizer or UAX14 engine.
    """
    spans = [match.span() for match in ATOM.finditer(paragraph)]
    for term in terms:
        start = paragraph.find(term)
        while start != -1:
            spans.append((start, start + len(term)))
            start = paragraph.find(term, start + 1)
    merged = []
    for start, end in sorted(spans):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return [paragraph[start:end] for start, end in merged]

def wrap(text, font, width, *, minimum_tail_em=4, protected_terms=FINANCE_TERMS):
    """Wrap unchanged text using existing atoms plus explicit literal groups.

    protected_terms applies to this call, at every literal occurrence. Choosing
    a substring cannot split an existing date, numeric or Latin atom. An atom
    or overlapping group wider than width raises; no shrinking or rewriting.
    """
    if width <= 0:
        raise ValueError('non-positive usable text width')
    if isinstance(protected_terms, (str, bytes)):
        raise ValueError('protected_terms must be a collection of literal strings')
    terms = tuple(protected_terms) if protected_terms is not None else ()
    if any(not isinstance(term, str) or not term.strip() or
           '\n' in term or '\r' in term for term in terms):
        raise ValueError('protected terms must be nonempty single-paragraph strings')
    result=[]
    for paragraph in str(text).split('\n'):
        lines=[]; current=[]
        for token in _protected_tokens(paragraph, terms):
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
                # A tail-length preference cannot introduce a prohibited
                # boundary that the first wrapping pass already avoided.
                # Move a punctuation-bound suffix as a unit, or retain the
                # existing legal (possibly short) tail when it will not fit.
                cut=len(lines[-2])-1
                while cut>0 and (lines[-2][cut][0] in CLOSING or
                                 lines[-2][cut-1][-1] in OPENING):
                    cut-=1
                if cut==0: break
                candidate=lines[-2][cut:]+lines[-1]
                if font.getlength(''.join(candidate))>width: break
                lines[-1]=candidate; lines[-2]=lines[-2][:cut]
        for line in lines:
            value=''.join(line)
            if font.getlength(value)>width:
                raise ValueError('rebalanced line exceeds width; revise Art')
            result.append(value)
    return result
