"""
Tests for the generic utilities in osgl.utils.
"""

import os
import sys
import tarfile
import time
import zipfile

import pytest

from osgl import utils as u


@pytest.mark.parametrize('url, expected', [
    ('https://www.example.org/', 'example.org'),
    ('https://github.com/example/sample.git', 'github.com/example/sample'),
    ('http://example.org/index.html', 'example.org'),
])
def test_strip_url(url, expected):
    """
    Common prefixes and suffixes are removed from URLs.
    """
    assert u.strip_url(url) == expected


def test_text_roundtrip(tmp_path):
    """
    Text written with write_text is read back unchanged (UTF-8).
    """
    file = tmp_path / 'text.txt'
    u.write_text(file, 'Jörmungandr\n')
    assert u.read_text(file) == 'Jörmungandr\n'


def test_read_first_line(tmp_path):
    """
    Only the first line (including the line break) is returned.
    """
    file = tmp_path / 'text.txt'
    u.write_text(file, 'first\nsecond\n')
    assert u.read_first_line(file) == 'first\n'


def test_load_properties(tmp_path):
    """
    Properties files are read into a dictionary, comment lines are skipped.
    """
    file = tmp_path / 'private.properties'
    u.write_text(file, '# comment\ngithub-name = someone\ngithub-token=abc\n')
    assert u.load_properties(file) == {'github-name': 'someone', 'github-token': 'abc'}


def test_unique_elements_and_occurrences():
    """
    Elements are counted and sorted by decreasing occurrence.
    """
    assert u.unique_elements_and_occurrences(['a', 'b', 'a']) == ['a(2)', 'b(1)']


# Archives


@pytest.mark.parametrize('name, expected', [
    ('game-1.0.tar.gz', 'tar'),
    ('game-1.0.tbz2', 'tar'),
    ('game-1.0.zip', 'zip'),
    ('game.jar', 'zip'),
    ('game-1.0.7z', None),
])
def test_detect_archive_type(name, expected):
    """
    Archive types are guessed from the file ending.
    """
    assert u.detect_archive_type(name) == expected


def test_determine_archive_version_generic():
    """
    Leading and trailing terms are cut off after converting to lower case.
    """
    version = u.determine_archive_version_generic('Phaos-0.9.2.tar.gz', ['phaos-'], ['.tar.gz', '.zip'])
    assert version == '0.9.2'


@pytest.fixture
def zip_archive(tmp_path):
    """
    Creates a zip archive with a file in a sub folder and a fixed modification date (2001-02-03 04:05:06).
    """
    archive = tmp_path / 'archive.zip'
    with zipfile.ZipFile(archive, 'w') as zip_file:
        info = zipfile.ZipInfo('folder/file.txt', date_time=(2001, 2, 3, 4, 5, 6))
        zip_file.writestr(info, 'content')
    return archive


def expected_timestamp():
    """
    Returns the local timestamp of the modification date used in the zip_archive fixture.
    """
    return time.mktime((2001, 2, 3, 4, 5, 6, 0, 0, -1))


def test_unzip_keep_last_modified(tmp_path, zip_archive):
    """
    Extracted files keep the modification date stored in the zip archive.
    """
    destination = tmp_path / 'out'
    destination.mkdir()
    u.unzip_keep_last_modified(zip_archive, destination)
    file = destination / 'folder' / 'file.txt'
    assert file.read_text() == 'content'
    assert os.path.getmtime(file) == pytest.approx(expected_timestamp())


def test_unzip(tmp_path, zip_archive):
    """
    unzip extracts the archive and keeps the modification date of files.
    """
    destination = tmp_path / 'out'
    destination.mkdir()
    u.unzip(zip_archive, destination)
    file = destination / 'folder' / 'file.txt'
    assert os.path.getmtime(file) == pytest.approx(expected_timestamp())


