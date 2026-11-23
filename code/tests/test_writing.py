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


def read_0ad_entry(real_entries_path):
    """
    Reads the real 0 A.D. entry and redirects its file name into the (temporary) entries folder.
    """
    entry = osg.read_entry(real_entries_path / '0_ad.md')
    entry['File'] = '0_ad.md'
    return entry


def test_write_entry_check_raise_does_not_write(repository_copy, real_entries_path):
    """
    With the default check, an invalid entry raises an error naming the file and no file is written.
    """
    entry = read_0ad_entry(real_entries_path)
    entry['Code language'] = ['Klingon']
    with pytest.raises(RuntimeError, match='0_ad.md.*Klingon'):
        osg.write_entry(entry)
    assert not (c.entries_path / '0_ad.md').exists()


def test_write_entry_check_warn_writes(repository_copy, real_entries_path, capsys):
    """
    With check 'warn', an invalid entry is written anyway and the problem is printed.
    """
    entry = read_0ad_entry(real_entries_path)
    entry['Code language'] = ['Klingon']
    osg.write_entry(entry, check='warn')
    assert 'Klingon' in capsys.readouterr().out
    assert '- Code language: Klingon\n' in u.read_text(c.entries_path / '0_ad.md')


def test_write_entry_check_none_writes_silently(repository_copy, real_entries_path, capsys):
    """
    Without check, an invalid entry is written without any message.
    """
    entry = read_0ad_entry(real_entries_path)
    entry['Code language'] = ['Klingon']
    osg.write_entry(entry, check=None)
    assert capsys.readouterr().out == ''
    assert (c.entries_path / '0_ad.md').is_file()


def test_write_entry_invalid_check_mode(repository_copy, real_entries_path):
    """
    An unknown check mode is rejected before anything is written.
    """
    entry = read_0ad_entry(real_entries_path)
    with pytest.raises(ValueError, match='Unknown check mode'):
        osg.write_entry(entry, check='maybe')
    assert not (c.entries_path / '0_ad.md').exists()


def test_write_entry_check_detects_grammar_error(repository_copy, real_entries_path):
    """
    Content that the grammar cannot parse again is detected (here a line break inside a value).
    """
    entry = read_0ad_entry(real_entries_path)
    entry['Keyword'] = entry['Keyword'] + ['broken\nvalue']
    with pytest.raises(RuntimeError, match='0_ad.md'):
        osg.write_entry(entry)
    assert not (c.entries_path / '0_ad.md').exists()


def test_write_entry_keeps_code_language_order(repository_copy, real_entries_path):
    """
    The order of the code languages is chosen by the author (main language first) and is not sorted on writing.
    """
    entry = read_0ad_entry(real_entries_path)
    entry['Code language'] = ['C++', 'C']
    osg.write_entry(entry)
    assert '- Code language: C++, C\n' in u.read_text(c.entries_path / '0_ad.md')


def test_repository_is_protected(repository_copy, real_entries_path):
    """
    The protect_repository fixture prevents writes into the real repository, here via an absolute file name.
    """
    entry = osg.read_entry(real_entries_path / '0_ad.md')
    with pytest.raises(RuntimeError, match='Test tried to write into the repository'):
        osg.write_entry(entry)  # entry['File'] is the absolute path of the real file
