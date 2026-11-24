"""Explicit chart typefaces for python-pptx authoring.

Call after authoring chart, axis, legend and label styles. This writes the
chosen family; it does not choose a font, change sizes, or certify rendering.
"""


def bind_chart_typeface(chart, family):
    """Bind existing DrawingML run/default-run styles without skipping siblings.

    lxml's live depth-first iterator can lose later style targets while their
    children are removed/replaced. Freeze targets before making any mutation.
    Styles created after this call need another authoring call. Native reopen,
    font-file identity and visible labels remain separate observations.
    """
    from pptx.oxml.xmlchemy import OxmlElement

    if not isinstance(family, str) or not family.strip() or family != family.strip():
        raise ValueError('Pass the exact nonempty task font family')
    root = getattr(chart, '_chartSpace', None)
    if root is None:
        raise TypeError('Pass a python-pptx Chart, not a shape or text frame')
    targets = [element for element in list(root.iter())
               if element.tag in {OxmlElement('a:rPr').tag,
                                  OxmlElement('a:defRPr').tag,
                                  OxmlElement('a:endParaRPr').tag}]
    font_tags = [OxmlElement('a:' + script).tag for script in ('latin', 'ea', 'cs')]
    for target in targets:
        for tag, script in zip(font_tags, ('latin', 'ea', 'cs')):
            for old in list(target):
                if old.tag == tag:
                    target.remove(old)
            element = OxmlElement('a:' + script)
            element.set('typeface', family)
            target.append(element)
    return {'family': family, 'styles_authored': len(targets),
            'scripts_authored': ['latin', 'ea', 'cs'],
            'scope': 'Existing chart text styles only; no font or pixel acceptance.'}
