"""
Some utilities for the archiving of the repositories.
"""


def derive_folder_name(url, replaces):
    """
    Creates a folder name from an url that is somewhat shortened. Uses replacement dictionary.
    """
    # in any case we replace all slashes with dots
    sanitize = lambda x: x.replace('/', '.')
    # for a given set of urls (known services), replace them with a short form
    for service in replaces:
        if url.startswith(service):
            url = replaces[service] + url[len(service):]
            return sanitize(url)
    # not found, just cut the initial http
    for generic in ['http://', 'https://', 'git://', 'svn://']:
        if url.startswith(generic):
            url = url[len(generic):]
            return sanitize(url)
    # none of the above worked, raise an error
    raise RuntimeError(f'malformed url: {url}')


def git_folder_name(url):
    """
    For git with a standard replacement dictionary, derive a canonical folder name used for archiving.
    """
    replaces = {
        'https://github.com': 'github',
        'https://git.code.sf.net/p': 'sourceforge',
        'https://git.tuxfamily.org': 'tuxfamily',
        'https://git.savannah.gnu.org/git': 'savannah.gnu',
        'https://gitlab.com': 'gitlab',
        'https://gitorious.org': 'gitorious',
        'https://anongit.': '',
        'https://bitbucket.org': 'bitbucket',
        'https://gitlab.gnome.org': 'gnome'
    }
    return derive_folder_name(url, replaces)
