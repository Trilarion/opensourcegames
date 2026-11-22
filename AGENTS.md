# Open Source Games List - Project Architecture

## Overview

**OSGL** is a curated database of open source games and frameworks (1900+ entries) which special emphasis on technical information
like availability of sources, licenses, programming languages or build infos..

The project consists of:

- **Content**: 1,900+ human readable markdown entry files (`entries/`) describing games and frameworks following a simple grammar
- **Metadata**: Developer and inspiration information (`developers.md`, `inspirations.md`)
- **Website**: Static HTML site (`docs/`) generated from the above
- **Maintenance Tools**: Python scripts (`code/`) for validating, enriching, and synchronizing data

## Architecture

### Data Sources
1. **Entry files** - Markdown files with game/tool information (languages, licenses, platforms, repositories, etc.)
2. **Developer/Inspiration lists** - Curated markdown with metadata, partly extracted from the entry files
3. **External APIs** - GitHub, GitLab, Wikipedia for enrichment
4. **Git repositories** - Ability to locally archive the 1,900+ game repositories for preservation

### Processing Pipeline
```
Entry files → Parse → Validate → Enrich (APIs, repositories) → Generate website
```

### Python Codebase (`code/`)
Package `osgl` in `code/src/osgl` (not installed during development, used from the source tree with `code/src` on the
Python path), tests in `code/tests` (pytest),
one-off scripts in `code/scripts`, data files directly in `code/`.
- **Core** (`osgl/*.py`): Parsing, I/O, entry/developer/inspiration management
- **Maintenance** (`osgl/maintenance`): Interactive tools for data validation and sync
- **Import/Export** (`osgl/archiving`, `osgl/sync`, `osgl/external`): Archive management, external data integration
- **Website** (`osgl/website`): Static website generator with templates and static assets
- **UI** (`osgl/ui.py`): Qt-based maintenance interfaces

## For Developers

**Before modifying Python code**, read **[`code/README.md`](code/README.md)** — it contains:
- Complete architecture explanation
- Mandatory code style conventions (including docstring layout, naming, and organization)
- Setup and dependency information
- How to run maintenance scripts
- Common tasks and troubleshooting

## Python execution

Python may be run (e.g. `python`, `pytest`) for verification or maintenance, but only with the currently active
project environment.

- The package `osgl` is not installed in the active environment during development; it is used directly from within
  the repository. Put `code/src` on the Python path (`PYTHONPATH=src` inside `code/`) and run tools as modules,
  e.g. `python -m osgl.website.generate`. pytest does this automatically (`pytest.ini`). The `osgl-*` commands are
  therefore usually not available.
- Never create virtual environments or other Python environments.
- Never install, upgrade or uninstall packages (no `pip install`, `uv`, `conda`, ...), this includes installing the
  `osgl` package itself. The maintainer sets up the environment.
- If a dependency is missing, stop and report what is missing instead of installing it.

## Python documentation style

Before editing Python code, read and follow the **Docstring Style** section in
`code/README.md`. In particular, function and class docstrings must use a
multi-line layout: place the opening triple quotes on their own line and begin
the documentation text on the following line. Do not use one-line docstrings.

## Key Principles

- **Single source of truth**: Entry files are authoritative; other data syncs from them. In particular, the entries
  (`Developer` and `Inspiration` fields) define which developers worked on which projects and which inspirations a
  project has. `developers.md` and `inspirations.md` only keep additional details (contacts, homepages, media links,
  ...) and must adapt to changes in the entries (renamed, added or removed entries). Changes affecting these
  mappings should update the entries and both listings together, to avoid inconsistencies (planned: tooling that
  does this in one step, with tests to follow).
- **Consistency over perfection**: Regular maintenance checks find and report issues
- **Pragmatic validation**: Lark grammars enforce entry format; runtime checks catch logical errors
- **Interactive maintenance**: Tools use a Qt UI for human-in-the-loop operations
- **Statistical analysis**: Statistics are calculated from the entries to detect entries that could be improved