def test_extract_archive(tmp_path, zip_archive):
    """
    Zip and tar archives are extracted depending on the detected type.
    """
    tar_source = tmp_path / 'source.txt'
    tar_source.write_text('tar content')
    tar_archive = tmp_path / 'archive.tar.gz'
    with tarfile.open(tar_archive, 'w:gz') as tar:
        tar.add(tar_source, arcname='source.txt')

    destination = tmp_path / 'out'
    destination.mkdir()
    u.extract_archive(zip_archive, destination, u.detect_archive_type(zip_archive.name))
    u.extract_archive(tar_archive, destination, u.detect_archive_type(tar_archive.name))
    assert (destination / 'folder' / 'file.txt').read_text() == 'content'
    assert (destination / 'source.txt').read_text() == 'tar content'


# Folders


def test_folder_size(tmp_path):
    """
    The folder size is the sum of all file sizes, including sub folders.
    """
    (tmp_path / 'a.txt').write_bytes(b'123')
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'sub' / 'b.txt').write_bytes(b'12345')
    assert u.folder_size(tmp_path) == 8


def test_strip_wrapped_folders(tmp_path):
    """
    Single sub folders are descended as far as possible.
    """
    inner = tmp_path / 'a' / 'b'
    inner.mkdir(parents=True)
    (inner / 'file.txt').write_text('x')
    assert os.path.samefile(u.strip_wrapped_folders(tmp_path), inner)


def test_determine_latest_last_modified_date(tmp_path):
    """
    The latest modification date of all files (recursively) is returned.
    """
    (tmp_path / 'sub').mkdir()
    old, new = tmp_path / 'old.txt', tmp_path / 'sub' / 'new.txt'
    old.write_text('x')
    new.write_text('x')
    os.utime(old, (1000, 1000))
    os.utime(new, (2000, 2000))
    assert u.determine_latest_last_modified_date(tmp_path) == 2000


def test_copy_tree(tmp_path):
    """
    All files and folders are copied into the destination, which is created if needed.
    """
    source = tmp_path / 'source'
    (source / 'sub' / 'empty').mkdir(parents=True)
    (source / 'a.txt').write_text('a')
    (source / 'sub' / 'b.txt').write_text('b')
    destination = tmp_path / 'destination' / 'nested'
    u.copy_tree(source, destination)
    assert (destination / 'a.txt').read_text() == 'a'
    assert (destination / 'sub' / 'b.txt').read_text() == 'b'
    assert (destination / 'sub' / 'empty').is_dir()


def test_recreate_directory(tmp_path):
    """
    An existing directory is emptied, a missing one is created.
    """
    folder = tmp_path / 'folder'
    u.recreate_directory(folder)
    assert folder.is_dir()
    (folder / 'file.txt').write_text('x')
    u.recreate_directory(folder)
    assert folder.is_dir() and not any(folder.iterdir())


def test_git_clear_path_keeps_git_folder(tmp_path):
    """
    Everything except the .git folder is removed.
    """
    (tmp_path / '.git').mkdir()
    (tmp_path / '.git' / 'HEAD').write_text('ref')
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'main.c').write_text('int main;')
    (tmp_path / 'README').write_text('readme')
    u.git_clear_path(tmp_path)
    assert [item.name for item in tmp_path.iterdir()] == ['.git']
    assert (tmp_path / '.git' / 'HEAD').read_text() == 'ref'


# Subprocesses


def test_subprocess_run_returns_output():
    """
    The standard output of a successful command is returned.
    """
    assert u.subprocess_run(['git', '--version'], display=False).startswith('git version')


def test_subprocess_run_raises_on_failure():
    """
    A failing command raises a RuntimeError.
    """
    with pytest.raises(RuntimeError):
        u.subprocess_run(['git', 'no-such-command'], display=False)


def test_subprocess_run_error_message_contains_stderr():
    """
    The message of the raised RuntimeError contains the standard error output of the command.
    """
    with pytest.raises(RuntimeError, match='no-such-command'):
        u.subprocess_run(['git', 'no-such-command'], display=False)


def test_subprocess_run_raises_on_timeout():
    """
    A command exceeding the timeout is killed and a SubprocessTimeoutError (a RuntimeError) is raised.
    """
    with pytest.raises(u.SubprocessTimeoutError):
        u.subprocess_run([sys.executable, '-c', 'import time; time.sleep(30)'], display=False, timeout=1)
