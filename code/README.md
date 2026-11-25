# Code Architecture

This folder contains the `osgl` Python package and scripts to maintain the Open Source Games List database.

## Folder Layout

```
code/
├── pyproject.toml          # package definition, dependencies, entry points, pytest configuration
├── src/osgl/               # the osgl package
├── tests/                  # pytest test suite
├── scripts/                # one-off tools, not part of the package
└── *.txt, *.json           # data files (backlog, rejected list, archive lists, ...)
```

## Architecture Overview

### Core Modules (`src/osgl/`)

- **`osg.py`**: Main game/entry operations (reading/writing/parsing entries, developers, inspirations)
- **`parse.py`**: Lark grammar-based parsing for markdown entry files and listing files
- **`constants.py`**: Centralized paths, configuration, validation constants, and lookup tables
- **`utils.py`**: Generic utilities (file I/O, subprocess, archive handling)
- **`archive.py`**: Git repository archiving helpers
- **`statistics.py`**: Statistics calculation and visualization
- **`rejected.py`**: Rejected entries management
- **`ui.py`**: Qt/PySide6 UI utilities
- **`external/`**: Wrappers around external services
  - **`github.py`**: GitHub API integration (PyGithub)
  - **`gitlab.py`**: GitLab API integration (Python-GitLab)
  - **`wikipedia.py`**: Wikipedia search integration

### Maintenance Tools (`src/osgl/maintenance/`)

- **`entries.py`**: Validate and maintain entry files (TODO: many consistency checks)
- **`developers.py`**: Maintain `developers.md`, sync with entries
- **`inspirations.py`**: Maintain `inspirations.md`, sync with entries
- **`screenshots.py`**: Update screenshot metadata and verify integrity

### Archive (`src/osgl/archiving/`)

- **`update.py`**: Clone/update git repositories in local archive
- **`detect_submodules.py`**: Detect git submodules of the archived repositories
- **`git_statistics.py`**: Extract statistics from archived repositories

### Synchronization (`src/osgl/sync/`)

Import scripts for external sources (GitHub, GitLab, LibreGameWiki, SourceForge, Codeberg, osgameclones, awesome lists).

### Website (`src/osgl/website/`)

- **`generate.py`**: Generates the static website in `../docs`
- **`templates/`**: Jinja templates
- **`static/`**: CSS, JavaScript, fonts and images copied to the website
- **`design.md`**: Design notes for the static website, including the improved labels of links to popular
  services (icon and short label instead of the raw URL, rules in `LINK_RULES` of `generate.py`)

### Grammars (`src/osgl/grammars/`)

- **`entries.lark`**: Lark grammar for parsing entry markdown files
- **`listing.lark`**: Lark grammar for parsing developer and inspiration listing files

### Data Files (`code/`)

- **`backlog.txt`**, **`rejected.txt`**: Curated lists of candidate and rejected games
- **`archives.json`**, **`archives.git-submodules.json`**: Repositories of the local archive
- **`github_entries.txt`**: Progress file of the GitHub import

All paths are defined in `constants.py`. The repository root is found by searching upwards for the `entries` folder
and `template.md`.

### Scripts (`scripts/`)

One-off tools that import from the `osgl` package but are not part of it (custom source conversions, collage
creation, duplicate check). Some of them need additional dependencies that are not listed in `pyproject.toml`.

## Setup & Dependencies

### Requirements
- Does not need to be compatible with older Python versions. Currently runs with Python 3.12+
- Dependencies listed in `pyproject.toml` (unpinned for flexibility)

### Install
During development the package `osgl` is **not installed** in the active Python environment. It is used directly from
the source tree in `src/` by putting that folder on the Python path. Only the dependencies from `pyproject.toml`
(and pytest) need to be installed in the environment.

```bash
# run inside the code/ folder (Windows PowerShell: $env:PYTHONPATH = "src")
PYTHONPATH=src python -m osgl.maintenance.entries
```

- pytest does this automatically (`pythonpath = src` in `pytest.ini`)
- VS Code does this automatically (`PYTHONPATH` in `.vscode/settings.json` and `.vscode/launch.json`)
- The repository root is found from the location of the package source, so the working directory does not matter

Installing the package is optional and only needed for the `osgl-*` commands. If done, it must be installed in
editable mode (`-e`), because it works on the data of the repository it is located in (the `dev` extra installs
pytest):

```bash
pip install -e .[dev]   # run inside the code/ folder
```

