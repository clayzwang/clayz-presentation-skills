"""Optional conversion of an existing native page field to a fixed footer cache.

The caller supplies an already-created dedicated native footer field and its
semantic page number. This preserves geometry, runs/fonts and field identity.
It does not compute page roles, add text overlays, renumber on reordering,
render, validate quality or establish application compatibility.
"""

def set_fixed_footer_number(shape, value):
    """Set one existing footer/page placeholder field to the fixed encoding.

    Accept only a dedicated text shape with one slidenum/footer field and a
    slide-number/footer placeholder. Unsupported shapes fail before mutation.
    Caller remains responsible for cover exclusion, number sequence, style,
    actual rendering and any later page changes. Automatic renumbering is not
    provided. Other object content and all geometry/style are untouched.
    """
    if type(value) is not int or value < 1:
        raise ValueError("value must be a positive integer, excluding bool")
    if not getattr(shape, "has_text_frame", False):
        raise ValueError("a dedicated native footer text shape is required")
    element = shape._element
    fields = element.xpath(".//a:fld")
    placeholders = element.xpath("./p:nvSpPr/p:nvPr/p:ph")
    if (len(fields) != 1 or len(placeholders) != 1
            or fields[0].get("type") not in {"slidenum", "footer"}
            or placeholders[0].get("type") not in {"sldNum", "ftr"}):
        raise ValueError("one known page/footer field and placeholder are required")
    texts = fields[0].findall("{http://schemas.openxmlformats.org/drawingml/2006/main}t")
    if len(texts) != 1 or any((item.text or "").strip()
                              for item in element.xpath(".//a:r/a:t")):
        raise ValueError("dedicated footer cache only; ordinary text is preserved")
    fields[0].set("type", "footer")
    placeholders[0].set("type", "ftr")
    texts[0].text = str(value)
    return {"mechanism": "editable-footer-field", "encoding": "footer",
            "cached_value": value, "automatic_renumbering": "not-provided",
            "application_behavior": "requires-actual-observation"}
