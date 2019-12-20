"""
Detects the submodules in the Git repositories via "git show HEAD:.gitmodules" and adds them to the list of
repositories to be checked out. Works on bare repositories.
"""

import json
import re
import urllib.parse

from utils.utils import *
from utils.archive import *

if __name__ == '__main__':

    regex_submodules = re.compile(r"url = (\S*)", re.MULTILINE)

    # get this folder
    root_folder = os.path.realpath(os.path.dirname(__file__))
    archive_folder = os.path.join(root_folder, 'archive')

    # read archives.json
    text = read_text(os.path.join(root_folder, 'archives.json'))
    archives = json.loads(text)

    # loop over all git archives
    submodules = []
    for repo in archives['git']:
        git_folder = git_folder_name(repo)
        folder = os.path.join(archive_folder, 'git', git_folder)
        if not os.path.isdir(folder):
            print('Warning: folder {} does not exist'.format(git_folder))
            continue
        os.chdir(folder)
        try:
            content = subprocess_run(['git', 'show', 'HEAD:.gitmodules'], False)
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
    print('found {} submodules'.format(len(submodules)))
    write_text(os.path.join(root_folder, 'archives.git-submodules.json'), json.dumps(submodules, indent=1))
