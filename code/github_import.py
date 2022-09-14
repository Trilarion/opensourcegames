"""
Uses the Github API to learn more about the Github projects.

Updates for example, the starring information.
"""

# TODO remove developers again?
# TODo try to identify main developers (number of commits or change of lines...)

import os
import json
from random import sample
from utils import constants as c, utils, osg, osg_parse, osg_github

gh_entries_file = os.path.join(c.code_path, 'github_entries.txt')
prefix = 'https://github.com/'
MINIMAL_CONTRIBUTIONS = 5

blog_alias = {'http://k776.tumblr.com/': 'https://k776.tumblr.com/',
              'http://timpetricola.com': 'https://timpetricola.com',
              'http:/code.schwitzer.ca': 'https://code.schwitzer.ca/',
              'http:\\www.vampier.net': 'https://www.vampier.net/'}
ignored_blogs = ('https://uto.io',)

ignored_languages = ('CSS', 'HTML', 'CMake', 'XSLT', 'ShaderLab')
language_aliases = {'VBA': 'Visual Basic', 'Common Lisp': 'Lisp', 'Game Maker Language': 'Game Maker Script',
                    'NewLisp': 'Lisp', 'Awk': 'AWK', 'Visual Basic': 'Basic', 'FreeBasic': 'Basic'}

# these gave some errors (but you may try them again or remove them from this list)
ignored_repos = ('https://github.com/jtc0de/Blitwizard.git',
                 'https://github.com/KaidemonLP/Open-Fortress-Source.git',
                 'https://github.com/danielcrenna/TrueCraft.git')

name_aliases = {'Andreas Rosdal': 'Andreas Røsdal', 'davefancella': 'Dave Fancella', 'himiloshpetrov': 'Milosh Petrov',
                'Jeremy Monin': 'Jeremy D. Monin', 'lennertclaeys': 'Lennert Claeys',
                'malignantmanor': 'Malignant Manor',
                'turulomio': 'Turulomio', '_Shaman': 'Shaman', 'alexandreSalconiDenis': 'Alexandre Salconi-Denis',
                'buginator': 'Buginator', 'CiprianKhlud': 'Ciprian Khlud', 'dericpage': 'Deric Page',
                'DI Murat Sari': 'Murat Sari', 'DolceTriade': 'Dolce Triade', 'DreamingPsion': 'Dreaming Psion',
                'edwardlii': 'Edward Lii', 'erik-vos': 'Erik Vos', 'joevenzon': 'Joe Venzon', 'noamgat': 'Noam Gat',
                'Dr. Martin Brumm': 'Martin Brumm', 'South Bound Apps (Android)': 'South Bound Apps'}


def collect_github_entries():
    """
    Reads the entries of the database and collects all entries with a Github repository. Just for convenience to limit
    the number of entries to iterate on later.
    """

    # read entries
    entries = osg.read_entries()
    print('{} entries read'.format(len(entries)))

    # loop over entries
    files = []
    for entry in entries:
        urls = [x for x in entry.get('Code repository', []) if x.startswith(prefix)]
        if urls:
            files.append(entry['File'])

    # write to file
    print('{} entries with github repos'.format(len(files)))
    utils.write_text(gh_entries_file, json.dumps(files, indent=1))


