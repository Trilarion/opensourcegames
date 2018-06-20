"""
    Clones and/or pulls all the gits listed in archives.json

    Requires: git executable in the path

    Warning: This may take a long time on the first run and may need a lot of storage space!

    TODO are really all existing branches cloned and pulled? (see https://stackoverflow.com/questions/67699/how-to-clone-all-remote-branches-in-git)
    TODO Sourceforge git clone may not work all the time (restart the script helps..)

    Note: May need to set http.postBuffer (https://stackoverflow.com/questions/17683295/git-bash-error-rpc-failed-result-18-htp-code-200b-1kib-s)
"""

import os
import json
import subprocess
import time


def read_text(file):
    """
    Reads a whole text file (UTF-8 encoded).
    """
    with open(file, mode='r', encoding='utf-8') as f:
        text = f.read()
    return text

def derive_folder_name(url, replaces):
    sanitize = lambda x: x.replace('/', '.')
    for service in replaces:
        if url.startswith(service):
            url = replaces[service] + url[len(service):]
            return sanitize(url)
    for generic in ['http://', 'https://']:
        if url.startswith(generic):
            url = url[len(generic):]
            return sanitize(url)
    raise Exception('malformed url')

def git_folder_name(url):
    replaces = {
        'https://github.com': 'github',
        'https://git.code.sf.net/p': 'sourceforge',
        'https://git.tuxfamily.org': 'tuxfamily',
        'https://git.savannah.gnu.org/git': 'savannah.gnu',
        'https://gitlab.com': 'gitlab',
        'https://gitorious.org': 'gitorious',
        'https://anongit.': '',
        'https://bitbucket.org': 'bitbucket'
    }
    return derive_folder_name(url, replaces)


def git_clone(url, folder):
    result = subprocess.run(["git", "clone", "--mirror", url, folder])
    if result.returncode:
        print(result)


def git_update(folder):
    os.chdir(folder)
    result = subprocess.run(["git", "fetch", "--all"])
    if result.returncode:
        print(result)


def svn_folder_name(url):
    replaces = {
        'https://svn.code.sf.net/p': 'sourceforge'
    }
    return derive_folder_name(url, replaces)


def svn_clone(url, folder):
    result = subprocess.run(["svn", "checkout", url, folder])
    if result.returncode:
        print(result)

def svn_update(folder):
    os.chdir(folder)
    result = subprocess.run(["svn", "update"])
    if result.returncode:
        print(result)


def hg_folder_name(url):
    replaces = {
        'https://bitbucket.org': 'bitbucket',
        'https://hg.code.sf.net/p': 'sourceforge',
        'http://hg.': ''
    }
    return derive_folder_name(url, replaces)


def hg_clone(url, folder):
    result = subprocess.run(["hg", "clone", url, folder])
    if result.returncode:
        print(result)


def hg_update(folder):
    os.chdir(folder)
    result = subprocess.run(['hg', 'pull', '-u'])
    if result.returncode:
        print(result)


def bzr_folder_name(url):
    replaces = {
        'https://code.launchpad.net': 'launchpad',
    }
    return derive_folder_name(url, replaces)


def bzr_clone(url, folder):
    result = subprocess.run(['bzr', 'branch', url, folder])
    if result.returncode:
        print(result)


def bzr_update(folder):
    os.chdir(folder)
    result = subprocess.run(['bzr', 'pull'])
    if result.returncode:
        print(result)


def run(type, urls):
    print('update {} {} archives'.format(len(urls), type))
    base_folder = os.path.join(root_folder, type)
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
        if url.startswith('https://git.code.sf.net/p/') or url.startswith('http://hg.code.sf.net/p/'):
            continue
        if not os.path.isdir(folder):
            print('clone {} into {}'.format(url, folder[len(base_folder):]))
            clone[type](url, folder)

    # at the end update them all
    for folder in folders:
        print('update {}'.format(os.path.basename(folder)))
        if not os.path.isdir(folder):
            print('folder not existing, wanted to update, will skip')
            continue
        print('update {}'.format(folder[len(base_folder):]))
        update[type](folder)


if __name__ == '__main__':

    folder_name = {
        'git': git_folder_name,
        'svn': svn_folder_name,
        'hg': hg_folder_name,
        'bzr': bzr_folder_name
    }

    clone = {
        'git': git_clone,
        'svn': svn_clone,
        'hg': hg_clone,
        'bzr': bzr_clone
    }

    update = {
        'git': git_update,
        'svn': svn_update,
        'hg': hg_update,
        'bzr': bzr_update
    }

    # get this folder
    root_folder = os.path.realpath(os.path.dirname(__file__))

    # read archives.json
    text = read_text(os.path.join(root_folder, 'archives.json'))
    archives = json.loads(text)

    for type in archives:
        # currently no bzr checkout (problems with the repos)
        if type == 'bzr':
            continue
        urls = archives[type]
        run(type, urls)





