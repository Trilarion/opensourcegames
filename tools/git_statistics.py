"""
takes all gits that we have in the list and checks the master branch out, then collects some statistics:
- number of distinct comitters
- list of commit dates
- number of commits
- language detection and lines of code counting on final state

uses git log --format="%an, %at, %cn, %ct" --all ti get commits, committers and times (as unix time stamp)
"""

import json
from utils.utils import *

if __name__ == "__main__":

    # paths
    file_path  = os.path.realpath(os.path.dirname(__file__))
    archives_path = os.path.join(file_path, 'git_repositories.json')
    temp_path = os.path.join(file_path, 'temp')

    # get git archives
    text = read_text(archives_path)
    archives = json.loads(text)
    print('process {} git archives'.format(len(archives)))

    # loop over them
    for count, archive in enumerate(archives, 1):

        # printer iteration info
        print('{}/{} - {}'.format(count, len(archives), archive))

        # recreate temp folder
        recreate_directory(temp_path)
        os.chdir(temp_path)

        # clone git in temp folder
        subprocess_run(["git", "clone", "--mirror", archive, temp_path])

        # get commits, etc. info
        info = subprocess_run(["git", "log", '--format="%an, %at, %cn, %ct"'])

        info = info.split('\n')
        info = info[:-1] # last line is empty
        number_commits = len(info)

        info = [x.split(', ') for x in info]
        commiters = set([x[0] for x in info])

        print(' commits: {}, commiters {}'.format(number_commits, len(commiters)))

