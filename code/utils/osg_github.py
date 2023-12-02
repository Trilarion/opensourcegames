"""
Everything specific to the GitHub API (via PyGithub - https://pygithub.readthedocs.io/en/latest/index.html).
"""

from github import Github, GithubException
from github.GithubException import UnknownObjectException


def normalize_repo_name(repo):
    """
    Bring repo to style xxx/yyy
    """
    prefix = 'https://github.com/'
    if repo.startswith(prefix):
        repo = repo[len(prefix):]
    suffix = '.git'
    if repo.endswith(suffix):
        repo = repo[:-len(suffix)]
    return repo


def repo_get_contributors(repo):
    contributors = []
    c = repo.get_contributors()
    for i in range(c.totalCount):
        contributors.append(c[i])
    return contributors


def retrieve_repo_info(repos, token=None):
    """
    For a list of GitHub repos, retrieves repo information.

    Repos must have the style xxx/yyy example: "PyGithub/PyGithub"
    """
    single_repo = isinstance(repos, str)
    if single_repo:
        repos = (repos,)
    result = []
    if token:
        g = Github(token)
    else:
        g = Github()
    for repo in repos:
        repo = normalize_repo_name(repo)
        try:
            # get repo
            r = g.get_repo(repo)
        except GithubException as e:
            if type(e) == UnknownObjectException:
                print(f'repo "{repo}" does not exist on GitHub')
                return None
            else:
                raise RuntimeError(e)
        e = {'archived': r.archived, 'contributors': repo_get_contributors(r), 'created': r.created_at, 'description': r.description,
             'forks': r.forks_count, 'language': r.language, 'last modified': r.last_modified, 'name': r.name,
             'open issues count': r.open_issues_count, 'owner': r.owner, 'stars': r.stargazers_count, 'topics': r.get_topics(), 'repo': repo}
        result.append(e)
    if single_repo:
        result = result[0]
    return result


def get_user(login, token=None):
    if token:
        g = Github(token)
    else:
        g = Github()
    user = g.get_user(login)
    return user
