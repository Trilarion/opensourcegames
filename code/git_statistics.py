"""
Takes all gits that we have in the list and checks the master branch out, then collects some statistics:
- number of distinct committers
- list of commit dates
- number of commits
- language detection and lines of code counting on final state

uses git log --format="%an, %at, %cn, %ct" --all ti get commits, committers and times (as unix time stamp)

STATUS: in development
"""

import json
import os

from utils import constants as c, utils as u

if __name__ == "__main__":

    # paths
    code_path = c.root_path / 'code'
    archives_path = code_path / 'git_repositories.json'
    temp_path = code_path / 'temp'

    # get git archives
    text = u.read_text(archives_path)
    archives = json.loads(text)
    print(f'process {len(archives)} git archives')

    # loop over them
    for count, archive in enumerate(archives, 1):

        # printer iteration info
        print(f'{count}/{len(archives)} - {archive}')

        # recreate temp folder
        u.recreate_directory(temp_path)
        os.chdir(temp_path)

        # clone git in temp folder
        u.subprocess_run(["git", "clone", "--mirror", archive, temp_path])

        # get commits, etc. info
        info = u.subprocess_run(["git", "log", '--format="%an, %at, %cn, %ct"'])

        info = info.split('\n')
        info = info[:-1]  # last line is empty
        number_commits = len(info)

        info = [x.split(', ') for x in info]
        committers = set([x[0] for x in info])

        print(f' commits: {number_commits}, committers {len(committers)}')
