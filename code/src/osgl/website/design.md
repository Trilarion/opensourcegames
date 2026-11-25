# Design of the static website

The website is built with the parsed entries, developers and inspirations read in Python, then a script uses Jinja templates
to generate html pages which use a CSS framework and Javascript data tables. The finished site is pushed to a suitable
location, only changed content would need to be copied though.

## Pages

index.html - overview of all pages
contribute.html - information how to edit and contribute

games/index.html - overview of all games (with recommended keywords) sorted alphabetically
games/table.html - overview of all games as table
games/[A-Z].html - entries sorted by title and categorized alphabetically
games/genres.html - all games in a certain genre
games/languages.html - all games with a certain language
games/platform.html - all games with a certain platform
games/dependencies.html - all games with a certain dependency

inspirations/index.html - overview of all inspirations (with number of games inspired) sorted alphabetically
inspirations/table.html - overview of all inspirations as table
inspirations/[A-Z].html - inspirations sorted by title and categorized alphabetically

developers/index.html - overview of all developers (with number of games created) sorted alphabetically
developers/table.html - overview of all developers as table
developers/[A-Z].html - developers sorted by name and categorized alphabetically

statistics/index.html - overview of statistics
statistics/keywords.html - statistics of keywords (links to genres/xx)
statistics/state.html - statistics of inactive games
statistics/languages.html - statistics of languages (links to languages/xx)
statistics/licenses.html - statistics of licenses
statistics/dependencies.html - statistics of code dependencies (links to dependencies/xx)
statistics/build-systems.html - statistics of build systems

##  Header/Footer

Header: link to overview, link to contribute, link to Github
Footer: link to Blog, link to overviews, link to Github

## Pages structure

### Game entry

- Title (anchor) -- [edit] (aligned right, forwards to contribute)
- Genre, Platform (say "unknown" if unknown), State
- Home (main website)
- Secondary homes: (includes code repository)
- Inspirations: (optional)
- Media: (optional)
- Download: (optional)
- Play: (optional)
- Other keywords: (optional)
- Developer: (optional)
- Note: (optional)

Technical info (hidden initially, can be toggled on/off)

- Code language
- Code repository
- Code license
- Code dependencies (optional)
- Build system/information (optional)
- Assets (optional)

### Inspiration entry

- Title (anchor) -- [edit]
- Media: (optional)
- Inspired entries: (with links)

### Developer entry

- Name (anchor) -- [edit]
- Games: (with links)
- Contact: links to profiles on SourceForge, GitHub, .. converted to links

## Links to external services

We strive to show improved replacements for links to popular services instead of raw URLs: the icon of the service
and a short, meaningful label, for example

| Link | Shown as |
|------|----------|
| `https://github.com/owner/repo.git` | GitHub icon, `owner/repo` (same for GitLab, Codeberg, Bitbucket) |
| `https://sourceforge.net/projects/name/`, `https://git.code.sf.net/p/name/code` | SourceForge icon, `name`, `name/code` |
| `https://en.wikipedia.org/wiki/Battle_Isle#Clones_and_successors` | Wikipedia icon, `Battle Isle › Clones and successors` (other languages with prefix, e.g. `de: …`) |
| `https://web.archive.org/web/20210119051426/https://example.org` | archive icon, `example.org (archived 2021)` |
| any other `https://www.example.org/page/` | `example.org/page` |

The label is derived from the URL only (not from the name of the entry), so it always describes the link target.
Labels longer than 50 characters are shortened in the middle with "…", the full URL is then shown as tooltip. The full
URL always stays the link target.

The rules are `LINK_RULES` in `generate.py` (used by `make_link` for all external links: entry fields, repositories,
notes, inspiration media, developer organizations), with one test case per rule in `tests/test_website.py`. A service
gets its own rule once it is linked often (roughly 20 links or more); its icon is added as described in
`icons/README.md`. In November 2026, about 70% of all links matched a rule (GitHub, SourceForge, Wikipedia, web
archive, Codeberg, GitLab, Bitbucket). Candidates for further rules are f-droid.org and the KDE sites.

## Overviews

Simple paragraphs with headers and columns (for example game names in three columns)