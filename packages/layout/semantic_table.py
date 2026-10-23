"""Content-measured native tables. Column roles describe data, not importance.

This is an authoring primitive, not a slide template. Art supplies the intended
comparison, explicit emphasis and available region; overflow returns to Art.
"""
from dataclasses import dataclass
from math import isfinite
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PIL import ImageFont
from packages.layout.text_flow import wrap


@dataclass(frozen=True)
class Column:
    label: str
    role: str = "text"  # text, number, period; never inferred from array position
    weight: float = 1.0


def data_cell_by_label(columns, rows, *, row_label_column, row_label, column_label):
    """Locate one explicitly chosen cell in the current data, excluding header.

    Labels match exactly; the identity column, target column and selected row
    must each resolve once. Unrelated duplicate labels are allowed. The result
    is a zero-based ``(data_row, column)`` for ``plan(emphasis=[...])``. Resolve
    again after changing rows or columns; this is not a persistent binding.

    Art chooses the member and metric. This helper neither infers importance
    from values nor normalizes, fuzzily matches or disambiguates labels.
    Existing explicit emphasis coordinates remain available.
    """
    labels = (row_label_column, row_label, column_label)
    if any(not isinstance(label, str) or not label.strip() for label in labels):
        raise ValueError("cell selection needs three nonempty string labels")
    if not columns or not rows:
        raise ValueError("cell selection needs columns and data rows")
    if any(len(row) != len(columns) for row in rows):
        raise ValueError("ragged table")

    def unique_column(label):
        matches = [i for i, column in enumerate(columns) if column.label == label]
        if len(matches) != 1:
            raise ValueError(f"column label must match exactly once: {label!r}")
        return matches[0]

    identity_column = unique_column(row_label_column)
    target_column = unique_column(column_label)
    matches = [i for i, row in enumerate(rows) if row[identity_column] == row_label]
    if len(matches) != 1:
        raise ValueError(f"row label must match exactly once: {row_label!r}")
    return matches[0], target_column


def plan(columns, rows, *, width, font_path, size=21, header_size=18,
         total_rows=(), emphasis=(), max_height=None, padding=(.17, .13),
         caption="", comparison="", protected_terms=None, native_width_scale=1.0,
         text_flow="native-wrap", line_spacing=1.0, exception_reason=None):
    # Optional calibration of usable line width for the actual target/font.
    # Physical columns, font size and padding remain Art's chosen values.
    if not isfinite(native_width_scale) or native_width_scale < 1:
        raise ValueError("native width scale must be finite and at least 1")
    if text_flow not in {"native-wrap", "authored-lines"}:
        raise ValueError("unknown table text_flow")
    if text_flow == "authored-lines" and not str(exception_reason or "").strip():
        raise ValueError("authored visual lines need an exception_reason")
    if isinstance(line_spacing, bool) or not isinstance(line_spacing, (int, float)) or not isfinite(line_spacing) or line_spacing <= 0:
        raise ValueError("line_spacing must be a positive multiple")
    if not columns or not rows or not comparison.strip() or not caption.strip():
        raise ValueError("table needs data, visible scope caption and comparison intent")
    if any(c.role not in {"text", "number", "period"} or c.weight <= 0 for c in columns):
        raise ValueError("invalid column semantics")
    if any(len(row) != len(columns) for row in rows):
        raise ValueError("ragged table")
    if any(i < 0 or i >= len(rows) for i in total_rows):
        raise ValueError("total row outside data")
    widths = [width * c.weight / sum(c.weight for c in columns) for c in columns]
    px, py = padding
    cells, heights = [], []
    for ri, row in enumerate([[c.label for c in columns]] + rows):
        line = []
        for ci, value in enumerate(row):
            pt = header_size if ri == 0 else size
            font = ImageFont.truetype(str(font_path), round(pt * 120 / 72))
            lines = wrap(value, font, (widths[ci] - 2 * px) * 120 / native_width_scale, **({"protected_terms":protected_terms} if protected_terms is not None else {}))
            # Numeric wrapping changes a comparison's reading; return to Art.
            if ri and columns[ci].role == "number" and len(lines) != 1:
                raise ValueError(f"numeric cell wraps: data row {ri-1}, column {ci}")
            line.append(dict(text=str(value), lines=lines, size_pt=pt,
                             align="center" if ri == 0 else "right" if columns[ci].role == "number" else "left",
                             vertical="middle" if ri == 0 else "top",
                             bold=ri == 0 or ri - 1 in total_rows or (ri - 1, ci) in emphasis,
                             header=ri == 0, total=ri - 1 in total_rows,
                             emphasis=(ri - 1, ci) in emphasis))
        cells.append(line)
        # A candidate estimate, not a prediction of native visual-line breaks.
        # Respond to the selected multiple before applying available height.
        heights.append(max(len(c["lines"]) * c["size_pt"] / 72 * 1.18 * line_spacing for c in line) + 2 * py)
    if max_height is not None and sum(heights) > max_height:
        raise ValueError(f"table needs {sum(heights):.2f}in, available {max_height:.2f}in; revise Art")
    return dict(columns=[vars(c) for c in columns], cells=cells, widths=widths,
                heights=heights, padding=list(padding), width=width,
                height=sum(heights), caption=caption, comparison=comparison,
                native_width_scale=native_width_scale,
                text_flow=text_flow, line_spacing=float(line_spacing),
                exception_reason=exception_reason,
                lines_role="measurement-estimate; not inserted native line breaks" if text_flow == "native-wrap" else "explicit authored visual lines")