### Configuration
- Local settings (e.g. paths on your machine) are stored in `local-config.ini` in the project root (not tracked in Git).
  It is read by `osgl/constants.py` and accessed via `get_config(key)`, which raises a `RuntimeError` with a
  descriptive message if the file, the `[general]` section or the key is missing. Currently it is only needed
  by the archive tools (`osgl.archiving.update`, `osgl.archiving.detect_submodules`).

  ```ini
  [general]
  # local folder where the game repositories are archived (subfolders git/, svn/, hg/ are created inside)
  archive-folder = D:\path\to\osgl-archive
  ```

  | Key              | Used by                                                       | Description                                  |
  |------------------|---------------------------------------------------------------|----------------------------------------------|
  | `archive-folder` | `osgl.archiving.update`, `osgl.archiving.detect_submodules`   | Root folder of the local repository archive. |
- GitHub/GitLab tokens can be stored in `private.properties` (not tracked in Git)

## Running Maintenance Tools

The maintenance tools provide an interactive UI with available operations. Without an installed package (the usual
case during development, `src/` on the Python path, see Install) all tools are run as modules:

```bash
python -m osgl.maintenance.entries       # maintain game entries
python -m osgl.maintenance.developers    # maintain developer information
python -m osgl.maintenance.inspirations  # maintain inspiration information
python -m osgl.maintenance.screenshots   # update/sync screenshot metadata
python -m osgl.archiving.update          # clone/update archived repositories
python -m osgl.website.generate          # generate the static website
```

With an editable install, the same main tools are also available as commands: `osgl-entries`, `osgl-developers`,
`osgl-inspirations`, `osgl-screenshots`, `osgl-archive`, `osgl-website`.

All other modules are run as modules as well:

```bash
python -m osgl.archiving.git_statistics
python -m osgl.sync.github_import
```

## Data Flow

1. **Entry files** (`../entries/*.md`) → parsed by `parse.py` → internal dictionary representation
2. **Listing files** (`../developers.md`, `../inspirations.md`) → parsed by `parse.py`
3. **External APIs** (GitHub, GitLab, Wikipedia) → enriched via `external/github.py`, `external/gitlab.py`, etc.
4. **Git repositories** → archived locally via `archiving/update.py` → statistics generated by `archiving/git_statistics.py`
5. **Generated files** → `../docs/data/entries.json`, `../statistics.md`, `../entries/screenshots/README.md`

### Repository archive

`osgl-archive` (`archiving/update.py`) clones or updates all repositories listed in `archives.json` and
`archives.git-submodules.json` into the `archive-folder` (subfolders `git/`, `git-submodules/`, `svn/`, `hg/`;
repositories no longer listed are moved to `<type>.unused/`). What is archived depends on the repository type:

| Type | Commands                                     | What is archived                                                                                                                                                                                                                                                        |
|------|----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| git  | `git clone --mirror`, `git fetch --all`      | Bare repository with all refs (refspec `+refs/*:refs/*`): all branches, tags and on GitHub also the pull request heads (`refs/pull/*`). Branches deleted upstream are kept (no `--prune`), force-pushed branches are overwritten (old commits may be lost by garbage collection). |
| hg   | `hg clone`, `hg pull -u`                     | Full history with all named branches, bookmarks and tags.                                                                                                                                                                                                               |
| svn  | `svn checkout`, `svn update`                 | Only a working copy of the latest revision of the given URL (often only trunk), the history stays on the server. A full copy would need `svnrdump dump` or `svnsync`.                                                                                                   |

Git LFS objects are archived for git repositories with `git lfs fetch --all origin` after cloning/updating; they
are stored in `lfs/objects/` of the bare repository. This requires `git-lfs` (otherwise it is skipped with a
message) and is only done for repositories that use LFS, detected by `filter=lfs` in the `.gitattributes` of `HEAD`
or by already archived LFS objects. LFS used only on branches other than `HEAD` is therefore not detected. Failed
LFS fetches (e.g. exceeded bandwidth quota) are reported, but do not affect the archived repository.

Error handling: all commands run non-interactively (no credential prompts), git aborts stalled http transfers
(`http.lowSpeedLimit`/`http.lowSpeedTime`) and every command has an overall timeout. Failures that look transient
(network problems) are retried a few times, permanent ones (e.g. repository not found) are not. Clones go into a
temporary `<folder>.incomplete` folder that is renamed only on success. All failures are printed at the end and
written to `failures.json` in the archive folder, next to `infos.json` (repository sizes); repositories that keep
failing permanently are candidates for updating the entries.

### Entries, developers and inspirations

The entries are the source of truth for the mapping of developers to projects (`Developer` field) and of
inspirations to projects (`Inspiration` field). The listing files only add details:

- `developers.md`: per developer the contact, homepage and organization; the `Games` lists mirror the entries
- `inspirations.md`: per inspiration the media links; the `Inspired entries` lists mirror the entries (whether an
  inspiration is itself an entry is not stored but derived from the entry titles, see `osg.is_included_inspiration`)

