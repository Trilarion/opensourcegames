"""
The svn is too big to be automatically imported to git (and Github) because there are lots of large binary data components.
Needs a manual solution.

TODO use git lfs migrate later on the elements
TODO check for sufficient disc space before checkout
"""

import json

import psutil

from utils.utils import *


def remove_folders(base_folder, names):
    if isinstance(names, str):
        names = (names,)
    for name in names:
        folder = os.path.join(base_folder, name)
        if os.path.isdir(folder):
            shutil.rmtree(folder)


def remove_files(base_folder, names):
    if isinstance(names, str):
        names = (names,)
    for name in names:
        file = os.path.join(base_folder, name)
        if os.path.isfile(file):
            os.remove(file)


def special_treatment(destination, revision):
    """

    """

    # copy all important files from Holyspirit/Holyspirit and delete it
    if 5 <= revision <= 330:
        source = os.path.join(destination, 'Holyspirit', 'Holyspirit')
        if os.path.isdir(source):
            if revision >= 8:
                shutil.copytree(os.path.join(source, 'Data'), os.path.join(destination, 'Data'))
            files = [x for x in os.listdir(source) if x.endswith('.txt')]
            for file in files:
                shutil.copy(os.path.join(source, file), destination)
            # remove it
            shutil.rmtree(os.path.join(destination, 'Holyspirit'))

    # copy all important files from Holyspirit and delete it
    if 337 <= revision <= 1700:
        source = os.path.join(destination, 'Holyspirit')
        if os.path.isdir(source):
            data = os.path.join(source, 'Data')
            if os.path.isdir(data):
                # shutil.copytree(data, os.path.join(destination, 'Data'))
                shutil.move(data, destination)
            files = [x for x in os.listdir(source) if x.endswith('.txt') or x.endswith('.conf')]
            for file in files:
                shutil.move(os.path.join(source, file), destination)
            # remove it
            shutil.rmtree(source)

    # remove Holyspirit3 folder
    if 464 <= revision <= 1700:
        remove_folders(destination, 'Holyspirit3')

    # remove Holyspirit2 folder
    if 659 <= revision <= 1700:
        remove_folders(destination, 'Holyspirit2')

    # remove Launcher/release
    if 413 <= revision <= 1700:
        source = os.path.join(destination, 'Launcher')
        remove_folders(source, ('debug', 'release'))

    # delete all *.dll, *.exe in base folder
    if 3 <= revision <= 9:
        files = os.listdir(destination)
        for file in files:
            if file.endswith('.exe') or file.endswith('.dll'):
                os.remove(os.path.join(destination, file))

    # delete "cross" folder
    if 42 <= revision <= 43:
        remove_folders(destination, 'Cross')

    # delete personal photos
    if 374 <= revision <= 1700:
        remove_folders(destination, 'Photos')

    # move empire of steam out
    if 1173 <= revision <= 1700:
        folder = os.path.join(destination, 'EmpireOfSteam')
        if os.path.isdir(folder):
            # move to empire path
            empire = os.path.join(empire_path, 'r{:04d}'.format(revision))
            shutil.move(folder, empire)

    # holy editor cleanup
    if 1078 <= revision <= 1700:
        source = os.path.join(destination, 'HolyEditor')
        remove_folders(source, ('bin', 'release', 'debug', 'obj'))
        remove_files(source, 'moc.exe')

    # source folder cleanup
    if 939 <= revision <= 1700:
        source = os.path.join(destination, 'Source')
        remove_folders(source, 'HS')
        remove_files(source, 'HS.zip')

    # Autres folder cleanup
    if 1272 <= revision <= 1700:
        source = os.path.join(destination, 'Autres')
        remove_folders(source, ('conf', 'db', 'hooks', 'locks'))
        remove_files(source, ('format', 'maj.php'))

    # remove Holyspirit-Demo
    if 1668 <= revision <= 1700:
        remove_folders(destination, 'Holyspirit_Demo')

def delete_global_excludes(folder):
    """

    """
    for dirpath, dirnames, filenames in os.walk(folder):
        rel_path = os.path.relpath(dirpath, folder)
        for file in filenames:
            if file in global_exclude:
                os.remove(os.path.join(dirpath, file))


def delete_empty_directories(folder):
    """

    """
    for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
        rel_path = os.path.relpath(dirpath, folder)
        if not filenames and not dirnames:
            os.removedirs(dirpath)


def list_large_unwanted_files(folder):
    """

    """
    output = []
    for dirpath, dirnames, filenames in os.walk(folder):
        rel_path = os.path.relpath(dirpath, folder)
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            already_listed = False
            for extension in unwanted_file_extensions:
                if file.endswith(extension):
                    output.append(os.path.join(rel_path, file) + ' ' + str(os.path.getsize(file_path)))
                    already_listed = True
                    break
            if not already_listed and os.path.getsize(file_path) > large_file_limit:
                output.append(os.path.join(rel_path, file) + ' ' + str(os.path.getsize(file_path)))
    return output


def checkout(revision_start, revision_end):
    """

    """
    assert revision_end >= revision_start

    for revision in range(revision_start, revision_end + 1):
        # check free disc space
        if psutil.disk_usage(svn_checkout_path).free < 3e10:  # 1e10 = 10 GiB
            print('not enough free disc space, will exit')
            sys.exit(-1)

        print('checking out revision {}'.format(revision))

        # create destination directory
        destination = os.path.join(svn_checkout_path, 'r{:04d}'.format(revision))
        if os.path.exists(destination):
            shutil.rmtree(destination)

        # checkout
        start_time = time.time()
        subprocess_run(['svn', 'export', '-r{}'.format(revision), svn_url, destination])
        print('checkout took {:.1f}s'.format(time.time() - start_time))


