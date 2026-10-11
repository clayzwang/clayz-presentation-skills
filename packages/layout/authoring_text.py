"""Measured manual text lines with an explicit native-font width allowance.

1.06 is a conservative STKaiti/LibreOffice lab observation, not a universal font
model. Actual reopened PDF glyph bounds and images remain necessary.
"""
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PIL import ImageFont
from packages.layout.text_flow import wrap

def measure_lines(text, width, size, font_path, *, protected_terms, width_scale=1.06):
    if width_scale<1:raise ValueError('Native width scale cannot reduce measured glyph width')
    font=ImageFont.truetype(str(font_path),round(size*120/72))
    lines=wrap(text,font,(width-.08)*120/width_scale,protected_terms=protected_terms)
    return lines,len(lines)*size/72*1.18+.07+size/72*.12
