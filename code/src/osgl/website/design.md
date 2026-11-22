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

## Overviews

Simple paragraphs with headers and columns (for example game names in three columns)