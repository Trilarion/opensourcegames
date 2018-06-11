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

def derive_folder_name(url):
    replaces = {
        'https://github.com': 'github',
        'https://git.code.sf.net/p': 'sourceforge',
        'https://git.tuxfamily.org': 'tuxfamily',
        'https://git.savannah.gnu.org/git': 'savannah.gnu',
        'https://gitlab.com': 'gitlab'
    }
    sanitize = lambda x: x.replace('/', '.')
    for service in replaces:
        if url.startswith(service):
            url = replaces[service] + url[len(service):]
            return sanitize(url)
    generics = ['http://', 'https://']
    for generic in generics:
        if url.startswith(generic) and url.endswith('.git'):
            url = url[len(generic):]
            return sanitize(url)
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
    print('update {} archives'.format(len(archives)))

    # get derived folder names
    folders = [derive_folder_name(url) for url in archives]

    # find those folders not used anymore
    existing_folders = [x for x in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, x))]
    unused_folders = [x for x in existing_folders if x not in folders]
    print('{} unused archives'.format(len(unused_folders)))
    if unused_folders:
        print(unused_folders)

    # new folder, need to clone
    new_folders = [x for x in folders if x not in existing_folders]
    print('{} new archives, will clone'.format(len(new_folders)))

    # add root to folders
    folders = [os.path.join(root_folder, x) for x in folders]
    os.chdir(root_folder)
    for folder, archive in zip(folders, archives):
        if not os.path.isdir(folder):
            clone(archive, folder)

    # at the end update them all
    for folder in folders:
        # pull all
        os.chdir(folder)
        pull()





