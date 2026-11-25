"""
Builds the website icon font (osgl.ttf and osgl.woff in code/src/osgl/website/static/css/fonts) from the SVG icons
in code/src/osgl/website/icons.

Every icon is one SVG file, named like the CSS class without the "icon-" prefix (e.g. search.svg -> icon-search).
The view box of each SVG is scaled to the font height (1024 units, ascent 960, descent -64, like the earlier IcoMoon
font) and the advance width follows from the view box width, so the icons keep their intended padding and aspect
ratio. Only <path> elements are used, paths with fill="none" (bounding boxes of the Material icons) are skipped.

After adding, removing or changing icons, run this script, update the ".icon-<name>:before" rules in osgl.min.css
(see ICONS for the code points) and change the cache busting query string of the font urls there. Provenance and
licenses of the icons: code/src/osgl/website/icons/README.md. Requires fontTools.
"""

import re

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path

from osgl import constants as c
from osgl.utils import read_text

# icon name (SVG file name without .svg, CSS class without "icon-") -> code point in the font
# (code points of the earlier IcoMoon font are kept, so that the CSS rules do not change)
ICONS = {
    'android': 0xEAC0,
    'appleinc': 0xEABE,
    'attach_money': 0xEAC3,
    'bitbucket': 0xE905,
    'book': 0xE919,
    'brightness_3': 0xE914,
    'car': 0xF1B9,
    'chess': 0xE91F,
    'codeberg': 0xE908,
    'child': 0xF1AE,
    'device_unknown': 0xE913,
    'dice': 0xE915,
    'directions_run': 0xE922,
    'earth': 0xE9CA,
    'filter': 0xEA5B,
    'fort-awesome': 0xF286,
    'github': 0xEAB0,
    'gitlab': 0xE906,
    'graduation-cap': 0xF19D,
    'heart': 0xF004,
    'home': 0xE90A,
    'ios': 0xE901,
    'language': 0xE90D,
    'laptop': 0xE90C,
    'library': 0xE921,
    'lightbulb': 0xEAC5,
    'lock_open': 0xEAC4,
    'music': 0xE91A,
    'new-tab': 0xEA7E,
    'pacman': 0xE916,
    'pencil': 0xE907,
    'price-tag': 0xE935,
    'puzzle-piece': 0xF12E,
    'rocket1': 0xF135,
    'search': 0xF002,
    'soccer-court': 0xE91D,
    'sourceforge': 0xE904,
    'spades': 0xE91B,
    'stack': 0xE92E,
    'star': 0xF005,
    'star-half-full': 0xF123,
    'star-o': 0xF006,
    'stats-dots': 0xE99B,
    'sun': 0xE9D4,
    'target': 0xE9B3,
    'tux': 0xEABD,
    'undo': 0xF0E2,
    'user-secret': 0xF21B,
    'users': 0xE972,
    'wikipedia': 0xE900,
    'windows': 0xE903,
    'wrench': 0xE991,
}

ICONS_PATH = c.web_static_path.parent / 'icons'
FONTS_PATH = c.web_static_path / 'css' / 'fonts'

FAMILY_NAME = 'osgl'
UNITS_PER_EM = 1024
ASCENT = 960
DESCENT = -64
SPACE_WIDTH = 512
# fixed timestamp (seconds since 1904-01-01) of the font header, so that unchanged icons give identical font files
TIMESTAMP = 3_850_000_000


def read_icon(name: str) -> tuple[tuple[float, float, float, float], list[str]]:
    """
    Return the view box (min x, min y, width, height) and the path data of the visible paths of an icon SVG file.

    Repeated close path commands (e.g. "zz" at the end of the Codeberg logo) are reduced to one, the SVG path parser
    of fontTools fails on them otherwise.
    """
    text = read_text(ICONS_PATH / f'{name}.svg')
    view_box = re.search(r'<svg[^>]*\sviewBox="([^"]*)"', text)
    if not view_box:
        raise RuntimeError(f'Icon {name} has no view box')
    view_box = tuple(float(x) for x in view_box.group(1).replace(',', ' ').split())
    paths = [attributes for attributes in re.findall(r'<path\s([^>]*?)/?>', text) if 'fill="none"' not in attributes]
    path_data = [re.search(r'(?:^|\s)d="([^"]*)"', attributes).group(1) for attributes in paths]
    path_data = [re.sub(r'([zZ])(?:\s*[zZ])+', r'\1', data) for data in path_data]
    if not path_data:
        raise RuntimeError(f'Icon {name} contains no visible path')
    if re.search(r'<(?:circle|ellipse|rect|polygon|polyline|line|g|use)\b', text) or 'transform=' in text:
        raise RuntimeError(f'Icon {name} contains elements or transforms that are not supported, convert them to paths')
    return view_box, path_data


