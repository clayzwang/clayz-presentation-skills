"""Art-approved emphasis preserves exact Copy and whole numeric tokens."""
import re
def validate_tokens(text,tokens):
    if not isinstance(tokens,list) or any(not isinstance(x,str) or not x for x in tokens):raise ValueError('Art emphasis must list nonempty tokens')
    for token in tokens:
        if not any(b for _,b in segments(text,[token])):raise ValueError('Art emphasis token absent or partial: '+token)
def segments(text,tokens):
    if not tokens:return [(text,False)]
    pattern=re.compile(r'(?<![\d.])(?:'+ '|'.join(re.escape(t) for t in sorted(set(tokens),key=len,reverse=True))+r')(?![\d.])')
    result=[];start=0
    for m in pattern.finditer(text):
        if m.start()>start:result.append((text[start:m.start()],False))
        result.append((m.group(),True));start=m.end()
    if start<len(text):result.append((text[start:],False))
    return result or [(text,False)]
