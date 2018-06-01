"""
    Clones and/or pulls all the gits listed in archives.csv

    Requires: git executable in the path

    Warning: This may take a long time on the first run and may need a lot of storage space!
"""

import os
import csv
import subprocess


def derive_folder_name(url):
    github = 'https://github.com/'
    if url.startswith(github):
        url = url[len(github):].split('/')
        folder = 'github.' + url[0] + '.' + url[1] + '.git'
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

    # read archives.csv
    archives = []
    with open('archives.csv', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            archives.append(row)

    # loop over archives
    for archive in archives:
        url = archive[0]
        folder = os.path.join(root_folder, derive_folder_name(url))

        # if not existing do the initial checkout
        if not os.path.isdir(folder):
            os.chdir(root_folder)
            clone(url, folder)

        # pull all
        os.chdir(folder)
        pull()