def make_glyph(view_box: tuple[float, float, float, float], path_data: list[str]):
    """
    Convert the paths of an icon into a TrueType glyph (quadratic curves, clockwise outer contours).

    The view box height is scaled to the font height, the top of the view box is placed on the ascent line.

    Returns the glyph and its advance width.
    """
    min_x, min_y, width, height = view_box
    scale = UNITS_PER_EM / height
    glyph_pen = TTGlyphPen(None)
    # the y flip reverses the contour direction, reverse it again for TrueType
    quadratic_pen = Cu2QuPen(glyph_pen, max_err=1.0, reverse_direction=True)
    transform_pen = TransformPen(quadratic_pen, (scale, 0, 0, -scale, -min_x * scale, ASCENT + min_y * scale))
    for data in path_data:
        parse_path(data, transform_pen)
    return glyph_pen.glyph(), round(width * scale)


def build_font():
    """
    Build the icon font from all icons in ICONS and return it.

    Raises a RuntimeError if the SVG files in the icon folder and the icons in ICONS differ.
    """
    files = {path.stem for path in ICONS_PATH.glob('*.svg')}
    if files != set(ICONS):
        raise RuntimeError(f'Icons without SVG file: {sorted(set(ICONS) - files)}, '
                           f'SVG files without icon: {sorted(files - set(ICONS))}')

    glyphs = {'.notdef': TTGlyphPen(None).glyph(), 'space': TTGlyphPen(None).glyph()}
    metrics = {'.notdef': (SPACE_WIDTH, 0), 'space': (SPACE_WIDTH, 0)}
    character_map = {0x20: 'space'}
    for name, code_point in sorted(ICONS.items(), key=lambda item: item[1]):
        glyph_name = f'uni{code_point:04X}'
        glyph, advance = make_glyph(*read_icon(name))
        glyphs[glyph_name] = glyph
        metrics[glyph_name] = (advance, 0)  # left side bearings are recalculated from the glyph bounds
        character_map[code_point] = glyph_name

    builder = FontBuilder(UNITS_PER_EM, isTTF=True)
    builder.font.recalcTimestamp = False
    builder.updateHead(created=TIMESTAMP, modified=TIMESTAMP)
    builder.setupGlyphOrder(list(glyphs))
    builder.setupCharacterMap(character_map)
    builder.setupGlyf(glyphs)
    glyf = builder.font['glyf']
    builder.setupHorizontalMetrics({name: (advance, glyf[name].xMin if glyf[name].numberOfContours else 0)
                                    for name, (advance, _) in metrics.items()})
    builder.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    builder.setupNameTable({
        'familyName': FAMILY_NAME,
        'styleName': 'Regular',
        'uniqueFontIdentifier': FAMILY_NAME,
        'fullName': FAMILY_NAME,
        'psName': FAMILY_NAME,
        'version': 'Version 2.0',
        'description': 'Icons of the Open Source Games List website, built by code/scripts/build_icon_font.py',
    })
    builder.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0,
                     usWinAscent=ASCENT, usWinDescent=-DESCENT, achVendID='NONE')
    builder.setupPost()
    builder.setupMaxp()
    print(f'{len(ICONS)} icons')
    return builder.font


def main():
    """
    Build the icon font and write osgl.ttf and osgl.woff.
    """
    font = build_font()
    font.save(FONTS_PATH / 'osgl.ttf')
    font.flavor = 'woff'
    font.save(FONTS_PATH / 'osgl.woff')
    print('osgl.ttf and osgl.woff written')


if __name__ == "__main__":
    main()
