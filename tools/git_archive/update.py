"""
    Clones and/or pulls all the gits listed in archives.csv

    Requires: git executable in the path

    Warning: This may take a long time on the first run and may need a lot of storage space!
"""

import os
import json
import subprocess


def read_text(file):
    """
    Reads a whole text file (UTF-8 encoded).
    """
    with open(file, mode='r', encoding='utf-8') as f:
        text = f.read()
    return text


def derive_folder_name(url):
    github = 'https://github.com/'
    if url.startswith(github):
        parts = url[len(github):].split('/')
        parts.insert(0, 'github')
        folder = '.'.join(parts)
    return folder


def clone(url, folder):
    result = subprocess.run(["git", "clone", url, folder])
    if result.returncode:
        print(result)


def pull():
    result = subprocess.run(["git", "pull", "--all"])
    if result.returncode:
        print(result)


if __name__ == '__main__':

    # get this folder
    root_folder = os.path.realpath(os.path.dirname(__file__))

    # read archives.json
    text = read_text(os.path.join(root_folder, 'archives.json'))
    archives = json.loads(text)

    # loop over archives
    for archive in archives:
        folder = os.path.join(root_folder, derive_folder_name(archive))

        # if not existing do the initial checkout
        if not os.path.isdir(folder):
            os.chdir(root_folder)
            clone(archive, folder)

        # pull all
        os.chdir(folder)
        pull()




