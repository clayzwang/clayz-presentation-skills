"""Apply configured custom metadata to an in-memory python-pptx presentation.

Call before the existing first save. This helper never saves, renders, changes
visible content, or supplies a quality verdict. It supports the current
metadata attribution mode and explicit string-valued custom properties.
"""
from xml.etree import ElementTree as ET

CUSTOM_NS = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VALUE_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
RELATIONSHIP = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.custom-properties+xml"


def apply_configured_custom_properties(presentation, config):
    """Create required properties, or retain an exactly matching existing part.

    Existing incomplete/conflicting metadata requires an explicit authoring
    decision; it is never silently overwritten or duplicated. Return value
    describes this in-memory operation, not application acceptance.
    """
    attribution = config["identity"]["attribution"]
    if attribution.get("mode") != "metadata":
        raise ValueError("This helper supports the explicit metadata mode only")
    expected = attribution.get("custom_properties")
    if not isinstance(expected, dict) or any(
        not isinstance(name, str) or not name.strip() or not isinstance(value, str)
        for name, value in expected.items()
    ):
        raise ValueError("Explicit nonempty names and string custom-property values required")
    if not expected:
        return {"action": "not-configured", "property_names": []}
    package = presentation.part.package
    try:
        current = package.part_related_by(RELATIONSHIP)
    except KeyError:
        current = None
    if current is not None:
        root = ET.fromstring(current.blob)
        if root.tag != "{" + CUSTOM_NS + "}Properties":
            raise ValueError("Existing custom-property root has a different identity")
        for name, value in expected.items():
            entries = [p for p in root.findall("{" + CUSTOM_NS + "}property")
                       if p.get("name") == name]
            actual = entries[0].find("{" + VALUE_NS + "}lpwstr") if len(entries) == 1 else None
            if actual is None or (actual.text or "") != value:
                raise ValueError("Existing custom property needs explicit reconciliation: " + name)
        return {"action": "retained", "property_names": list(expected)}
    # ElementTree escapes both names and values; do not interpolate XML text.
    root = ET.Element("{" + CUSTOM_NS + "}Properties")
    for pid, (name, value) in enumerate(expected.items(), 2):
        prop = ET.SubElement(root, "{" + CUSTOM_NS + "}property", {
            "fmtid": "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}",
            "pid": str(pid), "name": name})
        ET.SubElement(prop, "{" + VALUE_NS + "}lpwstr").text = value
    blob = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    ET.fromstring(blob)  # Reject invalid XML characters before mutating package.
    from pptx.opc.package import Part
    from pptx.opc.packuri import PackURI
    part = Part.load(PackURI("/docProps/custom.xml"), CONTENT_TYPE, package, blob)
    package.relate_to(part, RELATIONSHIP)
    return {"action": "created", "property_names": list(expected)}
