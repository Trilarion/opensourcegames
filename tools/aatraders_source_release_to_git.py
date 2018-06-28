"""
    Downloads source releases from Sourceforge and puts them into a git repository
"""

import json
import datetime
from utils.utils import *

def special_aatrade_package_extraction(source):
    """
    Unpacks "aatrade_packages".
    """
    files = os.listdir(source)
    if any([x.startswith('aatrade_package') for x in files]):
        # we got the special case
        print('aatrade package extraction of {}'.format(source))

        # first delete all, that do not begin with the package name
        for file in files:
            if not file.startswith('aatrade_package'):
                os.remove(os.path.join(source, file))

        # second extract all those with are left, removing them too
        files = os.listdir(source)
        for file in files:
            try:
                extract_archive(os.path.join(source, file), source, 'tar')
            except:
                extract_archive(os.path.join(source, file), source, 'zip')
            os.remove(os.path.join(source, file))


if __name__ == '__main__':

    # base path is the directory containing this file
    base_path = os.path.abspath(os.path.dirname(__file__))
    print('base path={}'.format(base_path))

    # recreate archive path
    archive_path = os.path.join(base_path, 'downloads')
    if not os.path.exists(archive_path):
        os.mkdir(archive_path)

    # load source releases urls
    with open(os.path.join(base_path, 'aatraders.json'), 'r') as f:
        urls = json.load(f)
    print('will process {} urls'.format(len(urls)))
    if len(urls) != len(set(urls)):
        raise RuntimeError("urls list contains duplicates")

    # determine file archives from urls
    archives = [x.split('/')[-2] for x in urls]
    if len(archives) != len(set(archives)):
        raise RuntimeError("files with duplicate archives, cannot deal with that")

    # determine version from file name
    versions = [determine_archive_version_generic(x, leading_terms=['aatrade_', 'aatrade-', 'aatrade'], trailing_terms=['.zip', '.tar.gz', '_release']) for x in archives]
    for version in versions:
        print(version)

    # extend archives to full paths
    archives = [os.path.join(archive_path, x) for x in archives]

    # download them
    print('download source releases')
    for url, destination in zip(urls, archives):
        # only if not yet existing
        if os.path.exists(destination):
            continue
        # download
        print('  download {}'.format(os.path.basename(destination)))
        download_url(url, destination)

    # extract them
    print('extract downloaded archives')
    extracted_archives = [x + '-extracted' for x in archives]
    for archive, extracted_archive in zip(archives, extracted_archives):
        print('  extract {}'.format(os.path.basename(archive)))
        # only if not yet existing
        if os.path.exists(extracted_archive):
            continue
        os.mkdir(extracted_archive)
        # extract
        extract_archive(archive, extracted_archive, detect_archive_type(archive))

    # go up in unzipped archives until the very first non-empty folder
    extracted_archives = [strip_wrapped_folders(x) for x in extracted_archives]

    # special 'aatrade_packageX' treatment
    for extracted_archive in extracted_archives:
        special_aatrade_package_extraction(extracted_archive)

    # calculate size of folder
    sizes = [folder_size(x) for x in extracted_archives]

    # determine date
    dates = [determine_latest_last_modified_date(x) for x in extracted_archives]
    dates_strings = [datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d') for x in dates]
    # if len(dates_strings) != len(set(dates_strings)):
    #     raise RuntimeError("Some on the same day, cannot cope with that")

    # gather all important stuff in one list and sort by dates and throw those out where size is not in range
    db = list(zip(urls, extracted_archives, versions, dates, dates_strings, sizes))
    db.sort(key=lambda x:x[3])

    size_range = [5e6, float("inf")] # set to None if not desired
    if size_range:
        db = [x for x in db if size_range[0] <= x[5] <= size_range[1]]

    print('proposed order')
    for url, _, version, _, date, size in db:
        print('  date={} version={} size={}'.format(date, version, size))

    # git init
    git_path = os.path.join(base_path, 'aatrade')
    if os.path.exists(git_path):
        shutil.rmtree(git_path)
    os.mkdir(git_path)
    os.chdir(git_path)
    subprocess_run(['git', 'init'])
    subprocess_run(['git', 'config', 'user.name', 'Trilarion'])
    subprocess_run(['git', 'config', 'user.email', 'Trilarion@users.noreply.gitlab.com'])

    # now process revision by revision
    print('process revisions')
    git_author = 'akapanamajack, tarnus <akapanamajack_tarnus@user.sourceforge.net>'
    for url, archive_path, version, _, date, _ in db:
        print('  process version={}'.format(version))

        # clear git path without deleting .git
        print('    clear git')
        for item in os.listdir(git_path):
            # ignore '.git
            if item == '.git':
                continue
            item = os.path.join(git_path, item)
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)

        # copy unpacked source files to git path
        print('copy to git')
        copy_tree(archive_path, git_path)

        # update the git index (add unstaged, remove deleted, ...)
        print('git add')
        os.chdir(git_path)
        subprocess_run(['git', 'add', '--all'])

        # perform the commit
        print('git commit')
        os.chdir(git_path)
        message = 'version {} ({}) on {}'.format(version, url, date)
        print('  message "{}"'.format(message))
        subprocess_run(['git', 'commit', '--message={}'.format(message), '--author={}'.format(git_author), '--date={}'.format(date)])