"""Restore a native slide-number field without cloning slide-local identity.

Use lxml elements from the destination/source p:sp. Source and target must share
approved text-box geometry/style outside txBody. No relationships are copied.
"""
from copy import deepcopy
from lxml import etree

P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def restore_slide_number_field(target, source):
    """Replace only txBody; preserve target cNvPr id/name, geometry and position."""
    if target.tag != P + 'sp' or source.tag != P + 'sp':
        raise ValueError('Only native text shapes are supported')
    source_body, target_body = source.find(P + 'txBody'), target.find(P + 'txBody')
    if source_body is None or target_body is None:
        raise ValueError('Both text bodies are required')
    fields = source_body.findall('.//' + A + 'fld')
    if len(fields) != 1 or fields[0].get('type') != 'slidenum':
        raise ValueError('Source must contain exactly one automatic slide-number field')
    if any(k.startswith(R) for e in source_body.iter() for k in e.attrib):
        raise ValueError('Relationship-bearing text bodies are unsupported')
    for tag in ('spPr', 'style'):
        left, right = target.find(P + tag), source.find(P + tag)
        if (left is None) != (right is None) or (left is not None and etree.tostring(left, method='c14n') != etree.tostring(right, method='c14n')):
            raise ValueError('Approved geometry/style differs: ' + tag)
    # Do not replace the containing shape: cNvPr IDs are local to its slide.
    target.replace(target_body, deepcopy(source_body))
    return target
