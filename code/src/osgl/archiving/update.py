"""
Clones and/or pulls all the gits listed in archives.json and archives.git-submodules.json

Requires: git executable in the path (and svn, hg for those repository types)

What is archived per repository type (see also the "Repository archive" section in code/README.md):
  - git: 'git clone --mirror' creates a bare repository with the refspec +refs/*:refs/*, so all branches, tags and
    other refs (on GitHub also the pull request heads refs/pull/*) are copied. 'git fetch --all' uses the same refspec
    and updates all of them. Branches deleted upstream are kept (no --prune), force-pushed branches are overwritten.
    Git LFS objects are fetched with 'git lfs fetch --all origin' into lfs/objects/ of the bare repository, if git-lfs
    is installed and the repository uses LFS (detected by 'filter=lfs' in the .gitattributes of HEAD or by already
    archived LFS objects, so LFS used only on other branches than HEAD is not detected).
  - hg: 'hg clone' copies the full history with all named branches, bookmarks and tags, 'hg pull -u' updates them.
  - svn: 'svn checkout' only creates a working copy of the latest revision of the given URL (often only trunk), the
    history stays on the server.

Error handling:
  - Commands are non-interactive (no credential prompts), git aborts stalled http transfers itself and every command
    has an overall timeout.
  - Failures that look transient (network problems) are retried a limited number of times, permanent failures (e.g.
    repository not found) are not.
  - Clones are made into a temporary '<folder>.incomplete' folder that is renamed only on success, so that failed or
    interrupted clones never leave a broken repository behind.
  - All failures are listed at the end and written to failures.json in the archive folder.

Warning: This may take a long time on the first run and may need a lot of storage space!

Note:
  - May need to set http.postBuffer (https://stackoverflow.com/questions/17683295/git-bash-error-rpc-failed-result-18-htp-code-200b-1kib-s)
  - For repositories see https://serverfault.com/questions/544156/git-clone-fail-instead-of-prompting-for-credentials
"""

import functools
import json
import os
import shutil
import pathlib
import time

from osgl import utils as u, archive as a, constants as c

env = {
    "GIT_TERMINAL_PROMPT": "0",  # fail instead of prompting for credentials (e.g. for repositories that do not exist)
    # "SSH_ASKPASS": "",
    "GCM_INTERACTIVE": "never",
    "GIT_ASKPASS": ""
}

# git aborts a http transfer if it is slower than GIT_LOW_SPEED_LIMIT bytes/s for GIT_LOW_SPEED_TIME seconds
GIT_LOW_SPEED_LIMIT = 1000
GIT_LOW_SPEED_TIME = 300
git_options = ['-c', f'http.lowSpeedLimit={GIT_LOW_SPEED_LIMIT}', '-c', f'http.lowSpeedTime={GIT_LOW_SPEED_TIME}']

# overall timeout in seconds for a single clone or update command (large repositories can take long on the first run)
COMMAND_TIMEOUT = 2 * 3600

# waiting times in seconds before the retries of a failed operation (number of retries = length of this tuple)
RETRY_DELAYS = (15, 60)

# suffix of the temporary folder a repository is cloned into
INCOMPLETE_SUFFIX = '.incomplete'

# parts of error messages (lower case) that indicate a permanent failure, which is not retried
PERMANENT_ERROR_PATTERNS = (
    'repository not found',
    'not found',
    'does not exist',
    'returned error: 401',
    'returned error: 403',
    'returned error: 404',
    'authentication failed',
    'could not read username',
    'terminal prompts disabled',
    'access denied',
    'over its data quota',
)

# parts of error messages (lower case) that indicate a transient failure, which is retried
TRANSIENT_ERROR_PATTERNS = (
    'timed out',
    'operation too slow',
    'connection reset',
    'connection was reset',
    'connection refused',
    'connection closed',
    'failed to connect',
    'could not resolve host',
    'rpc failed',
    'early eof',
    'unexpected disconnect',
    'remote end hung up',
    'returned error: 5',
    'internal server error',
    'bad gateway',
    'service unavailable',
    'temporarily unavailable',
    'ssl',
    'schannel',
    'gnutls',
)


def git_clone(url, folder):
    """
    Clone a git repository with --mirror option for archiving.
    """
    u.subprocess_run(["git", *git_options, "clone", "--mirror", url, str(folder)], env=env, timeout=COMMAND_TIMEOUT)


def git_update(folder):
    """
    Update a previously cloned git repository with latest changes.
    """
    os.chdir(folder)
    u.subprocess_run(["git", *git_options, "fetch", "--all"], env=env, timeout=COMMAND_TIMEOUT)


@functools.cache
def git_lfs_available():
    """
    Checks (once) if the git-lfs extension is installed.

    :return: True if 'git lfs version' runs successfully, False otherwise.
    """
    try:
        u.subprocess_run(["git", "lfs", "version"], display=False)
    except (RuntimeError, OSError):
        return False
    return True


