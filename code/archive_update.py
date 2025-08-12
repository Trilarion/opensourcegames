"""
Clones and/or pulls all the gits listed in archives.json and archives.git-submodules.json

Requires: git executable in the path

Uses 'git clone --mirror' to set up the git locally.

Warning: This may take a long time on the first run and may need a lot of storage space!

Note:
  - May need to set http.postBuffer (https://stackoverflow.com/questions/17683295/git-bash-error-rpc-failed-result-18-htp-code-200b-1kib-s)
  - For repositories see https://serverfault.com/questions/544156/git-clone-fail-instead-of-prompting-for-credentials
"""

# TODO are really all existing branches cloned and pulled? (see https://stackoverflow.com/questions/67699/how-to-clone-all-remote-branches-in-git)
# TODO Sourceforge git clone may not work all the time (restarting the script sometimes helps..)

import json
import os
import shutil
import pathlib

from utils import utils as u, archive as a, constants as c

def git_clone(url, folder):
    """
    Clones a git with --mirror for the first time.
    """
    # subprocess_run(["git", "clone", "--mirror", url, folder], shell=True, env={'GIT_TERMINAL_PROMPT': '0'})
    u.subprocess_run(["git", "clone", "--mirror", url, str(folder)])


def git_update(folder):
    """
    Updates a cloned git.
    """
    os.chdir(folder)
    # subprocess_run(["git", "fetch", "--all"],  shell=True, env={'GIT_TERMINAL_PROMPT': '0'})
    u.subprocess_run(["git", "fetch", "--all"], display=False)


def svn_folder_name(url):
    """
    Gets a folder name for a svn
    """
    replaces = {
        'https://svn.code.sf.net/p': 'sourceforge'
    }
    return a.derive_folder_name(url, replaces)


def svn_clone(url, folder):
    """
    Checks out an svn
    """
    u.subprocess_run(["svn", "checkout", url, str(folder)])


def svn_update(folder):
    """
    Updates an svn
    """
    os.chdir(folder)
    u.subprocess_run(["svn", "update"])


def hg_folder_name(url):
    """
    Gets a folder name for a hg repository.
    """
    replaces = {
        'https://bitbucket.org': 'bitbucket',
        'https://hg.code.sf.net/p': 'sourceforge',
        'http://hg.': ''
    }
    return a.derive_folder_name(url, replaces)


def hg_clone(url, folder):
    """
    Clones a hg repository.
    """
    u.subprocess_run(["hg", "clone", url, str(folder)])


def hg_update(folder):
    """
    Updates a hg repository.
    """
    os.chdir(folder)
    u.subprocess_run(['hg', 'pull', '-u'])


def run_update(type, urls, type_folder=None):
    """
    For a number of repository URLs update our archive. That includes:
    - Move all those that exist but aren't in the actual list in the "unused" directory.
    - Clone the repository for all new URLs where no folder exists
    - Update all others
    """
    if type_folder is None:
        type_folder = type
    print(f'update {len(urls)} {type} archives')

    # creates folders
    base_folder = archive_folder / type_folder
    if not base_folder.exists():
        base_folder.mkdir()
    unused_base_folder = archive_folder / (type_folder + '.unused')
    if not unused_base_folder.exists():
        unused_base_folder.mkdir()

    # get derived folder names
    folder_names = [folder_name[type](url) for url in urls]

    # find those folders not used anymore
    existing_folder_names = [x.name for x in base_folder.iterdir() if x.is_dir()]
    unused_folder_names = [x for x in existing_folder_names if x not in folder_names]
    print(f'{len(unused_folder_names)} unused archives, move to unused folder')
    for folder in unused_folder_names:
        origin = base_folder / folder
        destination = unused_base_folder / folder
        if not destination.exists():
            shutil.move(origin, destination)

    # new folder, need to clone
    new_folder_names = [x for x in folder_names if x not in existing_folder_names]
    print(f'{len(new_folder_names)} new archives, will clone')

    # add root to folders
    folders = [base_folder / name for name in folder_names]
    os.chdir(base_folder)
    for folder, url in zip(folders, urls):
        if not folder.is_dir():
            print(f'clone {url} into {folder.relative_to(base_folder)}')
            try:
                clone[type](url, folder)
            except RuntimeError as e:
                print('error occurred while cloning, will skip')

    # at the end update them all
    for folder in folders:
        print(f'update {folder.relative_to(base_folder)}')
        if not folder.is_dir():
            print('folder not existing, wanted to update, will skip')
            continue
        # print('update {}'.format(folder[len(base_folder):]))
        try:
            update[type](folder)
        except RuntimeError as e:
            print('error occurred while updating, will skip')


def run_info(type, urls):
    """
    Collects some statistics.
    """
    print(f'collect info on {type}')

    # get derived folder names
    folders = [type / folder_name[type](url) for url in urls]

    # collect information
    info = []
    for folder in folders:
        print(folder)
        path = archive_folder / folder
        size = u.folder_size(path) if path.is_dir() else -1
        info.append([size, folder])
    return info


if __name__ == '__main__':

    # we know how to deal with three different folder names
    supported_types = ['git', 'hg', 'svn']

    folder_name = {
        'git': a.git_folder_name,
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

    # get the archive folder
    archive_folder = c.get_config('archive-folder')
    if not archive_folder:
        raise RuntimeError('No archive folder specified.')
    else:
        archive_folder = pathlib.Path(archive_folder)

    # read archives.json
    code_folder = c.root_path / 'code'
    text = u.read_text(code_folder / 'archives.json')
    archives = json.loads(text)

    # read archives.git-submodules.json
    text = u.read_text(code_folder / 'archives.git-submodules.json')
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
    u.write_text(archive_folder / 'infos.json', text)
