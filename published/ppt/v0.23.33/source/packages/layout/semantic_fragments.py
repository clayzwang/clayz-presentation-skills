"""Materialize author-selected fragments of one unchanged Copy paragraph.

Optional construction primitive, not a semantic splitter or layout chooser.
It neither reads files nor saves, renders, measures or approves a deck.
"""
import math
import re

from pptx.dml.color import RGBColor
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Pt

from packages.layout.native_text import configure_frame, configure_paragraph
from packages.layout.text_emphasis import project_emphasis


def add_text_fragments(slide, text, fragments, *, node_id, font_family,
                       font_size_pt, color_hex, margins_emu, alignment,
                       emphasis_spans=()):
    """Add editable frames in source order at the author's chosen coordinates.

    ``fragments`` is an ordered list of dictionaries with exactly ``start``,
    ``end`` (half-open Unicode offsets) and ``box_emu`` (left, top, width,
    height). The intervals must partition the whole paragraph. Positions need
    not follow XML order; Art remains responsible for the visible reading path.

    All frames share the explicitly supplied base style. The author may style
    or group the returned shapes afterwards. Changes must preserve actual Copy
    text and its required scope, and remain subject to the ordinary checks.
    Existing emphasis projection preserves chosen spans across frame borders.

    Validation precedes adding shapes. Unexpected python-pptx errors are not
    rolled back. No claim is made about typography, capacity, target fonts,
    connector movement, native application behavior or professional quality.
    """
    if not isinstance(text, str) or not text or any(ord(c) < 32 for c in text):
        raise ValueError('One nonempty plain paragraph without control characters is required')
    if not isinstance(node_id, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', node_id):
        raise ValueError('An explicit node identity is required')
    if not isinstance(font_family, str) or not font_family.strip():
        raise ValueError('An explicit configured font family is required')
    if type(font_size_pt) not in (int, float) or not math.isfinite(font_size_pt) or font_size_pt <= 0:
        raise ValueError('An explicit positive font size is required')
    if not isinstance(color_hex, str) or not re.fullmatch(r'[0-9A-Fa-f]{6}', color_hex):
        raise ValueError('An explicit six-digit RGB color is required')
    if not isinstance(margins_emu, (tuple, list)) or len(margins_emu) != 4 or any(
            type(v) is not int or v < 0 for v in margins_emu):
        raise ValueError('Explicit nonnegative left/top/right/bottom margins are required')
    if alignment not in ('left', 'center', 'right', 'justify', 'inherit'):
        raise ValueError('An explicit supported alignment is required')
    if not isinstance(fragments, (list, tuple)) or not fragments:
        raise ValueError('Authored fragment intervals and positions are required')
    chosen, cursor = [], 0
    names = {shape.name for shape in slide.shapes}
    for index, fragment in enumerate(fragments, 1):
        if not isinstance(fragment, dict) or set(fragment) != {'start', 'end', 'box_emu'}:
            raise ValueError('Each fragment needs only start/end/box_emu')
        start, end, box = fragment['start'], fragment['end'], fragment['box_emu']
        if type(start) is not int or type(end) is not int or start != cursor or not start < end <= len(text):
            raise ValueError('Fragments must partition the unchanged paragraph in source order')
        if not isinstance(box, (list, tuple)) or len(box) != 4 or any(type(v) is not int for v in box):
            raise ValueError('An explicit integer EMU box is required')
        left, top, width, height = box
        if left < 0 or top < 0 or width <= 0 or height <= 0:
            raise ValueError('Fragment geometry must have a nonnegative origin and positive size')
        if margins_emu[0] + margins_emu[2] >= width or margins_emu[1] + margins_emu[3] >= height:
            raise ValueError('Margins leave no positive content area')
        name = node_id + '.fragment-' + str(index)
        if name in names:
            raise ValueError('Existing native object name conflicts: ' + name)
        chosen.append((start, end, tuple(box), name))
        names.add(name)
        cursor = end
    if cursor != len(text):
        raise ValueError('The complete original paragraph must be preserved')
    projected = project_emphasis(text, [text[a:b] for a, b, _, _ in chosen], emphasis_spans)
    result = []
    for (start, end, box, name), parts in zip(chosen, projected):
        shape = slide.shapes.add_textbox(*box)
        shape.name = name
        frame = shape.text_frame
        configure_frame(frame, fit='fixed', wrap=True)
        frame.margin_left, frame.margin_top, frame.margin_right, frame.margin_bottom = margins_emu
        paragraph = frame.paragraphs[0]
        configure_paragraph(paragraph, align=alignment)
        for part in parts:
            run = paragraph.add_run()
            run.text = part['text']
            run.font.name = font_family
            run.font.size = Pt(font_size_pt)
            run.font.bold = part['emphasis']
            run.font.color.rgb = RGBColor.from_string(color_hex)
            properties = run._r.get_or_add_rPr()
            for tag in ('ea', 'cs'):
                item = OxmlElement('a:' + tag)
                item.set('typeface', font_family)
                properties.append(item)
        result.append(dict(shape=shape, node_id=node_id, source_start=start,
                           source_end=end, object_name=name, geometry_emu=box))
    return result
