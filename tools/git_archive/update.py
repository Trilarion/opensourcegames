"""
    Clones and/or pulls all the gits listed in archives.json

    Requires: git executable in the path

    Warning: This may take a long time on the first run and may need a lot of storage space!

    TODO are really all existing branches cloned and pulled? (see https://stackoverflow.com/questions/67699/how-to-clone-all-remote-branches-in-git)
    TODO detect unused folders?
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

def friendly_folder_name(folder):
    folder = folder.replace('/', '.')
    return folder

def derive_folder_name(url):
    replaces = {
        'https://github.com': 'github',
        'https://git.code.sf.net/p': 'sourceforge',
        'https://git.tuxfamily.org': 'tuxfamily',
    }
    for service in replaces:
        if url.startswith(service):
            url = replaces[service] + url[len(service):]
            return friendly_folder_name(url)
    generic = 'https://'
    if url.startswith(generic) and url.endswith('.git'):
        url = url[len(generic):]
        return friendly_folder_name(url)
    raise Exception('unknown service, please define')


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




