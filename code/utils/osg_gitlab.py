"""
Everything specific to the Gitlab API (via Python GitLab https://python-gitlab.readthedocs.io/en/stable/)
"""

from dateutil import parser
from gitlab import Gitlab

def normalize_repo_name(repo):
    """
    Bring repo to style xxx/yyy
    """
    prefix = 'https://gitlab.com/'
    if repo.startswith(prefix):
        repo = repo[len(prefix):]
    suffix = '.git'
    if repo.endswith(suffix):
        repo = repo[:-len(suffix)]
    return repo


def retrieve_repo_info(repos, token=None):
    """

    :param repos:
    :param token:
    :return:
    """
    single_repo = isinstance(repos, str)
    if single_repo:
        repos = (repos,)
    result = []
    gl = Gitlab('https://gitlab.com')
    for repo in repos:
        repo = normalize_repo_name(repo)
        # get project
        p = gl.projects.get(repo)
        e = {'description': p.description, 'created': parser.parse(p.created_at), 'contributors': p.repository_contributors(get_all=True), 'forks': p.forks_count, 'name': p.name, 'last modified': parser.parse(p.last_activity_at), 'stars': p.star_count, 'languages': p.languages(get_all=True)}
        result.append(e)
    if single_repo:
        result = result[0]
    return result