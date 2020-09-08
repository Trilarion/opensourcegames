import json
import textwrap
import os
import re

import utils.constants
from utils import constants as c, utils


def export_json(infos):
    """
    Parses all entries, collects interesting info and stores it in a json file suitable for displaying
    with a dynamic table in a browser.
    """

    print('export to json for web display')

    # make database out of it
    db = {'headings': ['Game', 'Description', 'Download', 'State', 'Keywords', 'Source']}

    entries = []
    for info in infos:

        # game & description
        entry = ['{} (<a href="{}">home</a>, <a href="{}">entry</a>)'.format(info['Name'], info['home'][0],
                                                                             r'https://github.com/Trilarion/opensourcegames/blob/master/entries/' +
                                                                             info['file']),
                 textwrap.shorten(info['description'], width=60, placeholder='..')]

        # download
        field = 'download'
        if field in info and info[field]:
            entry.append('<a href="{}">Link</a>'.format(info[field][0]))
        else:
            entry.append('')

        # state (field state is essential)
        entry.append('{} / {}'.format(info['state'][0],
                                      'inactive since {}'.format(info['inactive']) if 'inactive' in info else 'active'))

        # keywords
        field = 'keywords'
        if field in info and info[field]:
            entry.append(', '.join(info[field]))
        else:
            entry.append('')

        # source
        text = []
        field = 'code repository'
        if field in info and info[field]:
            text.append('<a href="{}">Source</a>'.format(info[field][0]))
        field = 'code language'
        if field in info and info[field]:
            text.append(', '.join(info[field]))
        field = 'code license'
        if field in info and info[field]:
            text.append(info[field][0])
        entry.append(' - '.join(text))

        # append to entries
        entries.append(entry)

    # sort entries by game name
    entries.sort(key=lambda x: str.casefold(x[0]))

    db['data'] = entries

    # output
    json_path = os.path.join(c.entries_path, os.path.pardir, 'docs', 'data.json')
    text = json.dumps(db, indent=1)
    utils.write_text(json_path, text)


def git_repo(repo):
    """
        Tests if a repo is a git repo, then returns the repo url, possibly modifying it slightly.
    """

    # generic (https://*.git) or (http://*.git) ending on git
    if (repo.startswith('https://') or repo.startswith('http://')) and repo.endswith('.git'):
        return repo

    # for all others we just check if they start with the typical urls of git services
    services = ['https://git.tuxfamily.org/', 'http://git.pond.sub.org/', 'https://gitorious.org/',
                'https://git.code.sf.net/p/']
    for service in services:
        if repo.startswith(service):
            return repo

    if repo.startswith('git://'):
        return repo

    # the rest is ignored
    return None


def svn_repo(repo):
    """
    
    """
    if repo.startswith('https://svn.code.sf.net/p/'):
        return repo

    if repo.startswith('http://svn.uktrainsim.com/svn/'):
        return repo

    if repo == 'https://rpg.hamsterrepublic.com/source/wip':
        return repo

    if repo.startswith('http://svn.savannah.gnu.org/svn/'):
        return repo

    if repo.startswith('svn://'):
        return repo

    if repo.startswith('https://svn.icculus.org/') or repo.startswith('http://svn.icculus.org/'):
        return repo

    # not svn
    return None


def hg_repo(repo):
    """

    """
    if repo.startswith('https://bitbucket.org/') and not repo.endswith('.git'):
        return repo

    if repo.startswith('http://hg.'):
        return repo

    # not hg
    return None