def git_uses_lfs(folder):
    """
    Detects if a bare git repository uses Git LFS.

    Either the .gitattributes file of HEAD contains 'filter=lfs' or LFS objects were already archived earlier. LFS
    that is only used on other branches than HEAD is not detected (checking all refs would be too slow).

    :param folder: Folder of the bare repository (pathlib.Path).
    :return: True if LFS objects should be fetched, False otherwise.
    """
    if (folder / 'lfs' / 'objects').is_dir():
        return True
    try:
        attributes = u.subprocess_run(["git", "-C", str(folder), "show", "HEAD:.gitattributes"], display=False,
                                      env=env)
    except RuntimeError:
        return False  # no .gitattributes in HEAD or empty repository
    return 'filter=lfs' in attributes


def git_lfs_fetch(folder):
    """
    Fetches the Git LFS objects of all refs of a bare git repository into its lfs/objects folder.
    """
    u.subprocess_run(["git", "-C", str(folder), "lfs", "fetch", "--all", "origin"], env=env,
                     timeout=COMMAND_TIMEOUT)


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
    u.subprocess_run(["svn", "checkout", "--non-interactive", url, str(folder)], timeout=COMMAND_TIMEOUT)


def svn_update(folder):
    """
    Updates an svn
    """
    os.chdir(folder)
    u.subprocess_run(["svn", "update", "--non-interactive"], timeout=COMMAND_TIMEOUT)


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
    u.subprocess_run(["hg", "clone", "--noninteractive", url, str(folder)], timeout=COMMAND_TIMEOUT)


def hg_update(folder):
    """
    Updates a hg repository.
    """
    os.chdir(folder)
    u.subprocess_run(['hg', 'pull', '-u', '--noninteractive'], timeout=COMMAND_TIMEOUT)


# repository types we know how to deal with and the operations for each of them
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

supported_types = tuple(folder_name.keys())


def is_transient_error(error):
    """
    Decides if a failed operation should be retried, i.e. if the error looks like a temporary (network) problem.

    Errors matching a permanent pattern are never retried, even if they also match a transient pattern. Overall
    timeouts are not retried either, because the command already ran for a long time.

    :param error: The RuntimeError raised by the failed operation.
    :return: True if the operation should be retried, False otherwise.
    """
    if isinstance(error, u.SubprocessTimeoutError):
        return False
    message = str(error).casefold()
    if any(pattern in message for pattern in PERMANENT_ERROR_PATTERNS):
        return False
    return any(pattern in message for pattern in TRANSIENT_ERROR_PATTERNS)


def remove_folder(folder):
    """
    Removes a folder with all its content, if it exists (also read-only files as they occur in git repositories).
    """
    if folder.exists():
        shutil.rmtree(folder, onexc=u.handleRemoveReadonly)


def run_with_retries(operation, cleanup=None):
    """
    Runs an operation and retries it with waiting times from RETRY_DELAYS as long as it fails with a transient error.

    :param operation: Function without arguments, raises RuntimeError on failure.
    :param cleanup: Optional function without arguments, called after every failed attempt (e.g. to remove a partial
        clone before the next attempt).
    :raises RuntimeError: The error of the last attempt if all attempts failed or the error is not transient.
    """
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            operation()
            return
        except RuntimeError as error:
            if cleanup is not None:
                cleanup()
            if attempt == len(RETRY_DELAYS) or not is_transient_error(error):
                raise
            delay = RETRY_DELAYS[attempt]
            print(f'transient error, will retry in {delay} s (attempt {attempt + 2} of {len(RETRY_DELAYS) + 1})')
            time.sleep(delay)


def clone_repository(type, url, folder):
    """
    Clones a repository into a temporary folder and renames it to the final folder only on success, so that a failed
    or interrupted clone never leaves a partial repository in the final folder.

    :param type: Repository type ('git', 'svn' or 'hg').
    :param url: Repository URL.
    :param folder: Final folder of the repository (pathlib.Path), must not exist.
    :raises RuntimeError: If cloning failed (also after retries).
    """
    incomplete_folder = folder.with_name(folder.name + INCOMPLETE_SUFFIX)
    remove_folder(incomplete_folder)  # leftover of an interrupted earlier run
    run_with_retries(lambda: clone[type](url, incomplete_folder), cleanup=lambda: remove_folder(incomplete_folder))
    try:
        incomplete_folder.rename(folder)
    except OSError as error:
        remove_folder(incomplete_folder)
        raise RuntimeError(f'could not rename {incomplete_folder} to {folder}: {error}') from error


