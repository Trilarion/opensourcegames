"""
Utilities for the tools.
"""

import sys
import os
import time
import zipfile
import tarfile
import subprocess
import shutil
import urllib.request


def read_text(file):
    """
    Reads a whole text file (UTF-8 encoded).
    """
    with open(file, mode='r', encoding='utf-8') as f:
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


def subprocess_run(cmd):
    """
    Runs a cmd via subprocess and displays the std output in case of success or the std error output in case of failure
    where it also stops execution.
    """
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        print("error {} in call {}".format(result.returncode, cmd))
        print(result.stderr.decode('ascii'))
        sys.exit(-1)
    else:
        print('  output: {}'.format(result.stdout.decode('ascii')))


def copy_tree(source, destination):
    """
    Copies the full content of one directory into another avoiding the use of distutils.di_util.copy_tree because that
    can give unwanted errors on Windows (probably related to symlinks).
    """
    # this gave an FileNotFoundError: [Errno 2] No such file or directory: '' on Windows
    # distutils.dir_util.copy_tree(archive_path, git_path)
    for dirpath, dirnames, filenames in os.walk(source):
        # first create all the directory on destination
        directories_to_be_created = [os.path.join(destination, os.path.relpath(os.path.join(dirpath, x), source)) for x in dirnames]
        for directory in directories_to_be_created:
            os.makedirs(directory, exist_ok=True)
        # second copy all the files
        filepaths_source = [os.path.join(dirpath, x) for x in filenames]
        filepaths_destination = [os.path.join(destination, os.path.relpath(x, source)) for x in filepaths_source]
        for src, dst in zip(filepaths_source, filepaths_destination):
            shutil.copyfile(src, dst)


def download_url(url, destination):
    """
    Using urllib.request downloads from an url to a destination. Destination will be a file.

    Waits one second before, trying to be nice.
    """
    time.sleep(1)  # we are nice
    with urllib.request.urlopen(url) as response:
        with open(destination, 'wb') as f:
            shutil.copyfileobj(response, f)
