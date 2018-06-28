"""
    Downloads source releases from Sourceforge and puts them into a git repository
"""

import os
import shutil
import urllib.request
import json
import time
import zipfile
import subprocess
import datetime
import distutils.dir_util
import sys


def determine_version(name):
    # to lower case
    name = name.lower()
    # cut leading terms
    terms = ['phaos-', 'phaos', 'pv']
    for t in terms:
        if name.startswith(t):
            name = name[len(t):]
    # cut trailing '.zip'
    t = '.zip'
    if name.endswith(t):
        name = name[:-len(t)]
    return name


def determine_last_modified_date(folder):
    latest_last_modified = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            lastmodified = os.path.getmtime(filepath)
            if lastmodified > latest_last_modified:
                latest_last_modified = lastmodified
    return latest_last_modified


def unzip_keep_last_modified(archive, destination):
    """
        Assuming that destination is a directory and already existing.
    """
    with zipfile.ZipFile(archive, 'r') as zip:
        # zip.extractall(destination)
        for zip_entry in zip.infolist():
            name, date_time = zip_entry.filename, zip_entry.date_time
            date_time = time.mktime(date_time + (0, 0, -1))
            zip.extract(zip_entry, destination)
            os.utime(os.path.join(destination, name), (date_time, date_time))

def strip_wrapping(folder):
    names = os.listdir(folder)
    while len(names) == 1:
        folder = os.path.join(folder, names[0])
        names = os.listdir(folder)
    return folder

def copy_tree(source, destination):
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


def subprocess_run(cmd):
    """

    """
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        print("error {} in call {}".format(result.returncode, cmd))
        print(result.stderr.decode('ascii'))
        sys.exit(-1)
    else:
        print('  output: {}'.format(result.stdout.decode('ascii')))


if __name__ == '__main__':

    # https://sourceforge.net/projects/phaosrpg/files/OldFiles/Pv0.7devel.zip/download is a corrupt zip

    # base path is the directory containing this file
    base_path = os.path.abspath(os.path.dirname(__file__))
    print('base path={}'.format(base_path))

    # recreate archive path
    archive_path = os.path.join(base_path, 'downloads')
    if not os.path.exists(archive_path):
        os.mkdir(archive_path)

    # load source releases urls
    with open(os.path.join(base_path, 'phaos.json'), 'r') as f:
        urls = json.load(f)
    print('will process {} urls'.format(len(urls)))
    if len(urls) != len(set(urls)):
        raise RuntimeError("urls list contains duplicates")

    # determine file archives from urls
    archives = [x.split('/')[-2] for x in urls]
    if len(archives) != len(set(archives)):
        raise RuntimeError("files with duplicate archives, cannot deal with that")

    # determine version from file name
    versions = [determine_version(x) for x in archives]
    # for version in versions:
    #     print(version)

    # extend archives to full paths
    archives = [os.path.join(archive_path, x) for x in archives]

    # download them
    print('download source releases')
    for url, destination in zip(urls, archives):
        # only if not yet existing
        if os.path.exists(destination):
            continue
        # download
        print('  download {}'.format(os.path.basename(destination)))
        with urllib.request.urlopen(url) as response:
            with open(destination, 'wb') as f:
                shutil.copyfileobj(response, f)
                time.sleep(1) # we are nice

    # unzip them
    print('unzip downloaded archives')
    unzipped_archives = [x[:-4] for x in archives] # folder is archive name without .zip
    for archive, unzipped_archive in zip(archives, unzipped_archives):
        print('  unzip {}'.format(os.path.basename(archive)))
        # only if not yet existing
        if os.path.exists(unzipped_archive):
            continue
        os.mkdir(unzipped_archive)
        # unzip
        unzip_keep_last_modified(archive, unzipped_archive)

    # go up in unzipped archives until the very first non-empty folder
    unzipped_archives = [strip_wrapping(x) for x in unzipped_archives]

    # determine date
    dates = [determine_last_modified_date(x) for x in unzipped_archives]
    dates_strings = [datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d') for x in dates]
    # if len(dates_strings) != len(set(dates_strings)):
    #     raise RuntimeError("Some on the same day, cannot cope with that")

    # gather all important stuff in one list and sort by dates
    db = list(zip(urls, unzipped_archives, versions, dates, dates_strings))
    db.sort(key=lambda x:x[3])
    print('proposed order')
    for url, _, version, _, date in db:
        print('  date={} version={}'.format(date, version))

    # git init
    git_path = os.path.join(base_path, 'phaosrpg')
    if os.path.exists(git_path):
        shutil.rmtree(git_path)
    os.mkdir(git_path)
    os.chdir(git_path)
    subprocess_run(['git', 'init'])

    # now process revision by revision
    print('process revisions')
    git_author = 'eproductions3 <eproductions3@user.sourceforge.net>'
    for url, archive_path, version, _, date in db:
        print('  process version={}'.format(version))

        # clear git path without deleting .git
        print('    clear git')
        for item in os.listdir(git_path):
            # ignore '.git
            if item == '.git':
                continue
            item = os.path.join(git_path, item)
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)

        # copy unpacked source files to git path
        print('copy to git')
        copy_tree(archive_path, git_path)

        # update the git index (add unstaged, remove deleted, ...)
        print('git add')
        os.chdir(git_path)
        subprocess_run(['git', 'add', '--all'])

        # perform the commit
        print('git commit')
        os.chdir(git_path)
        message = 'version {} ({}) on {}'.format(version, url, date)
        print('  message "{}"'.format(message))
        subprocess_run(['git', 'commit', '--message={}'.format(message), '--author={}'.format(git_author), '--date={}'.format(date)])