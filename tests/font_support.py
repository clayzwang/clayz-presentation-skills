"""Portable metric-test font; this is not target-font render acceptance."""
import os
from PIL import ImageFont


def test_font_path():
    selected = os.environ.get('CLAYZ_TEST_FONT', 'DejaVuSans.ttf')
    return str(ImageFont.truetype(selected, 20).path)
