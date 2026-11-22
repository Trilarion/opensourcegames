"""
Tests for writing entries and the rejected list, using temporary copies of the data files.
"""

import pytest

from osgl import constants as c, osg, rejected, utils as u


REJECTED = ('Alpha (https://a.org, https://b.org): not open source\n'
            'beta game (https://c.org): assets proprietary')


# Rejected list


def test_read_rejected_file(repository_copy):
    """
    Each line is split into title, list of URLs and description.
    """
    u.write_text(c.rejected_file, REJECTED)
    assert rejected.read_rejected_file() == [
        {'Title': 'Alpha', 'URLs': ['https://a.org', 'https://b.org'], 'Description': 'not open source'},
        {'Title': 'beta game', 'URLs': ['https://c.org'], 'Description': 'assets proprietary'},
    ]


def test_write_rejected_file_sorts_case_insensitive(repository_copy):
    """
    The rejected list is written sorted by title, ignoring case.
    """
    items = [
        {'Title': 'beta game', 'URLs': ['https://c.org'], 'Description': 'assets proprietary'},
        {'Title': 'Alpha', 'URLs': ['https://a.org', 'https://b.org'], 'Description': 'not open source'},
    ]
    rejected.write_rejected_file(items)
    assert u.read_text(c.rejected_file) == REJECTED


def test_rejected_file_roundtrip(repository_copy):
    """
    Reading and writing the real rejected list keeps its content, and writing is stable (a second write does not
    change the file anymore). The text itself may change on the first write, because spacing is normalized.
    """
    original = rejected.read_rejected_file()
    rejected.write_rejected_file(original)
    assert rejected.read_rejected_file() == sorted(original, key=lambda x: str.casefold(x['Title']))
    written = u.read_text(c.rejected_file)
    rejected.write_rejected_file(rejected.read_rejected_file())
    assert u.read_text(c.rejected_file) == written


# Entries


@pytest.fixture
def real_entries_path():
    """
    Returns the path of the real entries folder (independent of redirections by other fixtures).
    """
    return c.root_path / 'entries'


def test_write_entry(repository_copy, real_entries_path):
    """
    A written entry has the same content as the original file.
    """
    entry = osg.read_entry(real_entries_path / '0_ad.md')
    entry['File'] = '0_ad.md'
    osg.write_entry(entry)
    written = u.read_text(c.entries_path / '0_ad.md')
    assert written == u.read_text(real_entries_path / '0_ad.md')


def test_write_entry_without_overwrite(repository_copy, real_entries_path):
    """
    With overwrite=False an existing entry file is not replaced.
    """
    entry = osg.read_entry(real_entries_path / '0_ad.md')
    entry['File'] = '0_ad.md'
    osg.write_entry(entry)
    with pytest.raises(RuntimeError, match='already existing'):
        osg.write_entry(entry, overwrite=False)


def test_written_entry_can_be_read_again(repository_copy, real_entries_path):
    """
    A written entry is read back to the same data.
    """
    entry = osg.read_entry(real_entries_path / '0_ad.md')
    entry['File'] = '0_ad.md'
    osg.write_entry(entry)
    entry_again = osg.read_entry('0_ad.md')
    entry_again['File'] = '0_ad.md'
    assert entry_again == entry


def test_repository_is_protected(repository_copy, real_entries_path):
    """
    The protect_repository fixture prevents writes into the real repository, here via an absolute file name.
    """
    entry = osg.read_entry(real_entries_path / '0_ad.md')
    with pytest.raises(RuntimeError, match='Test tried to write into the repository'):
        osg.write_entry(entry)  # entry['File'] is the absolute path of the real file
