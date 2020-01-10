"""
Everything specific to the Github API (via PyGithub).
"""

from github import Github


def retrieve_repo_info(repos):
    """
    For a list of Github repos, retrieves repo information
    """
    result = []
    g = Github()
    for repo in repos:
        r = g.get_repo(repo)
        e = {'archived': r.archived, 'description': r.description, 'language': r.language,
             'last modified': r.last_modified, 'open issues count': r.open_issues_count,
             'stars count': r.stargazers_count, 'topics': r.topics, 'repo': repo}
        result.append(e)
    return result
