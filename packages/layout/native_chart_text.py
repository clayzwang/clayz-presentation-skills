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


def set_manual_legend_colors(swatch, text_frame, *, mark_color, text_color):
    """Style existing manual legend parts with two explicit color decisions.

    A mark's relative emphasis does not choose the identifying words' color.
    No geometry, font, contrast threshold or automatic palette is supplied.
    Equal colors are allowed when explicitly chosen. Inspect actual rendering
    and visible association separately; this reports authorship, not quality.
    """
    from pptx.dml.color import RGBColor

    def rgb(value):
        if not isinstance(value, str):
            raise ValueError('Pass an explicit six-digit RGB color')
        cleaned = value.lstrip('#')
        if len(cleaned) != 6:
            raise ValueError('Pass an explicit six-digit RGB color')
        return RGBColor.from_string(cleaned.upper())

    mark, text = rgb(mark_color), rgb(text_color)
    if not hasattr(swatch, 'fill') or not hasattr(text_frame, '_txBody'):
        raise TypeError('Pass the native swatch shape and label TextFrame')
    swatch.fill.solid()
    swatch.fill.fore_color.rgb = mark
    count = 0
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            run.font.color.rgb = text
            count += 1
    return {'mark_color': str(mark), 'text_color': str(text),
            'label_runs_authored': count,
            'scope': 'Existing manual swatch/label colors only; no legibility or semantic verdict.'}


def set_point_label_wrapping(chart, requests):
    """Set wrap only on explicitly selected, existing custom point labels.

    Each request supplies series_index, point_index, expected_text and
    word_wrap (True/False/None). All selectors and literal identities are
    checked before any mutation. None restores inheritance, not no-wrap.
    Existing text, runs, style/position, number caches and workbooks stay put;
    automatic labels are not converted to custom text. This uses python-pptx's
    existing TextFrame wrapping behavior, not a new layout engine.

    A no-wrap request can still overflow, collide or retain explicit breaks.
    Observe the actual chart and neighbours after native export. No fit,
    automatic label update, semantic correspondence or GUI verdict is returned.
    """
    from pptx.chart.chart import Chart
    from pptx.text.text import TextFrame

    if not isinstance(chart, Chart):
        raise TypeError('Pass a python-pptx Chart')
    if not isinstance(requests, (list, tuple)):
        raise TypeError('Pass explicit point-label requests as a list or tuple')
    prepared, seen = [], set()
    required = {'series_index', 'point_index', 'expected_text', 'word_wrap'}
    for item in requests:
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError('Each request needs exactly series_index, point_index, expected_text, word_wrap')
        si, pi = item['series_index'], item['point_index']
        if type(si) is not int or type(pi) is not int or si < 0 or pi < 0:
            raise ValueError('Indices must be nonnegative integers, excluding booleans')
        if si >= len(chart.series):
            raise ValueError('series_index is outside this chart')
        series = chart.series[si]
        if pi >= len(series.points):
            raise ValueError('point_index is outside this series')
        if (si, pi) in seen:
            raise ValueError('Select each point label only once per call')
        seen.add((si, pi))
        expected, choice = item['expected_text'], item['word_wrap']
        if not isinstance(expected, str) or not expected:
            raise ValueError('expected_text must be the existing nonempty literal label')
        if choice is not None and type(choice) is not bool:
            raise ValueError('word_wrap must be True, False or None')
        # DataLabel.text_frame can add rich text and remove adjacent spPr/txPr.
        # Bind the existing body directly, retaining all current label siblings.
        labels = series._element.xpath('./c:dLbls/c:dLbl')
        matches = [el for el in labels if el.xpath('./c:idx/@val') == [str(pi)]]
        if len(matches) != 1:
            raise ValueError('Selected custom point label must already exist once')
        rich = matches[0].xpath('./c:tx/c:rich')
        if len(rich) != 1 or len(rich[0].xpath('./a:bodyPr')) != 1:
            raise ValueError('Existing custom label needs one rich text body/bodyPr')
        tf = TextFrame(rich[0], chart)
        if tf.text != expected:
            raise ValueError('Selected point label text differs from expected_text')
        prepared.append((si, pi, expected, choice, tf, tf.word_wrap))
    observations = []
    for si, pi, expected, choice, tf, before in prepared:
        tf.word_wrap = choice
        observations.append({'series_index': si, 'point_index': pi,
                             'text': expected, 'previous_word_wrap': before,
                             'authored_word_wrap': tf.word_wrap})
    return {'selected_labels': observations,
            'scope': 'Explicit existing custom point-label wrapping only; no text/style/data/geometry mutation or layout-quality verdict.'}