def write(slide, spec, x, y, *, family="STKaiti", ink="172B3A",
          accent="185D72", line="CAD5DA", name="semantic-table"):
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
    from pptx.dml.color import RGBColor
    from pptx.oxml.xmlchemy import OxmlElement
    from packages.layout.native_text import write_native_text
    shape = slide.shapes.add_table(len(spec["cells"]), len(spec["widths"]),
                                   Inches(x), Inches(y), Inches(spec["width"]), Inches(spec["height"]))
    shape.name = name
    table = shape.table
    # Disable theme banding/first-column defaults; make every cell explicit.
    for attr in ("first_row", "first_col", "last_row", "last_col", "horz_banding", "vert_banding"):
        setattr(table, attr, False)
    for ci, width in enumerate(spec["widths"]):
        table.columns[ci].width = Inches(width)
    for ri, row in enumerate(spec["cells"]):
        table.rows[ri].height = Inches(spec["heights"][ri])
        for ci, item in enumerate(row):
            cell = table.cell(ri, ci)
            px, py = spec["padding"]
            cell.margin_left = cell.margin_right = Inches(px)
            cell.margin_top = cell.margin_bottom = Inches(py)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("E9F0F2" if item["header"] or item["total"] else "FFFFFF")
            mode = spec.get("text_flow", "native-wrap")
            # Measurement estimates remain in spec; native wrapping owns the
            # actual visual lines. A local explicit exception keeps old intent.
            value = item["text"] if mode == "native-wrap" else "\v".join(item["lines"])
            write_native_text(cell, value, family=family, size_pt=item["size_pt"],
                              color=accent if item["emphasis"] or item["total"] else ink,
                              bold=item["bold"], role="header" if item["header"] else "body",
                              horizontal=item["align"], vertical=item.get("vertical", "middle" if item["header"] else "top"),
                              margins_in={"left":px,"right":px,"top":py,"bottom":py},
                              line_spacing=spec.get("line_spacing", 1.0), space_after_pt=0,
                              word_wrap=mode == "native-wrap",
                              exception_reason=spec.get("exception_reason"))
            tc = cell._tc.get_or_add_tcPr()
            for side in ("L", "R", "T", "B"):
                ln = OxmlElement("a:ln" + side); ln.set("w", "6350")
                fill = OxmlElement("a:solidFill"); col = OxmlElement("a:srgbClr")
                col.set("val", line if side == "B" else "FFFFFF"); fill.append(col); ln.append(fill); tc.append(ln)
    return shape