When entries are renamed, added or removed, or their developers or inspirations change, both listings must be
adapted. In principle, the entries and both listings should always be changed together, otherwise the data becomes
inconsistent (and e.g. the website generation fails on unknown references). Tooling that performs these changes in
one step is planned; tests for the consistency will follow.

## Code Style & Conventions

### Docstring Style
- Follow **PEP 257** conventions, every function should have a docstring
- Use multi-line docstrings for all functions/classes with a detailed explanation.
- Place the opening triple quotes (`"""`) on their own line; begin the documentation text on the following line. Do not use one-line docstrings such as `"""Does something."""`.
- Place the closing triple quotes on their own line after the documentation text.
- Include parameter descriptions for non-obvious parameters
- Avoid comments with multiple = or - as lines

### Naming Conventions
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase` (e.g., `DevelopersMaintainer`, `EntryTransformer`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `HEIGHT = 128`)
- **Private members**: Prefix with `_` (e.g., `_internal_state`)
- **Variable names**: Use expressive, extended variable names. (e.g. `number`, `language`)
- **Modules**: no `osg_` prefix inside the `osgl` package; avoid local variables that shadow imported module names
  (e.g. `parse`, `rejected`)

### Code Organization
- Keep modules focused and single-purpose
- Always use absolute imports (`from osgl import osg`, `from osgl.external import github`)
- Generic utility functions in `utils.py` (general-purpose, no OSG-specific logic)
- OSG-specific operations in `osg.py` and the other modules of the package
- Parsing logic isolated in `parse.py` using Lark grammars
- Constants centralized in `constants.py`, it also acts as the central configuration file (except for credentials and local paths)
- Runnable modules put their work into a `main()` function, called from `if __name__ == "__main__":`

### Error Handling & Validation
- Raise `RuntimeError` for logical errors or validation failures
- Include descriptive error messages referencing the problematic entry/developer
- Use assertions for internal logic that should never fail (e.g., `assert len(x) <= 1`)
- Print informative messages for maintenance operations (users run these interactively)

### Data Structures
- Parse markdown into dictionaries with field names as keys
- Convert between list (for iteration/sorting) and dictionary (for lookup) formats as needed
- Use `str.casefold()` for case-insensitive string comparisons
- Leverage `difflib.SequenceMatcher` for fuzzy name matching (similarity ratio)

### File I/O
- All text files are UTF-8 encoded with `errors='ignore'` for robustness
- Use `pathlib.Path` for all path operations (all paths in `constants.py`)
- Read/write operations centralized in `utils.py` and `osg.py`

### Dependencies
- The dependencies in `pyproject.toml` are intentionally unpinned to allow flexible version updates
- Test compatibility with Python 3.12+ before committing changes

### Comments
- Add comments for complex logic, workarounds, or non-intuitive patterns
- Mark TODO items for future improvements (searchable in maintenance scripts)

### Testing
- Tests are in `tests/` and use pytest, configured in `pytest.ini`; run them inside the `code/` folder. They import
  `osgl` directly from `src/` (`pythonpath` setting), so the package does not need to be installed, only its dependencies:
  ```bash
  pytest          # all tests
  pytest -m fast  # quick tests only
  pytest -m slow  # tests that process all entries of the database
  ```
- Mark tests that process the whole database with `@pytest.mark.slow`; all other tests are marked `fast` automatically
  (see `tests/conftest.py`)
- Tests in `test_database.py` run on the actual entries, developers and inspirations of the repository
- The Qt UIs are not tested automatically; new logic should preferably go into plain functions that can be tested

## Common Tasks

### Adding a New Consistency Check
1. Add TODO in `maintenance/entries.py`
2. Implement as a method in `EntryMaintainer` class (or create new class)
3. Add action to the interactive UI dictionary
4. Test with sample entry data

### Modifying Entry Format
1. Update grammar in `grammars/entries.lark`
2. Update `constants.py` field definitions
3. Update parsing in `parse.py` if needed
4. Run `pytest` and `osgl-entries` to validate all entries

### Adding External Data Source
1. Create new import script in `sync/`
2. Use existing patterns (GitHub, GitLab, LibreGameWiki)
3. Ensure data is normalized to internal entry format
4. Document in this README

## Troubleshooting

- **Import errors** (`No module named 'osgl'`): `code/src` is not on the Python path, set `PYTHONPATH` (see Install);
  for other missing modules, install the dependencies from `pyproject.toml`
- **Root folder not found**: The package was installed in non-editable mode and is not called from within the repository
- **API rate limits**: GitHub/GitLab scripts may hit rate limits; credentials can help
- **Encoding issues**: Most scripts handle UTF-8
