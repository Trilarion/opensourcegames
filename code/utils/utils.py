"""
Utilities for the tools. Only depending on standard Python or third party modules.
"""

import os
import shutil
import subprocess
import tarfile
import time
import urllib.request
import zipfile
import stat


def read_text(file):
    """
    Reads a whole text file (UTF-8 encoded).
    """
    with open(file, mode='r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    return text


def read_first_line(file):
    """
    Convenience function because we only need the first line of a category overview really.
    """
    with open(file, mode='r', encoding='utf-8') as f:
        line = f.readline()
    return line


def write_text(file, text):
    """
    Writes a whole text file (UTF-8 encoded).
    """
    with open(file, mode='w', encoding='utf-8') as f:
        f.write(text)


def determine_archive_version_generic(name, leading_terms, trailing_terms):
    """
    Given an archive file name, tries to get version information. Generic version that can cut off leading and trailing
    terms and converts to lower case. Give the most special terms first in the list. As many cut offs as possible are
    performed.
    """
    # to lower case
    name = name.lower()

    # cut leading terms
    for t in leading_terms:
        if name.startswith(t):
            name = name[len(t):]

    # cut trailing terms
    for t in trailing_terms:
        if name.endswith(t):
            name = name[:-len(t)]
    return name


def unzip_keep_last_modified(archive, destination):
    """
    Unzips content of a zip file archive into the destination directory keeping the last modified file property as
    it was in the zip archive.

    Assumes that destination is an existing directory path.
    """
    with zipfile.ZipFile(archive, 'r') as zip:
        # zip.extractall(destination)  # does not keep the last modified property
        for zip_entry in zip.infolist():
            name, date_time = zip_entry.filename, zip_entry.date_time
            date_time = time.mktime(date_time + (0, 0, -1))
            zip.extract(zip_entry, destination)
            os.utime(os.path.join(destination, name), (date_time, date_time))


def detect_archive_type(name):
    """
    Tries to guess which type an archive is.
    """
    # test for tar
    tar_endings = ['.tbz2', '.tar.gz']
    for ending in tar_endings:
        if name.endswith(ending):
            return 'tar'

    # test for zip
    zip_endings = ['.zip', '.jar']
    for ending in zip_endings:
        if name.endswith(ending):
            return 'zip'

    # unknown
    return None


def folder_size(path):
    size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for file in filenames:
            size += os.path.getsize(os.path.join(dirpath, file))
    return size


def extract_archive(source, destination, type):
    """
    Extracts a zip, tar, ... to a destination path.

    Type may result from detect_archive_type().
    """
    if type == 'tar':
        tar = tarfile.open(source, 'r')
        tar.extractall(destination)
    elif type == 'zip':
        unzip_keep_last_modified(source, destination)


def strip_wrapped_folders(folder):
    """
    If a folder only contains a single sub-folder and nothing else, descends this way as much as possible.

    Assumes folder is a directory.
    """
    while True:
        entries = list(os.scandir(folder))
        if len(entries) == 1 and entries[0].is_dir():
            folder = entries[0].path
        else:
            break
    return folder


def determine_latest_last_modified_date(folder):
    """
    Given a folder, recursively searches all files in this folder and all sub-folders and memorizes the latest
    "last modified" date of all these files.
    """
    latest_last_modified = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            lastmodified = os.path.getmtime(filepath)
            if lastmodified > latest_last_modified:
                latest_last_modified = lastmodified
    return latest_last_modified


def subprocess_run(cmd, display=True, shell=False, env={}):
    """
    Runs a cmd via subprocess and displays the std output in case of success or the std error output in case of failure
    where it also stops execution.
    """
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, env=dict(os.environ, **env))
    if result.returncode:
        if display:
            print("error {} in call {}".format(result.returncode, cmd))
            print(result.stdout.decode('cp1252'))
            print(result.stderr.decode('cp1252'))
        raise RuntimeError()
    if display:
        print('  output: {}'.format(result.stdout.decode('cp1252')))
    return result.stdout.decode('cp1252')


