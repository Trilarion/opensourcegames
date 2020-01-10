"""

"""


def derive_folder_name(url, replaces):
    """

    """
    sanitize = lambda x: x.replace('/', '.')
    for service in replaces:
        if url.startswith(service):
            url = replaces[service] + url[len(service):]
            return sanitize(url)
    for generic in ['http://', 'https://', 'git://', 'svn://']:
        if url.startswith(generic):
            url = url[len(generic):]
            return sanitize(url)
    raise Exception('malformed url: {}'.format(url))


def git_folder_name(url):
    """

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