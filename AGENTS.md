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
- **Core**: Parsing, I/O, entry/developer/inspiration management
- **Maintenance**: Interactive tools for data validation and sync
- **Import/Export**: Archive management, external data integration
- **UI**: Qt-based maintenance interfaces

## For Developers

**Before modifying Python code**, read **[`code/README.md`](code/README.md)** — it contains:
- Complete architecture explanation
- Code style conventions (docstrings, naming, organization)
- Setup and dependency information
- How to run maintenance scripts
- Common tasks and troubleshooting

## Key Principles

- **Single source of truth**: Entry files are authoritative; other data syncs from them
- **Consistency over perfection**: Regular maintenance checks find and report issues
- **Pragmatic validation**: Lark grammars enforce entry format; runtime checks catch logical errors
- **Interactive maintenance**: Tools use a Qt UI for human-in-the-loop operations
- **Statistical analysis**: Statistics are calculated from the entries to detect entries that could be improved
