"""Use optional, inspectable knowledge-pack terms without rewriting Copy."""
import json,hashlib
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from packages.layout.text_flow import FINANCE_TERMS
def load_terms(pack, visible_text):
    path=Path(pack)/'finance-terms.json'
    if not path.exists():return tuple(FINANCE_TERMS),{'status':'default-terms','pack_terms':False}
    data=json.loads(path.read_text());terms=data.get('protected_terms')
    if data.get('contract')!='io.clayz.presentation.finance-terms/1.0' or not isinstance(terms,list) or any(not isinstance(t,str) or not t.strip() for t in terms):raise ValueError('Malformed knowledge text terms')
    selected=tuple(sorted(set(FINANCE_TERMS)|{t for t in terms if t in visible_text},key=lambda t:(-len(t),t)))
    return selected,{'status':'applied-to-visible-copy','path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'selected_terms':list(selected)}
