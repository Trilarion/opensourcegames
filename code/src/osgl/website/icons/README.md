# Additional website icons

The website icon font (`code/src/osgl/website/static/css/fonts/osgl.ttf` and `osgl.woff`, CSS classes `icon-*` in
`osgl.min.css`) was originally created with [IcoMoon](https://icomoon.io/app). The IcoMoon project file is not
available, so further icons are added from the SVG sources in this folder with `code/scripts/extend_icon_font.py`
(run inside `code/` with `PYTHONPATH=src`).

This folder is not copied to the website.

## Icons

| File               | Code point | CSS class            | Used for                                   |
|--------------------|------------|----------------------|--------------------------------------------|
| `attach_money.svg` | U+EAC3     | `icon-attach_money`  | keyword "content commercial" (dollar sign) |
| `lock_open.svg`    | U+EAC4     | `icon-lock_open`     | keywords "content open", "content free"    |

## Provenance

Both icons are unmodified copies of the [Material Icons](https://github.com/google/material-design-icons) by Google
(style "Material Icons" (filled), 24px), licensed under the Apache License, Version 2.0 (copy in
[LICENSE-Apache-2.0.txt](LICENSE-Apache-2.0.txt)). Downloaded on 2026-11-23 from the master branch:

- `attach_money.svg`: https://raw.githubusercontent.com/google/material-design-icons/master/src/editor/attach_money/materialicons/24px.svg
- `lock_open.svg`: https://raw.githubusercontent.com/google/material-design-icons/master/src/action/lock_open/materialicons/24px.svg

In the font, the outlines are only scaled to the em size of the font (24 units -> 1024 units), flipped vertically and
converted to quadratic curves.