def fix_revision(revision_start, revision_end=None):
    """

    """
    if not revision_end:
        revision_end = revision_start
    assert revision_end >= revision_start

    unwanted_files = {}
    sizes = {}

    for revision in range(revision_start, revision_end + 1):
        print('fixing revision {}'.format(revision))

        # destination directory
        destination = os.path.join(svn_checkout_path, 'r{:04d}'.format(revision))
        if not os.path.exists(destination):
            raise RuntimeError('cannot fix revision {}, directory does not exist'.format(revision))

        # special treatment
        special_treatment(destination, revision)

        # delete files from global exclude list
        delete_global_excludes(destination)

        # list unwanted files
        unwanted_files[revision] = list_large_unwanted_files(destination)

        # delete empty directories
        delete_empty_directories(destination)

        # size of resulting folder
        sizes[revision] = folder_size(destination)

    text = json.dumps(unwanted_files, indent=1)
    write_text(os.path.join(svn_checkout_path, 'unwanted_files.json'.format(revision)), text)
    text = json.dumps(sizes, indent=1)
    write_text(os.path.join(svn_checkout_path, 'folder_sizes.json'.format(revision)), text)


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
    print('read log took {:.1f}s'.format(time.time() - start_time))
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


def gitify(revision_start, revision_end):
    """

    """
    assert revision_end >= revision_start

    for revision in range(revision_start, revision_end + 1):
        print('adding revision {} to git'.format(revision))

        # svn folder
        svn_folder = os.path.join(svn_checkout_path, 'r{:04d}'.format(revision))
        if not os.path.exists(svn_folder):
            raise RuntimeError('cannot add revision {}, directory does not exist'.format(revision))

        # clear git path
        print('git clear path')
        while True:
            try:
                git_clear_path(git_path)
                break
            except PermissionError as e:
                print(e)
                # wait a bit
                time.sleep(1)

        # copy source files to git path
        print('copy to git')
        copy_tree(svn_folder, git_path)

        os.chdir(git_path)

        # update the git index (add unstaged, remove deleted, ...)
        print('git add')
        subprocess_run(['git', 'add', '--all'])

        # check if there is something to commit
        status = subprocess_run(['git', 'status', '--porcelain'])
        if not status:
            print(' nothing to commit for revision {}, will skip'.format(revision))
            continue

        # perform the commit
        print('git commit')
        log = logs[revision]  # revision, author, date, message
        message = log[3] + '\r\nsvn-revision: {}'.format(revision)
        print('  message "{}"'.format(message))
        author = authors[log[1]]
        author = '{} <{}>'.format(*author)
        cmd = ['git', 'commit', '--allow-empty-message', '--message={}'.format(message), '--author={}'.format(author),
               '--date={}'.format(log[2])]
        print('  cmd: {}'.format(' '.join(cmd)))
        subprocess_run(cmd)


if __name__ == "__main__":

    global_exclude = ['Thumbs.db']
    unwanted_file_extensions = ['.exe', '.dll']
    large_file_limit = 1e6  # in bytes

    # base path is the directory containing this file
    base_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'conversion')
    print('base path={}'.format(base_path))

    # derived paths
    svn_checkout_path = os.path.join(base_path, 'svn')
    if not os.path.exists(svn_checkout_path):
        os.mkdir(svn_checkout_path)
    empire_path = os.path.join(base_path, 'empire')  # empire of steam side project
    if not os.path.exists(empire_path):
        os.mkdir(empire_path)
    git_path = os.path.join(base_path, 'lechemindeladam')
    if not os.path.exists(git_path):
        initialize_git()

    # svn url
    svn_url = "https://svn.code.sf.net/p/lechemindeladam/code/"

    # read logs
    # logs, authors = read_logs()
    # text = json.dumps(logs, indent=1)
    # write_text(os.path.join(base_path, 'logs.json'), text)
    # text = json.dumps(authors, indent=1)
    # write_text(os.path.join(base_path, 'authors.json'), text)
    text = read_text(os.path.join(base_path, 'logs.json'))
    logs = json.loads(text)
    logs = {x[0]: x for x in logs}  # dictionary
    text = read_text(os.path.join(base_path, 'authors.json'))
    authors = json.loads(text)  # should be a dictionary: svn-author: [git-author, git-email]

    # the steps
    # checkout(1, 50)
    # fix_revision(1, 50)
    # gitify(4, 50)

    # checkout(51, 100)
    # checkout(101, 200)

    # fix_revision(51, 200)

    # gitify(51, 200)

    # checkout(201, 400)
    # fix_revision(201, 400)
    # gitify(201, 400)

    # checkout(401, 800)
    # fix_revision(401, 800)
    # gitify(401, 800)

    # checkout(801, 1200)
    # fix_revision(801, 1200)
    # gitify(801, 1200)

    # checkout(1201, 1470)
    # fix_revision(1201, 1470)
    # gitify(1201, 1470)

    # checkout(1471, 1700)
    # fix_revision(1471, 1700)
    # gitify(1471, 1700)

    checkout(1701, 2100)
