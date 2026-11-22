"""
Tests that run on the actual database of the repository (entries, developers, inspirations) and on the package
resources. The tests over all entries are marked as slow.
"""

import pytest

from osgl import constants as c, osg, utils as u


def test_repository_layout():
    """
    The repository root is found and package resources are present.
    """
    assert c.entries_path.is_dir()
    assert c.template_file.is_file()
    assert c.grammar_entries_file.is_file()
    assert c.grammar_listing_file.is_file()
    assert (c.web_template_path / 'base.jinja').is_file()
    assert (c.web_static_path / 'css').is_dir()
    assert c.json_db_file.name == 'data.json'


def test_read_single_entry():
    """
    A known entry can be read and has the essential fields.
    """
    entry = osg.read_entry('0_ad.md')
    assert entry['Title'] == '0 A.D.'
    for field in c.essential_fields:
        assert field in entry


@pytest.mark.slow
def test_read_all_entries():
    """
    All entry files conform to the grammar and pass the consistency checks done while reading.
    """
    entries = osg.read_entries()
    files = [file for file in c.entries_path.iterdir() if file.is_file()]
    assert len(entries) == len(files)


@pytest.mark.slow
def test_entries_roundtrip():
    """
    Reading an entry and creating its content again reproduces the file content exactly.
    """
    differences = []
    for file in sorted(c.entries_path.iterdir()):
        if not file.is_file():
            continue
        text = u.read_text(file).replace('\r\n', '\n')
        entry = osg.read_entry(file)
        if osg.create_entry_content(entry) != text:
            differences.append(file.name)
    assert not differences, f'{len(differences)} entries change when written again, e.g. {differences[:5]}'


@pytest.mark.slow
def test_read_developers_and_inspirations():
    """
    The developers and inspirations listings can be parsed.
    """
    assert osg.read_developers()
    assert osg.read_inspirations()
