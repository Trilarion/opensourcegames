"""
Uses the Gitlab API to learn more about the Gitlab projects.
"""

import json
from utils import constants as c, utils, osg, osg_gitlab, osg_parse

gl_entries_file = c.code_path / 'gitlab_entries.txt'
prefix = 'https://gitlab.com/'

# these may give errors and should be ignored
ignored_repos = ()


def collect_gitlab_entries():
    """
    Reads the entries of the database and collects all entries with a Gitlab repository. Just for convenience to limit
    the number of entries to iterate on later.
    """

    # read entries
    entries = osg.read_entries()
    print(f'{len(entries)} entries read')

    # loop over entries
    filenames = []
    for entry in entries:
        urls = [x for x in entry.get('Code repository', []) if x.startswith(prefix)]
        if urls:
            filenames.append(entry['File'].name)

    # write to file
    print(f'{len(filenames)} entries with gitlab repos')
    utils.write_text(gl_entries_file, json.dumps(filenames, indent=1))


def gitlab_import():
    """
    Import various information from Gitlab repositories (like contributors) or stars for Gitlab repos
    """
    private_properties = json.loads(utils.read_text(c.private_properties_file))

    files = json.loads(utils.read_text(gl_entries_file))

    all_developers = osg.read_developers()
    print(f' {len(all_developers)} developers read')

    # all exceptions that happen will be eaten (but will end the execution)
    try:
        # loop over each entry
        for index, file in enumerate(files):
            print(f' process {file} ({index})')

            # read entry
            entry = osg.read_entry(file)
            code_repositories = entry['Code repository']
            repos = [x for x in code_repositories if x.startswith(prefix)]
            repos[0] += ' @add'
            repos = [x for x in repos if '@add' in x]
            repos = [x.split(' ')[0] for x in repos]
            repos = [x for x in repos if x not in ignored_repos]
            for repo in repos:
                print(f'  GL repo {repo}')

                info = osg_gitlab.retrieve_repo_info(repo)

                # new comment @created, stars, forks
                new_comments = [f"@created {info['created'].year}", f"@stars {info['stars']}", f"@forks {info['forks']}"]

                # search for repository
                for idx, r in enumerate(code_repositories):
                    if r.startswith(repo):
                        if not isinstance(r, osg_parse.Value):  # if there was no comment yet, make one
                            r = osg_parse.Value(r)
                        code_repositories[idx] = r  # need to store it, otherwise changes will be lost
                        break

                # update comment
                comments = r.comment
                if comments:
                    comments = comments.split(',')
                    comments = [comment.strip() for comment in comments]
                    comments = [comment for comment in comments if not comment.startswith('@')]  # delete old ones
                    comments += new_comments
                else:
                    comments = new_comments
                r.comment = ', '.join(comments)

                # language in languages
                for language, usage in info['languages'].items():
                    if language in c.known_languages and usage > 5 and language not in entry['Code language']:
                        entry['Code language'].append(language)
                        print(f'  added to languages: {language}')

            entry['Code repository'] = code_repositories
            osg.write_entry(entry)
    except RuntimeError as e:
        print(f"Error processing repo {file}")
        raise e
    finally:
        # shorten file list
        utils.write_text(gl_entries_file, json.dumps(files[index:], indent=1))

        # osg.write_developers(all_developers)
        # print('developers database updated')


def gitlab_starring_synchronization():
    """
    Which Gitlab repositories have I not starred yet.
    """
    private_properties = json.loads(utils.read_text(c.private_properties_file))

    files = json.loads(utils.read_text(gl_entries_file))

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
    print(f'found {len(all_repos)} Gitlab repos')

    # TODO not finished


if __name__ == "__main__":
    # collect entries (run this only once)
    # collect_gitlab_entries()

    # import information from Gitlab
    gitlab_import()

    # which Gitlab repos have I not starred?
    # gitlab_starring_synchronization()