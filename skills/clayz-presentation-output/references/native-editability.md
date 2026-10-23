# Native editing defaults

Art selects the representation and objects from the content before applying these native editing properties. These APIs do not choose a medium, page partition or visible frame. Shape-owned labels apply after choosing a shape; registered connectors apply after choosing a node relationship. Capability-validation samples are not composition references.

Chart text has separate scopes: a broad chart default, axes, legends, a label group, an individual point label and custom rich-text runs cannot stand in for each other. Inspect the style of the text the current task needs; a default size does not establish every small label. In the currently used python-pptx 1.0.2 implementation, accessing `DataLabel.text_frame` obtains or creates custom text, which is a content-mode choice. Point position and whether a literal string updates with data are separate responsibilities. With fixed text, retain synchronization of data, text, selectors and mappings; the existing narrow wrap helper does not convert automatic values to literal text. Ordinary TextFrame settings do not govern chart internals. Current rendering and future GUI value/reflow behavior need their own evidence; no global no-wrap, font-size or annotation quota follows.

For selected Python-native text objects, use `packages.layout.native_text`. `write_native_text` preserves logical paragraphs without inserting measured visual breaks; `prepare_native_text` preserves existing emphasis runs. Defaults are native word wrapping and float `line_spacing=1.0`, with real paragraph-before/after spacing. Keep semantic paragraphs/items; local no-wrap or fixed-point exceptions use an explicit reason, never a global fixed-line-height mode.

Body defaults are left/top with 6pt after; label/header/button/node defaults are center/middle with 0pt after. Default margins are .12in sides and .06in top/bottom and can be explicitly overridden. Table cell anchoring is written on the cell. `semantic_table` defaults to native wrapping: planned `cells[].lines` are measurement estimates, not native paragraph or hard-break instructions. Headers center, numeric body cells align by their column role, and long body prose anchors top. Record real exported lines and unchanged capacity/glyph checks; do not relabel estimates as authored native lines or relax validators.

```python
from packages.layout import prepare_native_text, write_native_text
from packages.layout import refresh_rectangular_connector

# The current design has already selected these objects and relationships.
prepare_native_text(selected_body, role='body', line_spacing=1.15,
                    space_after_pt=8)
write_native_text(selected_labeled_shape, selected_label, role='label')
# After the caller moves a node, update its already selected connector.
refresh_rectangular_connector(selected_connector)  # Not GUI-following proof.
```

`add_text_shape` owns its label and geometry in one native object. Default to this for a labeled node; separate/group annotations only when independent placement requires it. Do not generally merge unrelated body text. Python adapter shape objects now consume their own `text`, with text options `textRole`, `wordWrap`, `lineSpacingMultiple`, `paraSpaceBeforePt/AfterPt`. Legacy `breakLine` aliases wordWrap; an existing manifest's explicit breakLine=False is retained as a legacy choice, not the new-content default. Explicit fixed spacing uses `lineSpacingPt` and `textFlowExceptionReason`. This implementation covers the Python route, not equivalent behavior in all adapters.

Node connectors register native IDs/sites and own their line-end arrows; coordinate-only decorative lines are not attachment. The narrow rectangle scope remains same-slide direct spTree, ordinary unrotated/unflipped rectangles. Check target identity, chosen site, stored geometry and the entry actually adopted by the application separately. Attachment success or a shorter route cannot replace Art’s selected relationship. In the current whole page, observe whether paths and labels still refer to the intended objects; preserve unknown relocation causes. `refresh_rectangular_connector` recalculates programmatically edited geometry from registered targets, without an automatic observer. GUI dragging in PowerPoint/WPS/LibreOffice needs actual evidence. Independent labels do not follow a line-end API. Whole direction blocks may use native arrow AutoShapes. See `examples/native_editability.py`; keep XML, rendering and GUI claims separate, with unavailable GUI checks deferred. No new approval, quality threshold, layout quota or reader cycle is introduced.

### Optional value labels with an independent format source

Verify value content and format source separately. Automatic values may retain independent numeric formats and point-label fonts without fixed literal value strings. Optional set_point_value_label_formats only writes numFmt on explicitly selected existing automatic point labels and rejects custom text; it leaves data/font/position siblings untouched and does not certify GUI updates. sourceLinked=false selects an explicit numeric format. Data edits still need synchronized chart caches and workbook values, followed by inspection of displayed labels and meaning-bearing colours/signs. Fixed text keeps its maintenance responsibility; this interface never silently converts it.

### Maintaining an explicitly selected connector set

When implementing an approved node-geometry change, optional refresh_rectangular_connectors prevalidates an explicit same-slide set of registered straight connectors before updating any selected path. It preserves target IDs/sites, own line ends and style; it does not discover all incident edges, move separate labels, choose different sites or seek shortest routes. This interface does not authorize moving locked Art nodes or reflowing text. Whole-page correspondence and target-application dragging still need their own evidence; unobserved behavior stays unverified.
