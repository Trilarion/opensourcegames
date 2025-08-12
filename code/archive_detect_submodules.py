"""
Detects the submodules in the Git repositories via "git show HEAD:.gitmodules" and adds them to the list of
repositories to be checked out. Works on bare repositories.
"""

import json
import re
import pathlib
import urllib
import os

from utils import constants as c, utils as u, archive as a

if __name__ == '__main__':

    regex_submodules = re.compile(r"url = (\S*)", re.MULTILINE)

    # get the archive folder
    archive_folder = c.get_config('archive-folder')
    if not archive_folder:
        raise RuntimeError('No archive folder specified.')
    else:
        archive_folder = pathlib.Path(archive_folder)

    base_folder = archive_folder / 'git'

    # read archives.json
    code_folder = c.root_path / 'code'
    text = u.read_text(code_folder / 'archives.json')
    archives = json.loads(text)

    # loop over all git archives
    submodules = []
    for repo in archives['git']:
        print(f'process {repo}')
        git_folder = a.git_folder_name(repo)
        folder = archive_folder / 'git' / git_folder
        if not folder.is_dir():
            print(f'Warning: folder {git_folder} does not exist')
            continue
        os.chdir(folder)
        try:
            content = u.subprocess_run(['git', 'show', 'HEAD:.gitmodules'], False)
        except:
            continue
        matches = regex_submodules.findall(content)
        # resolve relative urls
        matches = [urllib.parse.urljoin(repo, x) if x.startswith('..') else x for x in matches]
        submodules.extend(matches)

    # transform git://github.com to https://github.com
    for a, b in (('git://github.com', 'https://github.com'), ('git@github.com:', 'https://github.com/'), ('git+ssh://git@github.com', 'https://github.com')):
        submodules = [b + x[len(a):] if x.startswith(a) else x for x in submodules]

    # let all github repos end on ".git"
    submodules = [x + '.git' if 'github.com' in x and not x.endswith('.git') else x for x in submodules]

    # eliminate those which are duplicates and those which are in archives already
    submodules = set(submodules) - set(archives['git'])
    submodules = sorted(list(submodules))

    # TODO single dots are not yet resolved correctly, for example in https://github.com/henkboom/pax-britannica.git
    submodules = [x for x in submodules if not any([x.startswith(y) for y in ('.', 'git@')])]

    # store them
    print(f'found {len(submodules)} submodules')
    u.write_text(code_folder / 'archives.git-submodules.json', json.dumps(submodules, indent=1))
