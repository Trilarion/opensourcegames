"""
Everything specific to the Github API (via PyGithub).
"""

from github import Github


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


def retrieve_repo_info(repos):
    """
    For a list of Github repos, retrieves repo information.

    Repos must be have the style xxx/yyy example: "PyGithub/PyGithub"
    """
    single_repo = isinstance(repos, str)
    if single_repo:
        repos = (repos,)
    result = []
    g = Github()
    for repo in repos:
        repo = normalize_repo_name(repo)
        r = g.get_repo(repo)
        e = {'archived': r.archived, 'contributors': repo_get_contributors(r), 'description': r.description,
             'language': r.language, 'last modified': r.last_modified, 'open issues count': r.open_issues_count,
             'stars count': r.stargazers_count, 'topics': r.topics, 'repo': repo}
        result.append(e)
    if single_repo:
        result = result[0]
    return result
