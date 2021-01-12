"""
Uses the Github API to learn more about the Github projects.
"""

import os
import json
from utils import constants as c, utils, osg, osg_parse, osg_github

gh_entries_file = os.path.join(c.code_path, 'github_entries.txt')
prefix = 'https://github.com/'

blog_alias = {'http://k776.tumblr.com/': 'https://k776.tumblr.com/', 'http://timpetricola.com': 'https://timpetricola.com',
              'http:/code.schwitzer.ca': 'https://code.schwitzer.ca/', 'http:\\www.vampier.net': 'https://www.vampier.net/'}
ignored_blogs = ('https://uto.io',)

ignored_languages = ('CSS', 'HTML', 'CMake', 'XSLT', 'ShaderLab')
language_aliases = {'VBA': 'Visual Basic', 'Common Lisp': 'Lisp', 'Game Maker Language': 'Game Maker Script', 'NewLisp': 'Lisp'}

ignored_repos = ('https://github.com/jtc0de/Blitwizard.git','https://github.com/IceReaper/KKnD.git',
                 'https://github.com/KaidemonLP/Open-Fortress-Source.git', 'https://github.com/danielcrenna/TrueCraft.git')

name_aliases = {'Andreas Rosdal': 'Andreas Røsdal', 'davefancella': 'Dave Fancella', 'himiloshpetrov': 'Milosh Petrov',
                'Jeremy Monin': 'Jeremy D. Monin', 'lennertclaeys': 'Lennert Claeys', 'malignantmanor': 'Malignant Manor',
                'turulomio': 'Turulomio', '_Shaman': 'Shaman', 'alexandreSalconiDenis': 'Alexandre Salconi-Denis',
                'buginator': 'Buginator', 'CiprianKhlud': 'Ciprian Khlud', 'dericpage': 'Deric Page',
                'DI Murat Sari': 'Murat Sari', 'DolceTriade': 'Dolce Triade', 'DreamingPsion': 'Dreaming Psion',
                'edwardlii': 'Edward Lii', 'erik-vos': 'Erik Vos', 'joevenzon': 'Joe Venzon', 'noamgat': 'Noam Gat',
                'Dr. Martin Brumm': 'Martin Brumm'}


def collect_github_entries():
    """
    Reads the entries of the database and collects all entries with github as repository
    """

    # read entries
    entries = osg.read_entries()
    print('{} entries read'.format(len(entries)))

    # loop over entries
    files = []
    for entry in entries:
        urls = [x for x in entry['Code repository'] if x.startswith(prefix)]
        if urls:
            files.append(entry['File'])

    # write to file
    print('{} entries with github repos'.format(len(files)))
    utils.write_text(gh_entries_file, json.dumps(files, indent=1))


def github_import():
    """

    :return:
    """
    private_properties = json.loads(utils.read_text(c.private_properties_file))

    files = json.loads(utils.read_text(gh_entries_file))

    all_developers = osg.read_developers()
    print(' {} developers read'.format(len(all_developers)))

    # all exceptions that happen will be eaten (but will end the execution)
    try:
        # loop over each entry
        for index, file in enumerate(files):
            print(' process {}'.format(file))

            # read entry
            entry = osg.read_entry(file)
            code_repositories = entry['Code repository']
            repos = [x.value for x in code_repositories if x.startswith(prefix)]
            repos[0] += ' @add'
            repos = [x for x in repos if '@add' in x]
            repos = [x.split(' ')[0] for x in repos]
            repos = [x for x in repos if x not in ignored_repos]
            for repo in repos:
                print('  GH repo {}'.format(repo))

                info = osg_github.retrieve_repo_info(repo, private_properties['github-token'])

                new_comments = []
                # is archived
                if info['archived']:
                    if not osg.is_inactive(entry):
                        print('warning: repo is archived but not inactive state??')
                    # add archive to repo comment
                    new_comments.append('@archived')

                # add created comment
                new_comments.append('@created {}'.format(info['created'].year))

                # add stars
                new_comments.append('@stars {}'.format(info['stars']))

                # add forks
                new_comments.append('@forks {}'.format(info['forks']))

                # update comment
                for r in code_repositories:
                    if r.value.startswith(repo):
                        break
                comments = r.comment
                if comments:
                    comments = comments.split(',')
                    comments = [c.strip() for c in comments]
                    comments = [c for c in comments if not c.startswith('@')] # delete old ones
                    comments += new_comments
                else:
                    comments = new_comments
                r.comment = ', '.join(comments)

                # language in languages
                language = info['language']
                language = language_aliases.get(language, language)
                if language and language not in entry['Code language'] and language not in ignored_languages:
                    entry['Code language'].append(osg_parse.ValueWithComment(language))
                    print('  added to languages: {}'.format(language))

                # contributors
                for contributor in info['contributors']:
                    if contributor.type != 'User':
                        continue
                    if contributor.contributions < 4:
                        continue
                    # contributor.login/name/blog
                    name = contributor.name
                    if not name:
                        name = contributor.login
                    name = name_aliases.get(name, name)
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
                        entry['Developer'] = entry.get('Developer', []) + [osg_parse.ValueWithComment(name)]

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
                        # TODO add to games entries!
                    else:
                        print('   dev "{}" ({}) added to developer database'.format(name, nickname))
                        all_developers[name] = {'Name': name, 'Contact': [nickname], 'Games': [entry['Title']]}
                        if blog:
                            all_developers[name]['Home'] = [blog]


            entry['Code repository'] = code_repositories
            osg.write_entry(entry)
    except:
        raise
    finally:
        # shorten file list
        utils.write_text(gh_entries_file, json.dumps(files[index:], indent=1))

        osg.write_developers(all_developers)
        print('developers database updated')


if __name__ == "__main__":

    # collect entries
    # collect_github_entries()

    # import information from gh
    github_import()
