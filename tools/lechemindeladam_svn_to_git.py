"""
The svn is too big to be automatically imported to git (and Github) because there are lots of large binary data components.
Needs a manual solution.
"""

import json

from utils.utils import *


def special_treatment(destination, revision):
    """

    """

    if revision == 5:
        shutil.rmtree(os.path.join(destination, 'Holyspirit'))


def delete_global_excludes(folder):
    """

    """
    for dirpath, dirnames, filenames in os.walk(folder):
        rel_path = os.path.relpath(dirpath, folder)
        if rel_path.startswith('.svn'):
            continue
        for file in filenames:
            if file in global_exclude:
                os.remove(os.path.join(dirpath, file))


def delete_empty_directories(folder):
    """

    """
    for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
        rel_path = os.path.relpath(dirpath, folder)
        if rel_path.startswith('.svn'):
            continue
        if not filenames and not dirnames:
            os.removedirs(dirpath)


def list_large_unwanted_files(folder):
    """

    """
    output = []
    for dirpath, dirnames, filenames in os.walk(folder):
        rel_path = os.path.relpath(dirpath, folder)
        if rel_path.startswith('.svn'):
            continue
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            already_listed = False
            for extension in unwanted_file_extensions:
                if file.endswith(extension):
                    output.append(os.path.join(rel_path, file))
                    already_listed = True
                    break
            if not already_listed and os.path.getsize(file_path) > large_file_limit:
                output.append(os.path.join(rel_path, file))
    return output


def checkout(revision_start, revision_end):
    """

    """
    assert revision_end >= revision_start

    for revision in range(revision_start, revision_end + 1):
        print('checking out revision {}'.format(revision))

        # create destination directory
        destination = os.path.join(svn_checkout_path, 'r{:04d}'.format(revision))
        if os.path.exists(destination):
            shutil.rmtree(destination)

        # checkout
        start_time = time.time()
        subprocess_run(['svn', 'checkout', '-r{}'.format(revision), svn_url, destination])
        print('checkout took {}s'.format(time.time() - start_time))

        # sanitation (delete files from global exclude list)
        delete_global_excludes(destination)

        # list unwanted files
        unwanted_files = list_large_unwanted_files(destination)
        if unwanted_files:
            text = json.dumps(unwanted_files, indent=1)
            write_text(os.path.join(svn_checkout_path, 'r{:04d}_unwanted_files.json'.format(revision)), text)

        # delete empty directories
        delete_empty_directories(destination)

        # special treatment
        special_treatment(destination, revision)


def initialize_git():
    """

    """
    # git init
    os.mkdir(git_path)
    os.chdir(git_path)
    subprocess_run(['git', 'init'])
    subprocess_run(['git', 'config', 'user.name', 'Trilarion'])
    subprocess_run(['git', 'config', 'user.email', 'Trilarion@users.noreply.gitlab.com'])


def combine_log_messages(msg):
    """

    """
    # throw out all empty ones
    msg = [x.strip() for x in msg if x]
    # combine again
    msg = "\r\n".join(msg)
    return msg


def read_logs():
    """
    Probably regular expressions would have worked too.
    """
    # read log
    print('read all log messages')
    os.chdir(svn_checkout_path)
    start_time = time.time()
    log = subprocess_run(['svn', 'log', svn_url], display=False)
    print('read log took {}s'.format(time.time() - start_time))
    # process log
    log = log.split('\r\n------------------------------------------------------------------------\r\n')
    # not the last one
    log = log[:-2]
    print('{} log entries'.format(len(log)))

    # process log entries
    log = [x.split('\r\n') for x in log]

    # the first one still contains an additional "---" elements
    log[0] = log[0][1:]

    # split the first line
    info = [x[0].split('|') for x in log]

    # get the revision
    revision = [int(x[0][1:]) for x in info]

    author = [x[1].strip() for x in info]
    unique_authors = list(set(author))
    unique_authors.sort()

    date = [x[2].strip() for x in info]
    msg = [combine_log_messages(x[2:]) for x in log]
    logs = list(zip(revision, author, date, msg))
    logs.sort(key=lambda x: x[0])
    return logs, unique_authors


if __name__ == "__main__":

    global_exclude = ['Thumbs.db']
    unwanted_file_extensions = ['.exe', '.dll']
    large_file_limit = 1e6  # in bytes

    # base path is the directory containing this file
    base_path = os.path.abspath(os.path.dirname(__file__))
    print('base path={}'.format(base_path))

    # derived paths
    svn_checkout_path = os.path.join(base_path, 'svn_checkout')
    if not os.path.exists(svn_checkout_path):
        os.mkdir(svn_checkout_path)
    git_path = os.path.join(base_path, 'lechemindeladam')
    # if not os.path.exists(git_path):
    #    initialize_git()

    # svn url
    svn_url = "https://svn.code.sf.net/p/lechemindeladam/code/"

    # read logs
    # logs, authors = read_logs()
    # text = json.dumps(logs, indent=1)
    # write_text(os.path.join(svn_checkout_path, 'logs.json'), text)
    # text = json.dumps(authors, indent=1)
    # write_text(os.path.join(svn_checkout_path, 'authors.json'), text)

    checkout(1, 50)