def github_import():
    """
    Import various information from Github repositories (like contributors) or stars for Github repos
    """

    files = json.loads(utils.read_text(gh_entries_file))

    # Github rate limiting limits us to 1000 queries an hour, so take a random sampling
    if len(files) > 1000:
        files = sample(files, 5)


    all_developers = osg.read_developers()
    print(' {} developers read'.format(len(all_developers)))

    # loop over each entry
    for index, file in enumerate(files):
        try:
            print(' process {} ({})'.format(file, index))

            # read entry
            entry = osg.read_entry(file)
            code_repositories = entry['Code repository']
            repos = [x for x in code_repositories if x.startswith(prefix)]
            repos[0] += ' @add'
            repos = [x for x in repos if '@add' in x]
            repos = [x.split(' ')[0] for x in repos]
            repos = [x for x in repos if x not in ignored_repos]
            for repo in repos:
                print('  GH repo {}'.format(repo))
                token = os.environ["GITHUB_TOKEN"]
                if not token:
                    private_properties = json.loads(utils.read_text(c.private_properties_file))
                    token = private_properties['github-token']

                info = osg_github.retrieve_repo_info(repo, token=token)

                new_comments = []
                # is archived
                if info['archived']:
                    if not osg.is_inactive(entry):
                        print('warning: repo is archived but not inactive state, check state')
                    # add archive to repo comment
                    new_comments.append('@archived')
                # TODO check for repos that aren't archived anymore but are marked as such

                # add created comment
                new_comments.append('@created {}'.format(info['created'].year))

                # add stars
                new_comments.append('@stars {}'.format(info['stars']))

                # add forks
                new_comments.append('@forks {}'.format(info['forks']))

                # update comment
                for r in code_repositories:
                    if r.startswith(repo):
                        break
                comments = r.comment
                if comments:
                    comments = comments.split(',')
                    comments = [c.strip() for c in comments]
                    comments = [c for c in comments if not c.startswith('@')]  # delete old ones
                    comments += new_comments
                else:
                    comments = new_comments
                r.comment = ', '.join(comments)

                # language in languages
                language = info['language']
                language = language_aliases.get(language, language)
                if language and language not in entry['Code language'] and language not in ignored_languages:
                    entry['Code language'].append(language)
                    print('  added to languages: {}'.format(language))

                # contributors
                for contributor in info['contributors']:
                    if contributor.type != 'User':
                        continue
                    if contributor.contributions < MINIMAL_CONTRIBUTIONS:
                        continue
                    # contributor.login/name/blog
                    name = contributor.name
                    if not name:
                        name = contributor.login
                    name = name_aliases.get(name, name)
                    name = name.strip()  # sometimes they have trailing spaces (for whatever reason)
                    nickname = '{}@GH'.format(contributor.login)
                    blog = contributor.blog
                    if blog:
                        blog = blog_alias[blog] if blog in blog_alias else blog
                        if not blog.startswith('http'):
                            blog = 'https://' + blog
                        if blog in ignored_blogs:
                            blog = None

                    # look up author in entry developers
                    if name not in entry.get('Developer', []):
                        print('   dev "{}" added to entry {}'.format(name, file))
                        entry['Developer'] = entry.get('Developer', []) + [name]

                    # look up author in developers data base
                    if name in all_developers:
                        dev = all_developers[name]
                        if not nickname in dev.get('Contact', []):
                            print(' existing dev "{}" added nickname ({}) to developer database'.format(name, nickname))
                            # check that name has not already @GH contact
                            if any(x.endswith('@GH') for x in dev.get('Contact', [])):
                                print('warning: already GH contact')
                            dev['Contact'] = dev.get('Contact', []) + [nickname]
                        if blog and blog not in dev.get('Home', []):
                            dev['Home'] = dev.get('Home', []) + [blog]
                        if entry['Title'] not in dev['Games']:
                            dev['Games'].append(entry['Title'])
                    else:
                        print('   dev "{}" ({}) added to developer database'.format(name, nickname))
                        all_developers[name] = {'Name': name, 'Contact': [nickname], 'Games': [entry['Title']]}
                        if blog:
                            all_developers[name]['Home'] = [blog]

            entry['Code repository'] = code_repositories
            osg.write_entry(entry)
        except:
            pass # KEep going to other entries
    
    # shorten file list
    utils.write_text(gh_entries_file, json.dumps(files[index:], indent=1))

    osg.write_developers(all_developers)
    print('developers database updated')


def github_starring_synchronization():
    """
    Which Github repositories haven't I starred yet.
    """
    private_properties = json.loads(utils.read_text(c.private_properties_file))

    files = json.loads(utils.read_text(gh_entries_file))

    # loop over each entry and collect list of repos
    all_repos = []
    for index, file in enumerate(files):
        # read entry
        entry = osg.read_entry(file)

        # get repos
        code_repositories = entry.get('Code repository', [])
        repos = [x for x in code_repositories if x.startswith(prefix)]
        repos[0] += ' @add'
        repos = [x for x in repos if '@add' in x]
        repos = [x.split(' ')[0] for x in repos]
        repos = [x for x in repos if x not in ignored_repos]
        all_repos.extend(repos)
    all_repos = set(all_repos)
    print('found {} Github repos'.format(len(all_repos)))

    # get my Github user
    user = osg_github.get_user(private_properties['github-name'], token=private_properties['github-token'])

    # get starred repos
    starred = user.get_starred()
    starred = [repo.clone_url for repo in starred]
    starred = set(starred)
    print('starred {} Github repos'.format(len(starred)))

    # and now the difference
    unstarred = all_repos - starred
    print('not yet starred {} repos'.format(len(unstarred)))
    print(', '.join(unstarred))


if __name__ == "__main__":
    # collect entries (run this only once)
    collect_github_entries()

    # import information from gh
    github_import()

    # which github repos haven't I starred
    # github_starring_synchronization()
