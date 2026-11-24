"""Explicit native text policies; content and geometry remain the caller's.

Optional authoring API. It neither wraps text nor measures overflow. These
settings do not establish rendered fidelity, editable capacity or app behavior.
"""
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN

_FIT = {"fixed": MSO_AUTO_SIZE.NONE,
        "shrink": MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE,
        "grow": MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT, "inherit": None}
_ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER,
          "right": PP_ALIGN.RIGHT, "justify": PP_ALIGN.JUSTIFY,
          "inherit": None}

def configure_frame(text_frame, *, fit="fixed", wrap=True):
    """Choose native auto-fit and wrapping without clearing existing content.

    Fixed disables both text shrink and shape growth. It can still overflow.
    Shrink/grow are explicit alternatives; inherit delegates to the document.
    No margin, font, paragraph, coordinates, field or table value is replaced.
    """
    if not isinstance(fit, str) or fit not in _FIT:
        raise ValueError("fit must be fixed, shrink, grow or inherit")
    if wrap is not None and type(wrap) is not bool:
        raise ValueError("wrap must be bool or None for inheritance")
    text_frame.auto_size = _FIT[fit]
    text_frame.word_wrap = wrap
    return {"fit": fit, "wrap": wrap}

def configure_paragraph(paragraph, *, align):
    """Set this paragraph's alignment; apply after adding each paragraph.

    Different roles may require different alignment. Existing runs, breaks,
    bullets, indentation, spacing, fonts, fields and text are preserved.
    This is not a deck-wide alignment command or an editable-quality check.
    """
    if not isinstance(align, str) or align not in _ALIGN:
        raise ValueError("align must be left, center, right, justify or inherit")
    paragraph.alignment = _ALIGN[align]
    return {"align": align}
