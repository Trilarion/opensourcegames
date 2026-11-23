"""
Adds the additional icons in code/src/osgl/website/icons (SVG, 24x24 Material icons) to the website icon font
(osgl.ttf and osgl.woff in code/src/osgl/website/static/css/fonts).

The font was originally exported from IcoMoon, but the IcoMoon project file is not available anymore. This script
extends the existing font files instead. It can be run repeatedly, existing glyphs at the given code points are
replaced. After running it, add/check the corresponding ".icon-<name>:before" rules in osgl.min.css and change the
cache busting query string of the font urls there. Provenance of the icons: code/src/osgl/website/icons/README.md.
"""

import re

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

from osgl import constants as c
from osgl.utils import read_text

# icon source file name (without .svg) -> code point in the font
ICONS = {
    'attach_money': 0xEAC3,
    'lock_open': 0xEAC4,
}

ICONS_PATH = c.web_static_path.parent / 'icons'
FONTS_PATH = c.web_static_path / 'css' / 'fonts'

# Material icons have a 24x24 view box. Like the Material icons already in the font (e.g. brightness_3), the view box
# is scaled to the em size (1024) with y = 22 on the baseline (y-axis flipped).
SCALE = 1024 / 24
BASELINE = 22


def read_icon_path(name):
    """
    Return the path data of the visible path of an icon SVG file.

    The Material icon SVGs contain an invisible bounding box path (fill="none") which is skipped.
    """
    text = read_text(ICONS_PATH / f'{name}.svg')
    paths = re.findall(r'<path([^>]*)/>', text)
    paths = [path for path in paths if 'fill="none"' not in path]
    if len(paths) != 1:
        raise RuntimeError(f'Icon {name} must contain exactly one visible path, found {len(paths)}')
    return re.search(r'\sd="([^"]*)"', paths[0]).group(1)


def make_glyph(path_data, glyph_set):
    """
    Convert SVG path data into a TrueType glyph (quadratic curves, clockwise outer contours).
    """
    glyph_pen = TTGlyphPen(glyph_set)
    # the y flip reverses the contour direction, reverse it again for TrueType
    quadratic_pen = Cu2QuPen(glyph_pen, max_err=1.0, reverse_direction=True)
    transform_pen = TransformPen(quadratic_pen, (SCALE, 0, 0, -SCALE, 0, BASELINE * SCALE))
    parse_path(path_data, transform_pen)
    return glyph_pen.glyph()


def extend_font(font):
    """
    Add or replace all icons of ICONS in the font.
    """
    glyph_order = font.getGlyphOrder()
    glyf = font['glyf']
    for name, code_point in ICONS.items():
        glyph_name = f'uni{code_point:04X}'
        glyph = make_glyph(read_icon_path(name), glyf)
        if glyph_name not in glyph_order:
            glyph_order.append(glyph_name)
        glyf[glyph_name] = glyph
        glyph.recalcBounds(glyf)
        font['hmtx'][glyph_name] = (1024, glyph.xMin)
        for table in font['cmap'].tables:
            if table.isUnicode():
                table.cmap[code_point] = glyph_name
        print(f'icon {name} -> U+{code_point:04X} ({glyph_name})')
    font.setGlyphOrder(glyph_order)


def main():
    """
    Extend osgl.ttf and write osgl.ttf and osgl.woff.
    """
    font = TTFont(FONTS_PATH / 'osgl.ttf', recalcTimestamp=False)
    extend_font(font)
    font.flavor = None
    font.save(FONTS_PATH / 'osgl.ttf')
    font = TTFont(FONTS_PATH / 'osgl.ttf', recalcTimestamp=False)
    font.flavor = 'woff'
    font.save(FONTS_PATH / 'osgl.woff')
    print('osgl.ttf and osgl.woff written')


if __name__ == "__main__":
    main()