def preview(draw, spec, x, y, *, scale=120, font_path, ink="172B3A", accent="185D72"):
    """Uses the same widths, line breaks, padding and row heights as native output."""
    cy = y * scale
    for ri, row in enumerate(spec["cells"]):
        cx = x * scale; height = spec["heights"][ri] * scale
        for ci, item in enumerate(row):
            width = spec["widths"][ci] * scale
            draw.rectangle((cx, cy, cx + width, cy + height), fill="#E9F0F2" if item["header"] or item["total"] else "white")
            font = ImageFont.truetype(str(font_path), round(item["size_pt"] * scale / 72))
            for li, value in enumerate(item["lines"]):
                tx = cx + spec["padding"][0] * scale
                if item["align"] == "right": tx = cx + width - spec["padding"][0] * scale - font.getlength(value)
                ty = cy + spec["padding"][1] * scale + li * item["size_pt"] / 72 * 1.18 * scale
                draw.text((tx, ty), value, font=font, fill="#" + (accent if item["emphasis"] or item["total"] else ink), anchor="lt", stroke_width=0)
            draw.line((cx, cy + height, cx + width, cy + height), fill="#CAD5DA", width=1)
            cx += width
        cy += height


def column_demands(columns, rows, *, font_path, size=23, header_size=18, padding=.17, width_scale=1.06):
    """Minimum single-line content widths; Art still chooses available width.

    Not every text cell must stay on one line. This is an inspectable diagnostic,
    not an automatic full-slide-width template.
    """
    if any(len(row)!=len(columns) for row in rows):raise ValueError('ragged table')
    demands=[]
    for ci,col in enumerate(columns):
        labels=[(col.label,header_size)]+[(str(row[ci]),size) for row in rows]
        demands.append(max(ImageFont.truetype(str(font_path),round(pt*120/72)).getlength(value)*width_scale/120+2*padding for value,pt in labels))
    return demands


def table_grid_boundary(table_shape, *, axis, boundary_index):
    """Return two integer-EMU endpoints of a current native table grid boundary.

    ``axis="column"`` returns a vertical boundary, ``axis="row"`` a horizontal
    one. Index 0 and the dimension's count are the outside edges. Read the
    returned or reopened shape after setting its actual grid dimensions.

    Only top-level, unrotated and unflipped slide tables with a consistent frame
    and positive grid are supported. This is read-only geometry: the caller
    chooses the semantic index and relation. A grid boundary through merged
    cells is not necessarily a visible cell border. No label/year inference,
    rendering, layout changes or quality judgment is performed.
    """
    from operator import index
    from pptx.shapes.shapetree import SlideShapes

    if axis not in {"column", "row"}:
        raise ValueError("axis must be column or row")
    if isinstance(boundary_index, bool):
        raise TypeError("boundary index must be an integer, not bool")
    boundary_index = index(boundary_index)
    if not getattr(table_shape, "has_table", False):
        raise ValueError("a native table shape is required")
    if not isinstance(table_shape._parent, SlideShapes):
        raise ValueError("only top-level slide tables are supported")
    xfrm = table_shape._element.xfrm
    if xfrm is None or table_shape.rotation != 0:
        raise ValueError("rotated or missing table transforms are unsupported")
    if any(xfrm.get(k) not in {None, "0", "false"} for k in ["flipH", "flipV"]):
        raise ValueError("flipped table transforms are unsupported")
    widths = [int(c.width) for c in table_shape.table.columns]
    heights = [int(r.height) for r in table_shape.table.rows]
    if any(v <= 0 for v in widths + heights):
        raise ValueError("table grid dimensions must be positive")
    if sum(widths) != int(table_shape.width) or sum(heights) != int(table_shape.height):
        raise ValueError("table frame and grid dimensions differ")
    dimension = widths if axis == "column" else heights
    if not 0 <= boundary_index <= len(dimension):
        raise ValueError("boundary index outside table grid")
    left, top = int(table_shape.left), int(table_shape.top)
    if axis == "column":
        x = left + sum(widths[:boundary_index])
        return (x, top), (x, top + sum(heights))
    y = top + sum(heights[:boundary_index])
    return (left, y), (left + sum(widths), y)
