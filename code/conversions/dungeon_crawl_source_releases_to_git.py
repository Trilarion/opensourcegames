"""
Helps me with importing source revisions into Git
"""

import shutil
import os
import subprocess
import tarfile
import zipfile
import distutils.dir_util
import sys
import urllib.request
import tempfile
import datetime


def extract_sources(source_path, type, destination_path):
    """
        Extracts a zip, tar, ... to a destination path.
    """
    if type == '.tbz2':
        tar = tarfile.open(source_path, 'r')
        os.chdir(destination_path)
        tar.extractall()
    elif type == '.zip':
        with zipfile.ZipFile(source_path, 'r') as zip:
            zip.extractall(destination_path)

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

def single_revision():
    """

    """
    # remove temp path completely and create again
    print('clear temp')
    if os.path.isdir(temp_path):
        shutil.rmtree(temp_path)
    os.mkdir(temp_path)

    # download archive
    print('download archive from ftp')
    with urllib.request.urlopen(ftp_link) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)

    # unpack source files and delete archive
    print('extract {} to temp'.format(os.path.basename(ftp_link)))
    extract_sources(tmp_file.name, os.path.splitext(ftp_link)[1], temp_path)
    os.remove(tmp_file.name)

    # we need to go up in temp_path until we find the first non-empty directory
    nonempty_temp_path = temp_path
    names = os.listdir(nonempty_temp_path)
    while len(names) == 1:
        nonempty_temp_path = os.path.join(nonempty_temp_path, names[0])
        names = os.listdir(nonempty_temp_path)
    print('  working in "{}" relative to temp'.format(os.path.relpath(nonempty_temp_path, temp_path)))

    # if no original date is indicated, get it from the files (latest of last modified)
    global original_date
    if original_date is None:
        latest_last_modified = 0
        for dirpath, dirnames, filenames in os.walk(nonempty_temp_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                lastmodified = os.path.getmtime(filepath)
                if lastmodified > latest_last_modified:
                    latest_last_modified = lastmodified
        original_date = datetime.datetime.fromtimestamp(latest_last_modified).strftime('%Y-%m-%d')
        print('  extracted original date from files: {}'.format(original_date))

    # clear git path without deleting '.git'
    print('clear git')
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
    distutils.dir_util.copy_tree(nonempty_temp_path, git_path)

    # update the git index (add unstaged, remove deleted, ...)
    print('git add')
    os.chdir(git_path)
    subprocess_run(['git', 'add', '--all'])

    # perform the commit
    print('git commit')
    os.chdir(git_path)
    message = 'version {} ({}) on {}'.format(version, ftp_link, original_date)
    print('  message "{}"'.format(message))
    # subprocess_run(['git', 'commit', '--message={}'.format(message), '--author={}'.format(author), '--date={}'.format(original_date), '--dry-run'])
    subprocess_run(['git', 'commit', '--message={}'.format(message), '--author={}'.format(author), '--date={}'.format(original_date)])


if __name__ == "__main__":

    git_path = r'..\crawl' # must be initialized with 'git init' before
    temp_path = r'..\temp'
    author = 'Linley Henzell et al 1997-2005 <www.dungeoncrawl.org>' # is used for all commits


    # 1.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/1.1.x/src/dc110f-src.tbz2'
    # version = '110f'
    # original_date = '1997-10-04'  # format yyyy-mm-dd, according to versions.txt in version 400b26
    # single_revision()

    # 2.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/2.7.x/src/dc270f-src.tbz2'
    # version = '270f'
    # original_date = '1998-09-22'
    # single_revision()

    # 3.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/2.7.x/src/dc272f-src.tbz2'
    # version = '272f'
    # original_date = '1998-10-02'
    # single_revision()

    # 4.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/2.8.x/src/dc280f-src.tbz2'
    # version = '280f'
    # original_date = '1998-10-18'
    # single_revision()

    # 5.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/2.8.x/src/dc281f-src.tbz2'
    # version = '281f'
    # original_date = '1998-10-20'
    # single_revision()

    # 6.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/2.8.x/src/dc282f-src.tbz2'
    # version = '282f'
    # original_date = '1998-10-24'
    # single_revision()

    # 7.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/3.0.x/src/dc301f-src.tbz2'
    # version = '301f'
    # original_date = '1999-01-01'
    # single_revision()

    # 8.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/3.0.x/src/dc302f-src.tbz2'
    # version = '302f'
    # original_date = '1999-01-04'
    # single_revision()

    # 9.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/3.2.x/src/dc320f-src.tbz2'
    # version = '320f'
    # original_date = '1999-02-09'
    # single_revision()

    # 10.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/final/3.3.x/src/dc330f-src.tbz2'
    # version = '330f'
    # original_date = '1999-03-30'
    # single_revision()

    # 11.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta01-src.zip'
    # version = '331beta01'
    # original_date = '1999-04-09'  # "Date last modified" of every file inside and of that the latest
    # single_revision()

    # 12.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta02-src.zip'
    # version = '331beta02'
    # original_date = '1999-06-18'
    # single_revision()

    # 13.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta03-src.zip'
    # version = '331beta03'
    # original_date = '1999-06-22'
    # single_revision()

    # 14.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta04-src.zip'
    # version = '331beta04'
    # original_date = '1999-08-08'
    # single_revision()

    # 15.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta05-src.zip'
    # version = '331beta05'
    # original_date = '1999-08-27'
    # single_revision()

    # 16.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta06-src.zip'
    # version = '331beta06'
    # original_date = '1999-09-12'
    # single_revision()

    # 17.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta07-src.zip'
    # version = '331beta07'
    # original_date = '1999-09-24'
    # single_revision()

    # 18.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta08-src.zip'
    # version = '331beta08'
    # original_date = '1999-09-28'
    # single_revision()

    # 19.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/3.3.x/src/cr331beta09-src.zip'
    # version = '331beta09'
    # original_date = '1999-10-02'
    # single_revision()

    # 20.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr1999oct12src.zip'
    # version = 'cr1999oct12'
    # original_date = '1999-10-12'
    # single_revision()

    # 21.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr1999oct15src.zip'
    # version = 'cr1999oct15'
    # original_date = '1999-10-15'
    # single_revision()

    # 22.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr1999nov18src.zip'
    # version = 'cr1999nov18'
    # original_date = '1999-11-18'
    # single_revision()

    # 23.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr1999nov23src.zip'
    # version = 'cr1999nov23'
    # original_date = '1999-11-23'
    # single_revision()

    # 24.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr1999dec27src.zip'
    # version = 'cr1999dec27'
    # original_date = '1999-12-27'
    # single_revision()

    # 25.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr1999dec30src.zip'
    # version = 'cr1999dec30'
    # original_date = '1999-12-30'
    # single_revision()

    # 26.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr1999dec31src.zip'
    # version = 'cr1999dec31'
    # original_date = '1999-12-31'
    # single_revision()

    # 27.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000jan10src.zip'
    # version = 'cr2000jan10'
    # original_date = '2000-01-10'
    # single_revision()

    # 28.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000feb23src.zip'
    # version = 'cr2000feb23'
    # original_date = '2000-02-23'
    # single_revision()

    # 29.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000mar06src.zip'
    # version = 'cr2000mar06'
    # original_date = '2000-03-06'
    # single_revision()

    # 30.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000jun19src.zip'
    # version = 'cr2000jun19src'
    # original_date = '2000-06-19'
    # single_revision()

    # 31.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000jun20src.zip'
    # version = 'cr2000jun20'
    # original_date = '2000-06-20'
    # single_revision()

    # 32.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000jun22src.zip'
    # version = 'cr2000jun22'
    # original_date = '2000-06-22'
    # single_revision()

    # 33.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000jul22src.zip'
    # version = 'cr2000jul22'
    # original_date = '2000-07-22'
    # single_revision()

    # 34.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000aug01src.zip'
    # version = 'cr2000aug01'
    # original_date = '2000-08-01'
    # single_revision()

    # 35.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000aug13src.zip'
    # version = 'cr2000aug13'
    # original_date = '2000-08-13'
    # single_revision()

    # 36.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/orphan/src/cr2000oct30src.zip'
    # version = 'cr2000oct30'
    # original_date = '2000-10-30'
    # single_revision()

    # 37.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta01-src.tbz2'
    # version = '400beta01'
    # original_date = None # 2000-12-20
    # single_revision()

    # 38.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta02-src.tbz2'
    # version = '400beta02'
    # original_date = None # 2000-12-22
    # single_revision()

    # 39.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta03-src.tbz2'
    # version = '400beta03'
    # original_date = None # 2000-12-29
    # single_revision()

    # 40.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta04-src.tbz2'
    # version = '400beta04'
    # original_date = None # 2001-01-11
    # single_revision()

    # 41.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta06-src.tbz2'
    # version = '400beta06'
    # original_date = None  # 2001-01-23
    # single_revision()

    # 42.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta07-src.tbz2'
    # version = '400beta07'
    # original_date = None # 2001-01-29
    # single_revision()

    # 43.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta08-src.tbz2'
    # version = 'cr400beta08'
    # original_date = None # 2001-02-20
    # single_revision()

    # 44.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta09-src.tbz2'
    # version = 'cr400beta09'
    # original_date = None # 2001-03-06
    # single_revision()

    # 45.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta10-src.tbz2'
    # version = 'cr400beta10'
    # original_date = None # 2001-03-13
    # single_revision()

    # 46.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta10b-src.tbz2'
    # version = 'cr400beta10b'
    # original_date = None # 2001-03-14
    # single_revision()

    # 47.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta10c-src.tbz2'
    # version = 'cr400beta10c'
    # original_date = None # 2001-03-15
    # single_revision()

    # 48.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta10d-src.tbz2'
    # version = '400beta10d'
    # original_date = None # 2001-03-18
    # single_revision()

    # 49.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta11-src.tbz2'
    # version = '400beta11'
    # original_date = None # 2001-03-21
    # single_revision()

    # 50.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta12-src.tbz2'
    # version = '400beta12'
    # original_date = None # 2001-04-02
    # single_revision()

    # 51.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta13-src.tbz2'
    # version = '400beta13'
    # original_date = None # 2001-04-09
    # single_revision()

    # 52.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta14-src.tbz2'
    # version = '400beta14'
    # original_date = None # 2001-04-20
    # single_revision()

    # 53.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta15-src.tbz2'
    # version = '400beta15'
    # original_date = None # 2001-04-25
    # single_revision()

    # 54.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta16-src.tbz2'
    # version = '400beta16'
    # original_date = None # 2001-05-11
    # single_revision()

    # 55.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta17-src.tbz2'
    # version = '400beta17'
    # original_date = None # 2001-06-01
    # single_revision()

    # 56.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta18-src.tbz2'
    # version = '400beta18'
    # original_date = None # 2001-08-04
    # single_revision()

    # 57.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta19-src.tbz2'
    # version = '400beta19'
    # original_date = None # 2001-08-10
    # single_revision()

    # 58.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta20-src.tbz2'
    # version = '400beta20'
    # original_date = None # 2001-11-05
    # single_revision()

    # 59.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/cr400beta22-src.tbz2'
    # version = '400beta22'
    # original_date = None # 2001-12-21
    # single_revision()

    # 60.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/dc400b23-src.tbz2'
    # version = '400b23'
    # original_date = None # 2002-03-16
    # single_revision()

    # 61.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/dc400b24-src.tbz2'
    # version = '400b24'
    # original_date = '2002-06-03' # taken again from ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/
    # single_revision()

    # 62.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/dc400b25-src.tbz2'
    # version = '400b25'
    # original_date = '2003-03-06'
    # single_revision()

    # 63.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/dc400a26-src.tbz2'
    # version = '400a26'
    # original_date = '2003-03-17'
    # single_revision()

    # 64.
    # ftp_link = 'ftp://ftp.dungeoncrawl.org/dev/4.0.x/src/dc400b26-src.tbz2'
    # version = '400b26'
    # original_date = '2003-03-24'
    # single_revision()