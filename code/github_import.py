"""
Uses the Github API to learn more about the Github projects.
"""

import os
import json
from utils import constants as c, utils, osg, osg_parse, osg_github

gh_entries_file = os.path.join(c.code_path, 'github_entries.txt')
prefix = 'https://github.com/'


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
            for repo in repos:
                print('  GH repo {}'.format(repo))

                info = osg_github.retrieve_repo_info(repo)

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
                    if r.value == repo:
                        break
                comments = r.comment
                if comments:
                    comments = comments.split(',')
                    comments = [c.strip() for c in comments if not c.startswith('@')]
                r.comment = ', '.join(comments + new_comments)

                # language in languages
                language = info['language']
                if language not in entry['Code language']:
                    entry['Code language'].append(language)

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
                    nickname = '{}@GH'.format(contributor.login)

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
                        if contributor.blog and contributor.blog not in dev.get('Home', []):
                            dev['Home'] = dev.get('Home', []) + [contributor.blog]
                    else:
                        print('   dev "{}" ({}) added to developer database'.format(name, nickname))
                        all_developers[name] = {'Name': name, 'Contact': [nickname], 'Games': [entry['Title']]}
                        if contributor.blog:
                            all_developers[name]['Home'] = [contributor.blog]


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