def export_primary_code_repositories_json(infos):
    """

    """

    print('export to json for local repository update')

    primary_repos = {'git': [], 'svn': [], 'hg': []}
    unconsumed_entries = []

    # for every entry filter those that are known git repositories (add additional repositories)
    field = 'code repository-raw'
    for info in infos:
        # if field 'Code repository' is available
        if field in info:
            consumed = False
            repos = info[field]
            if repos:
                # split at comma
                repos = repos.split(',')
                # keep the first and all others containing "(+)"
                additional_repos = [x for x in repos[1:] if "(+)" in x]
                repos = repos[0:1]
                repos.extend(additional_repos)
                for repo in repos:
                    # remove parenthesis and strip of white spaces
                    repo = re.sub(r'\([^)]*\)', '', repo)
                    repo = repo.strip()
                    url = git_repo(repo)
                    if url:
                        primary_repos['git'].append(url)
                        consumed = True
                        continue
                    url = svn_repo(repo)
                    if url:
                        primary_repos['svn'].append(url)
                        consumed = True
                        continue
                    url = hg_repo(repo)
                    if url:
                        primary_repos['hg'].append(url)
                        consumed = True
                        continue

            if not consumed:
                unconsumed_entries.append([info['Name'], info[field]])
                # print output
                if 'code repository' in info:
                    print('Entry "{}" unconsumed repo: {}'.format(info['Name'], info[field]))

    # sort them alphabetically (and remove duplicates)
    for k, v in primary_repos.items():
        primary_repos[k] = sorted(set(v))

    # statistics of gits
    git_repos = primary_repos['git']
    print('{} Git repositories'.format(len(git_repos)))
    for domain in (
            'repo.or.cz', 'anongit.kde.org', 'bitbucket.org', 'git.code.sf.net', 'git.savannah', 'git.tuxfamily',
            'github.com',
            'gitlab.com', 'gitlab.com/osgames', 'gitlab.gnome.org'):
        print('{} on {}'.format(sum(1 if domain in x else 0 for x in git_repos), domain))

    # write them to code/git
    json_path = os.path.join(c.root_path, 'code', 'archives.json')
    text = json.dumps(primary_repos, indent=1)
    utils.write_text(json_path, text)


def export_git_code_repositories_json():
    """

    """

    urls = []
    field = 'code repository'

    # for every entry, get all git
    for info in infos:
        # if field 'Code repository' is available
        if field in info:
            repos = info[field]
            if repos:
                # take the first
                repo = repos[0]
                url = git_repo(repo)
                if url:
                    urls.append(url)

    # sort them alphabetically (and remove duplicates)
    urls.sort()

    # write them to code/git
    json_path = os.path.join(c.root_path, 'code', 'git_repositories.json')
    text = json.dumps(urls, indent=1)
    utils.write_text(json_path, text)


def check_validity_backlog():
    import requests

    # read backlog and split
    file = os.path.join(c.root_path, 'code', 'backlog.txt')
    text = utils.read_text(file)
    urls = text.split('\n')
    urls = [x.split(' ')[0] for x in urls]

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=5)
        except Exception as e:
            print('{} gave error: {}'.format(url, e))
        else:
            if r.status_code != requests.codes.ok:
                print('{} returned status code: {}'.format(url, r.status_code))

            if r.is_redirect or r.history:
                print('{} redirected to {}, {}'.format(url, r.url, r.history))


def check_code_dependencies(infos):
    """

    """

    # get all names of frameworks and library also using osg.code_dependencies_aliases
    valid_dependencies = list(utils.constants.general_code_dependencies_without_entry.keys())
    for info in infos:
        if any((x in ('framework', 'library', 'game engine') for x in info['keywords'])):
            name = info['Name']
            if name in utils.constants.code_dependencies_aliases:
                valid_dependencies.extend(utils.constants.code_dependencies_aliases[name])
            else:
                valid_dependencies.append(name)

    # get all referenced code dependencies
    referenced_dependencies = {}
    for info in infos:
        deps = info.get('code dependencies', [])
        for dependency in deps:
            if dependency in referenced_dependencies:
                referenced_dependencies[dependency] += 1
            else:
                referenced_dependencies[dependency] = 1

    # delete those that are valid dependencies
    referenced_dependencies = [(k, v) for k, v in referenced_dependencies.items() if k not in valid_dependencies]

    # sort by number
    referenced_dependencies.sort(key=lambda x: x[1], reverse=True)

    # print out
    print('Code dependencies not included as entry')
    for dep in referenced_dependencies:
        print('{} ({})'.format(*dep))





