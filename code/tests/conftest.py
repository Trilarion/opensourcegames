"""
Shared fixtures for the osgl test suite.
"""

import os
import pathlib
import shutil

# render charts without a display (must be set before matplotlib is imported)
os.environ.setdefault('MPLBACKEND', 'Agg')

import pytest

from osgl import constants as c, parse, utils as u


SAMPLE_ENTRY = """# Sample Game

- Home: https://example.org/
- Inspiration: Master of Orion
- State: beta, inactive since 2020
- Keyword: strategy, remake or clone
- Code repository: https://github.com/example/sample.git (@created 2018, @stars 27)
- Code language: C, C++
- Code license: GPL-2.0
- Developer: Jane Doe, "Studio, Inc."

A short note about the game.

## Building

- Build system: CMake
"""

SAMPLE_ENTRY_FILE = 'sample_game.md'


def pytest_collection_modifyitems(items):
    """
    Marks every test that is not marked as slow as fast, so that both groups can be selected with -m.
    """
    for item in items:
        if item.get_closest_marker('slow') is None:
            item.add_marker(pytest.mark.fast)


@pytest.fixture(autouse=True)
def protect_repository(monkeypatch):
    """
    Lets every test fail that tries to write a file inside the repository via osgl.utils.write_text.

    Tests that need to write data files use the repository_copy fixture, which redirects the paths to a temporary
    folder outside of the repository.
    """
    original_write_text = u.write_text

    def guarded_write_text(file, text):
        """
        Writes the text only if the file is outside the repository.
        """
        path = pathlib.Path(file).resolve()
        if path.is_relative_to(c.root_path):
            raise RuntimeError(f'Test tried to write into the repository: {path}')
        original_write_text(file, text)

    monkeypatch.setattr(u, 'write_text', guarded_write_text)


@pytest.fixture
def repository_copy(tmp_path, monkeypatch):
    """
    Copies the listing files and the rejected list to a temporary folder and redirects the corresponding constants
    (and the entries path, to an empty folder) there. Returns the temporary folder.
    """
    for name, source in (('developer_file', c.developer_file), ('inspirations_file', c.inspirations_file),
                         ('rejected_file', c.rejected_file)):
        destination = tmp_path / source.name
        shutil.copyfile(source, destination)
        monkeypatch.setattr(c, name, destination)
    entries_path = tmp_path / 'entries'
    entries_path.mkdir()
    monkeypatch.setattr(c, 'entries_path', entries_path)
    return tmp_path


@pytest.fixture(scope='session')
def parse_entry():
    """
    Returns a function that parses and transforms the content of an entry file with the entries grammar.
    """
    grammar = u.read_text(c.grammar_entries_file)
    return parse.create(grammar, parse.EntryTransformer)


@pytest.fixture(scope='session')
def parse_listing():
    """
    Returns a function that parses and transforms the content of a listing file (developers, inspirations).
    """
    grammar = u.read_text(c.grammar_listing_file)
    return parse.create(grammar, parse.ListingTransformer)


@pytest.fixture
def sample_entry_text():
    """
    Returns the text of a small, valid sample entry.
    """
    return SAMPLE_ENTRY


@pytest.fixture
def raw_sample_entry(parse_entry):
    """
    Returns the sample entry as parsed but not yet checked, i.e. as list of (field, value) pairs with the file name
    as first pair. This is the input format of osg._check_and_process_entry.
    """
    return [('File', pathlib.Path(SAMPLE_ENTRY_FILE))] + parse_entry(SAMPLE_ENTRY)
