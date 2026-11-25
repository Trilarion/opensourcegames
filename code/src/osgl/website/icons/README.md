# Website icons

The icons of the website icon font (`code/src/osgl/website/static/css/fonts/osgl.ttf` and `osgl.woff`, CSS classes
`icon-*` in `osgl.min.css`). Each icon is an unmodified (apart from the Font Awesome conversion below) SVG file from an
upstream icon set, named like its CSS class. The font is built from these files with `code/scripts/build_icon_font.py`
(run inside `code/` with `PYTHONPATH=src`, requires fontTools), which also contains the code points.

The font replaces an earlier font that was made with [IcoMoon](https://icomoon.io/app) and whose project file was lost.
The code points of that font are kept. Most icons were identified in their upstream sets by comparing outlines and
look the same as before. The logos are the current versions of Simple Icons (except Windows, which is not part of
Simple Icons anymore), and the icons for the genres Board and Sports are replacements of icons whose origin could not
be found.

This folder is not copied to the website.

## Adding or changing an icon

1. Put the SVG file (only `<path>` elements, no transforms) into this folder, named like the CSS class.
2. Add the name and a free code point (private use area) to `ICONS` in `code/scripts/build_icon_font.py` and run it.
3. Add the `.icon-<name>:before` rule to `osgl.min.css` and change the cache busting query string of the font urls.
4. Add the icon to the table below and, for a new set, the source and license.

## Icons

| File                 | Code point | CSS class             | Set                   | Upstream icon           | Used for                                |
|----------------------|------------|-----------------------|-----------------------|-------------------------|-----------------------------------------|
| `android.svg`        | U+EAC0     | `icon-android`        | Simple Icons          | android                 | platform Android                        |
| `appleinc.svg`       | U+EABE     | `icon-appleinc`       | Simple Icons          | apple                   | platform macOS                          |
| `attach_money.svg`   | U+EAC3     | `icon-attach_money`   | Material Icons        | editor/attach_money     | keyword "content commercial"            |
| `bitbucket.svg`      | U+E905     | `icon-bitbucket`      | Simple Icons          | bitbucket               | Bitbucket links                         |
| `book.svg`           | U+E919     | `icon-book`           | Font Awesome 4.7.0    | book (U+F02D)           | genre Visual novel                      |
| `brightness_3.svg`   | U+E914     | `icon-brightness_3`   | Material Icons        | image/brightness_3      | state inactive                          |
| `car.svg`            | U+F1B9     | `icon-car`            | Font Awesome 4.7.0    | car (U+F1B9)            | genre Game engine                       |
| `chess.svg`          | U+E91F     | `icon-chess`          | Material Symbols      | chess_knight            | genre Board                             |
| `child.svg`          | U+F1AE     | `icon-child`          | Font Awesome 4.7.0    | child (U+F1AE)          | navigation                              |
| `device_unknown.svg` | U+E913     | `icon-device_unknown` | Material Icons        | hardware/device_unknown | unknown platform                        |
| `dice.svg`           | U+E915     | `icon-dice`           | IcoMoon Free          | 022-dice                | genre Adventure, navigation             |
| `directions_run.svg` | U+E922     | `icon-directions_run` | Material Icons        | maps/directions_run     | genre Platform                          |
| `earth.svg`          | U+E9CA     | `icon-earth`          | IcoMoon Free          | 203-earth               | platform Web, navigation                |
| `filter.svg`         | U+EA5B     | `icon-filter`         | IcoMoon Free          | 348-filter              | navigation                              |
| `fort-awesome.svg`   | U+F286     | `icon-fort-awesome`   | Font Awesome 4.7.0    | fort-awesome (U+F286)   | genre Strategy                          |
| `github.svg`         | U+EAB0     | `icon-github`         | Simple Icons          | github                  | GitHub links, navigation                |
| `gitlab.svg`         | U+E906     | `icon-gitlab`         | Simple Icons          | gitlab                  | GitLab links                            |
| `graduation-cap.svg` | U+F19D     | `icon-graduation-cap` | Font Awesome 4.7.0    | graduation-cap (U+F19D) | genre Educational                       |
| `heart.svg`          | U+F004     | `icon-heart`          | Font Awesome 4.7.0    | heart (U+F004)          | navigation                              |
| `home.svg`           | U+E90A     | `icon-home`           | IcoMoon Free          | 001-home                | navigation                              |
| `ios.svg`            | U+E901     | `icon-ios`            | Simple Icons          | ios                     | platform iOS                            |
| `language.svg`       | U+E90D     | `icon-language`       | Font Awesome 4.7.0    | language (U+F1AB)       | navigation                              |
| `laptop.svg`         | U+E90C     | `icon-laptop`         | Font Awesome 4.7.0    | laptop (U+F109)         | navigation                              |
| `library.svg`        | U+E921     | `icon-library`        | IcoMoon Free          | 034-library             | Internet Archive links, genre Library   |
| `lightbulb.svg`      | U+EAC5     | `icon-lightbulb`      | Material Icons        | action/lightbulb        | navigation                              |
| `lock_open.svg`      | U+EAC4     | `icon-lock_open`      | Material Icons        | action/lock_open        | keywords "content open", "content free" |
| `music.svg`          | U+E91A     | `icon-music`          | IcoMoon Free          | 018-music               | genre Music                             |
| `new-tab.svg`        | U+EA7E     | `icon-new-tab`        | IcoMoon Free          | 383-new-tab             | external links                          |
| `pacman.svg`         | U+E916     | `icon-pacman`         | IcoMoon Free          | 023-pacman              | genre Arcade                            |
| `pencil.svg`         | U+E907     | `icon-pencil`         | IcoMoon Free          | 006-pencil              | navigation                              |
| `price-tag.svg`      | U+E935     | `icon-price-tag`      | IcoMoon Free          | 054-price-tag           | navigation                              |
| `puzzle-piece.svg`   | U+F12E     | `icon-puzzle-piece`   | Font Awesome 4.7.0    | puzzle-piece (U+F12E)   | genre Puzzle                            |
| `rocket1.svg`        | U+F135     | `icon-rocket1`        | Font Awesome 4.7.0    | rocket (U+F135)         | genre Simulation                        |
| `search.svg`         | U+F002     | `icon-search`         | Font Awesome 4.7.0    | search (U+F002)         | navigation, search                      |
| `soccer-court.svg`   | U+E91D     | `icon-soccer-court`   | Material Design Icons | soccer-field            | genre Sports                            |
| `sourceforge.svg`    | U+E904     | `icon-sourceforge`    | Simple Icons          | sourceforge             | SourceForge links                       |
| `spades.svg`         | U+E91B     | `icon-spades`         | IcoMoon Free          | 024-spades              | genre Cards                             |
| `stack.svg`          | U+E92E     | `icon-stack`          | IcoMoon Free          | 047-stack               | genre Framework                         |
| `star.svg`           | U+F005     | `icon-star`           | Font Awesome 4.7.0    | star (U+F005)           | top rated, navigation                   |
| `star-half-full.svg` | U+F123     | `icon-star-half-full` | Font Awesome 4.7.0    | star-half-o (U+F123)    | medium rated                            |
| `star-o.svg`         | U+F006     | `icon-star-o`         | Font Awesome 4.7.0    | star-o (U+F006)         | low rated                               |
| `stats-dots.svg`     | U+E99B     | `icon-stats-dots`     | IcoMoon Free          | 156-stats-dots          | navigation                              |
| `sun.svg`            | U+E9D4     | `icon-sun`            | IcoMoon Free          | 213-sun                 | state active                            |
| `target.svg`         | U+E9B3     | `icon-target`         | IcoMoon Free          | 180-target              | genre Action                            |
| `tux.svg`            | U+EABD     | `icon-tux`            | Simple Icons          | linux                   | platform Linux                          |
| `undo.svg`           | U+F0E2     | `icon-undo`           | Font Awesome 4.7.0    | undo (U+F0E2)           | navigation                              |
| `user-secret.svg`    | U+F21B     | `icon-user-secret`    | Font Awesome 4.7.0    | user-secret (U+F21B)    | genre Role playing                      |
| `users.svg`          | U+E972     | `icon-users`          | IcoMoon Free          | 115-users               | multiplayer, navigation                 |
| `wikipedia.svg`      | U+E900     | `icon-wikipedia`      | Simple Icons          | wikipedia               | Wikipedia links                         |
| `windows.svg`        | U+E903     | `icon-windows`        | Font Awesome 4.7.0    | windows (U+F17A)        | platform Windows                        |
| `wrench.svg`         | U+E991     | `icon-wrench`         | IcoMoon Free          | 146-wrench              | navigation                              |

## Sources and licenses

All files were downloaded on 2026-11-25 (`attach_money.svg` and `lock_open.svg` on 2026-11-23) from these pinned
versions:

- **IcoMoon Free** by Keyamoon, CC BY 4.0 (or GPL), see [LICENSE-IcoMoon-Free.txt](LICENSE-IcoMoon-Free.txt):
  `https://raw.githubusercontent.com/Keyamoon/IcoMoon-Free/d006795ede82361e1bac1ee76f215cf1dc51e4ca/SVG/<icon>.svg`
- **Font Awesome 4.7.0** by Dave Gandy, SIL OFL 1.1, see [LICENSE-OFL-1.1.txt](LICENSE-OFL-1.1.txt):
  `https://raw.githubusercontent.com/FortAwesome/Font-Awesome/v4.7.0/fonts/fontawesome-webfont.svg`.
  Font Awesome 4.7 has no single SVG files, the glyphs (selected by code point) are converted from this SVG font into
  SVG files with the view box `0 0 <advance width> 1792` (em size of the font) and the y-axis flipped (ascent 1536).
- **Simple Icons** 16.38.1, CC0 1.0, see [LICENSE-CC0-1.0-Simple-Icons.md](LICENSE-CC0-1.0-Simple-Icons.md):
  `https://raw.githubusercontent.com/simple-icons/simple-icons/16.38.1/icons/<icon>.svg`.
  The logos are trademarks of their respective owners.
- **Material Icons** (style "Material Icons", filled) by Google, Apache License 2.0, see
  [LICENSE-Apache-2.0.txt](LICENSE-Apache-2.0.txt):
  `https://raw.githubusercontent.com/google/material-design-icons/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/<icon>/materialicons/24px.svg`
- **Material Symbols** (style outlined) by Google, Apache License 2.0, see [LICENSE-Apache-2.0.txt](LICENSE-Apache-2.0.txt):
  `https://raw.githubusercontent.com/google/material-design-icons/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/symbols/web/<icon>/materialsymbolsoutlined/<icon>_24px.svg`
- **Material Design Icons** by Pictogrammers, Apache License 2.0 (Pictogrammers Free License), see
  [LICENSE-Apache-2.0.txt](LICENSE-Apache-2.0.txt):
  `https://raw.githubusercontent.com/Templarian/MaterialDesign/2424e748e0cc63ab7b9c095a099b9fe239b737c0/svg/<icon>.svg`

In the font, the view box of every icon is scaled to the font height (1024 units, ascent 960, descent -64), the
outlines are flipped vertically and converted to quadratic curves.