def run_update(archive_folder, type, urls, type_folder=None):
    """
    For a number of repository URLs update our archive. That includes:
    - Move all those that exist but aren't in the actual list in the "unused" directory.
    - Clone the repository for all new URLs where no folder exists
    - Update all others

    :param archive_folder: Root folder of the local archive (pathlib.Path).
    :param type: Repository type ('git', 'svn' or 'hg').
    :param urls: Repository URLs of this type.
    :param type_folder: Name of the sub folder in the archive, defaults to the type.
    :return: List of failures, each a dictionary with type, url, folder, operation and error message.
    """
    if type_folder is None:
        type_folder = type
    print(f'update {len(urls)} {type} archives')
    failures = []

    # creates folders
    base_folder = archive_folder / type_folder
    if not base_folder.exists():
        base_folder.mkdir()
    unused_base_folder = archive_folder / (type_folder + '.unused')
    if not unused_base_folder.exists():
        unused_base_folder.mkdir()

    # remove leftovers of interrupted clones of earlier runs
    for folder in base_folder.iterdir():
        if folder.is_dir() and folder.name.endswith(INCOMPLETE_SUFFIX):
            print(f'remove incomplete clone {folder.name}')
            remove_folder(folder)

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
    cloned_folders = set()
    for folder, url in zip(folders, urls):
        if not folder.is_dir():
            print(f'clone {url} into {folder.relative_to(base_folder)}')
            try:
                clone_repository(type, url, folder)
                cloned_folders.add(folder)
            except RuntimeError as error:
                print('error occurred while cloning, will skip')
                failures.append({'type': type_folder, 'url': url, 'folder': folder.name, 'operation': 'clone',
                                 'error': str(error)})

    # at the end update all (except the freshly cloned ones)
    for folder, url in zip(folders, urls):
        if folder in cloned_folders:
            continue
        print(f'update {folder.relative_to(base_folder)}')
        if not folder.is_dir():
            print('folder not existing, wanted to update, will skip')
            continue
        try:
            run_with_retries(lambda: update[type](folder))
        except RuntimeError as error:
            print('error occurred while updating, will skip')
            failures.append({'type': type_folder, 'url': url, 'folder': folder.name, 'operation': 'update',
                             'error': str(error)})
    os.chdir(base_folder)  # do not stay in a repository folder

    # fetch the Git LFS objects (after cloning and updating, so that they match the current refs)
    if type == 'git':
        failures.extend(run_lfs_fetch(folders, urls, type_folder))

    return failures


def run_lfs_fetch(folders, urls, type_folder):
    """
    Fetches the Git LFS objects for all archived git repositories that use LFS.

    A failure here does not affect the archived repository itself, it is only reported.

    :param folders: Folders of the bare repositories (pathlib.Path), not existing ones are skipped.
    :param urls: Repository URLs, in the same order as folders.
    :param type_folder: Name of the sub folder in the archive (used in the failure report).
    :return: List of failures, each a dictionary with type, url, folder, operation and error message.
    """
    if not git_lfs_available():
        print('git-lfs is not installed, will skip fetching Git LFS objects')
        return []
    failures = []
    for folder, url in zip(folders, urls):
        if not folder.is_dir() or not git_uses_lfs(folder):
            continue
        print(f'lfs fetch {folder.name}')
        try:
            run_with_retries(lambda: git_lfs_fetch(folder))
        except RuntimeError as error:
            print('error occurred while fetching Git LFS objects, will skip')
            failures.append({'type': type_folder, 'url': url, 'folder': folder.name, 'operation': 'lfs fetch',
                             'error': str(error)})
    return failures


def run_info(archive_folder, type, urls):
    """
    Collects some statistics.

    :param archive_folder: Root folder of the local archive (pathlib.Path).
    :param type: Repository type ('git', 'svn' or 'hg').
    :param urls: Repository URLs of this type.
    :return: List of [size, folder] pairs, size is -1 if the folder does not exist.
    """
    print(f'collect info on {type}')

    # get derived folder names
    folders = [pathlib.Path(type) / folder_name[type](url) for url in urls]

    # collect information
    info = []
    for folder in folders:
        print(folder)
        path = archive_folder / folder
        size = u.folder_size(path) if path.is_dir() else -1
        info.append([size, folder])
    return info


def print_failures(failures):
    """
    Prints a summary of all failed clone and update operations.
    """
    print(f'{len(failures)} failed operations')
    for failure in failures:
        error_lines = failure['error'].strip().splitlines()
        reason = error_lines[-1] if error_lines else ''
        print(f"  {failure['operation']} {failure['type']} {failure['url']}: {reason}")


def main():
    """
    Updates the local archive from archives.json and archives.git-submodules.json and writes infos.json and
    failures.json.
    """
    # get the archive folder
    archive_folder = pathlib.Path(c.get_config('archive-folder'))

    # read archives.json
    text = u.read_text(c.archives_file)
    archives = json.loads(text)

    # read archives.git-submodules.json
    text = u.read_text(c.archives_submodules_file)
    archives_git_submodules = json.loads(text)

    # run update on submodules
    failures = run_update(archive_folder, 'git', archives_git_submodules, 'git-submodules')

    # update
    for type in archives:
        if type not in supported_types:
            continue
        urls = archives[type]
        failures.extend(run_update(archive_folder, type, urls))

    # report failures
    print_failures(failures)
    text = json.dumps(failures, indent=1)
    u.write_text(archive_folder / 'failures.json', text)

    # collect info
    infos = []
    for type in archives:
        if type not in supported_types:
            continue
        urls = archives[type]
        infos.extend(run_info(archive_folder, type, urls))
    infos.sort(key=lambda x: x[0], reverse=True)
    infos = [[size, str(folder)] for size, folder in infos]  # paths are not JSON serializable
    text = json.dumps(infos, indent=1)
    u.write_text(archive_folder / 'infos.json', text)


if __name__ == '__main__':
    main()
