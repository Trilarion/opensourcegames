"""
Clones and/or pulls all the gits listed in archives.json

Requires: git executable in the path

Uses 'git clone --mirror' to set up the git locally.

Warning: This may take a long time on the first run and may need a lot of storage space!

TODO are really all existing branches cloned and pulled? (see https://stackoverflow.com/questions/67699/how-to-clone-all-remote-branches-in-git)
TODO Sourceforge git clone may not work all the time (restarting the script sometimes helps..)

Note: May need to set http.postBuffer (https://stackoverflow.com/questions/17683295/git-bash-error-rpc-failed-result-18-htp-code-200b-1kib-s)
"""

import json

from utils.utils import *
from utils.archive import *


def git_clone(url, folder):
    subprocess_run(["git", "clone", "--mirror", url, folder])


def git_update(folder):
    os.chdir(folder)
    subprocess_run(["git", "fetch", "--all"])


def svn_folder_name(url):
    replaces = {
        'https://svn.code.sf.net/p': 'sourceforge'
    }
    return derive_folder_name(url, replaces)


def svn_clone(url, folder):
    subprocess_run(["svn", "checkout", url, folder])


def svn_update(folder):
    os.chdir(folder)
    subprocess_run(["svn", "update"])


def hg_folder_name(url):
    replaces = {
        'https://bitbucket.org': 'bitbucket',
        'https://hg.code.sf.net/p': 'sourceforge',
        'http://hg.': ''
    }
    return derive_folder_name(url, replaces)


def hg_clone(url, folder):
    subprocess_run(["hg", "clone", url, folder])


def hg_update(folder):
    os.chdir(folder)
    subprocess_run(['hg', 'pull', '-u'])


def run_update(type, urls, type_folder=None):
    if type_folder is None:
        type_folder = type
    print('update {} {} archives'.format(len(urls), type))
    base_folder = os.path.join(archive_folder, type_folder)
    if not os.path.exists(base_folder):
        os.mkdir(base_folder)

    # get derived folder names
    folders = [folder_name[type](url) for url in urls]

    # find those folders not used anymore
    existing_folders = [x for x in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, x))]
    unused_folders = [x for x in existing_folders if x not in folders]
    print('{} unused archives'.format(len(unused_folders)))
    if unused_folders:
        print(unused_folders)

    # new folder, need to clone
    new_folders = [x for x in folders if x not in existing_folders]
    print('{} new archives, will clone'.format(len(new_folders)))

    # add root to folders
    folders = [os.path.join(base_folder, x) for x in folders]
    os.chdir(base_folder)
    for folder, url in zip(folders, urls):
        if not os.path.isdir(folder):
            print('clone {} into {}'.format(url, folder[len(base_folder):]))
            try:
                clone[type](url, folder)
            except RuntimeError as e:
                print('error occurred while cloning, will skip')

    # at the end update them all
    for folder in folders:
        print('update {}'.format(os.path.basename(folder)))
        if not os.path.isdir(folder):
            print('folder not existing, wanted to update, will skip')
            continue
        print('update {}'.format(folder[len(base_folder):]))
        try:
            update[type](folder)
        except RuntimeError as e:
            print('error occurred while updating, will skip')


def run_info(type, urls):
    print('collect info on {}'.format(type))

    # get derived folder names
    folders = [os.path.join(type, folder_name[type](url)) for url in urls]

    # collect information
    info = []
    for folder in folders:
        print(folder)
        path = os.path.join(archive_folder, folder)
        size = folder_size(path) if os.path.isdir(path) else -1
        info.append([size, folder])
    return info


if __name__ == '__main__':

    supported_types = ['git', 'hg', 'svn']

    folder_name = {
        'git': git_folder_name,
        'svn': svn_folder_name,
        'hg': hg_folder_name,
    }

    clone = {
        'git': git_clone,
        'svn': svn_clone,
        'hg': hg_clone,
    }

    update = {
        'git': git_update,
        'svn': svn_update,
        'hg': hg_update,
    }

    # get this folder
    root_folder = os.path.realpath(os.path.dirname(__file__))
    archive_folder = os.path.join(root_folder, 'archive')

    # read archives.json
    text = read_text(os.path.join(root_folder, 'archives.json'))
    archives = json.loads(text)

    # read archives.git-submodules.json
    text = read_text(os.path.join(root_folder, 'archives.git-submodules.json'))
    archives_git_submodules = json.loads(text)

    # run update on submodules
    # run_update('git', archives_git_submodules, 'git-submodules')

    # update
    for type in archives:
        if type not in supported_types:
            continue
        urls = archives[type]
        run_update(type, urls)

    # collect info
    infos = []
    for type in archives:
        urls = archives[type]
        infos.extend(run_info(type, urls))
    infos.sort(key=lambda x: x[0], reverse=True)
    text = json.dumps(infos, indent=1)
    write_text(os.path.join(archive_folder, 'infos.json'), text)