# TODO need move_tree
def copy_tree(source, destination):
    """
    Copies the full content of one directory into another avoiding the use of distutils.di_util.copy_tree because that
    can give unwanted errors on Windows (probably related to symlinks).
    """
    # this gave an FileNotFoundError: [Errno 2] No such file or directory: '' on Windows
    # distutils.dir_util.copy_tree(archive_path, git_path)
    os.makedirs(destination, exist_ok=True)
    for dirpath, dirnames, filenames in os.walk(source):
        # first create all the directory on destination
        for directory in (os.path.join(destination, os.path.relpath(os.path.join(dirpath, x), source)) for x in dirnames):
            os.makedirs(directory, exist_ok=True)
        # second copy all the files
        for source_file in (os.path.join(dirpath, x) for x in filenames):
            destination_file = os.path.join(destination, os.path.relpath(source_file, source))
            shutil.copyfile(source_file, destination_file)


def download_url(url, destination):
    """
    Using urllib.request downloads from an url to a destination. Destination will be a file.

    Waits one second before, trying to be nice.
    """
    time.sleep(1)  # we are nice
    with urllib.request.urlopen(url) as response:
        with open(destination, 'wb') as f:
            shutil.copyfileobj(response, f)


def handleRemoveReadonly(func, path, exc):
    """
    Necessary on Windows. See https://stackoverflow.com/questions/1889597/deleting-directory-in-python
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def git_clear_path(git_path):
    """
    Clears all in a path except the '.git' directory
    """
    for item in os.listdir(git_path):
        # ignore '.git
        if item == '.git':
            continue
        item = os.path.join(git_path, item)
        if os.path.isdir(item):
            shutil.rmtree(item, onerror=handleRemoveReadonly)
        else:
            os.remove(item)


def recreate_directory(path):
    """
    Recreates a directory (deletes before if existing)
    """
    if os.path.isdir(path):
        shutil.rmtree(path, onerror=handleRemoveReadonly)
    for attempts in range(10):
        try:
            os.mkdir(path)
        except PermissionError:
            time.sleep(0.1)
            continue
        else:
            break
    else:
        raise RuntimeError()


def unzip(zip_file, destination_directory):
    """
    Unzips and keeps the original modified date.

    :param zip_file:
    :param destination_directory:
    :return:
    """
    dirs = {}

    with zipfile.ZipFile(zip_file, 'r') as zip:
        for info in zip.infolist():
            name, date_time = info.filename, info.date_time
            name = os.path.join(destination_directory, name)
            zip.extract(info, destination_directory)

            # still need to adjust the dt o/w item will have the current dt
            date_time = time.mktime(info.date_time + (0, 0, -1))

            if os.path.isdir(name):
                # changes to dir dt will have no effect right now since files are
                # being created inside of it; hold the dt and apply it later
                dirs[name] = date_time
            else:
                os.utime(name, (date_time, date_time))

    # done creating files, now update dir dt
    for name in dirs:
        date_time = dirs[name]
        os.utime(name, (date_time, date_time))


def strip_url(url):
    for prefix in ('http://', 'https://', 'svn://', 'www.'):
        if url.startswith(prefix):
            url = url[len(prefix):]
    for suffix in ('/', '.git', '/en', '/index.html'):
        if url.endswith(suffix):
            url = url[:-len(suffix)]
    return url


def load_properties(filepath, sep='=', comment_char='#'):
    """
    Read the file as a properties file (in Java).
    """
    properties = {}
    with open(filepath, "rt") as file:
        for line in file:
            line = line.strip()
            if not line.startswith(comment_char):
                line = line.split(sep)
                assert (len(line) == 2)
                key = line[0].strip()
                value = line[1].strip()
                properties[key] = value
    return properties


def unique_elements_and_occurrences(elements):
    """

    """
    unique_elements = {}
    for element in elements:
        try:
            unique_elements[element] = unique_elements.get(element, 0) + 1
        except Exception as e:
            print(e)
    unique_elements = list(unique_elements.items())
    unique_elements.sort(key=lambda x: -x[1])
    unique_elements = ['{}({})'.format(k, v) for k, v in unique_elements]
    return unique_elements
