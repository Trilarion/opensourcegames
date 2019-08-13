"""
Specific functions working on the games.
"""

import re
from utils.utils import *

essential_fields = ('Home', 'State', 'Keywords', 'Code repository', 'Code language', 'Code license')
valid_fields = ('Home', 'Media', 'State', 'Play', 'Download', 'Platform', 'Keywords', 'Code repository', 'Code language',
'Code license', 'Code dependencies', 'Assets license', 'Build system', 'Build instructions')
valid_platforms = ('Windows', 'Linux', 'macOS', 'Android', 'Browser')
recommended_keywords = ('action', 'arcade', 'adventure', 'visual novel', 'sports', 'platform', 'puzzle', 'role playing', 'simulation', 'strategy', 'card game', 'board game', 'music', 'educational', 'tool', 'game engine', 'framework', 'library')


def entry_iterator(games_path):
    """

    """

    # get all entries (ignore everything starting with underscore)
    entries = os.listdir(games_path)
    entries = (x for x in entries if not x.startswith('_'))

    # iterate over all entries
    for entry in entries:
        entry_path = os.path.join(games_path, entry)

        # read entry
        content = read_text(entry_path)

        # yield
        yield entry, entry_path, content


def parse_entry(content):
    """
    Returns a dictionary of the features of the content
    """

    info = {}

    # read name
    regex = re.compile(r"^# (.*)") # start of content, starting with "# " and then everything until the end of line
    matches = regex.findall(content)
    if len(matches) != 1 or not matches[0]:
        raise RuntimeError('Name not found in entry "{}"'.format(content))
    info['name'] = matches[0]

    # read description
    regex = re.compile(r"^.*\n\n_(.*)_\n") # third line from top, everything between underscores
    matches = regex.findall(content)
    if len(matches) != 1 or not matches[0]:
        raise RuntimeError('Description not found in entry "{}"'.format(content))
    info['description'] = matches[0]

    # first read all field names
    regex = re.compile(r"^- (.*?): ", re.MULTILINE) # start of each line having "- ", then everything until a colon, then ": "
    fields = regex.findall(content)

    # check that essential fields are there
    for field in essential_fields:
        if field not in fields:
            raise RuntimeError('Essential field "{}" missing in entry "{}"'.format(field, info['name']))

    # check that all fields are valid fields and are existing in that order
    index = 0
    for field in fields:
        while index < len(valid_fields) and field != valid_fields[index]:
            index += 1
        if index == len(valid_fields):
            raise RuntimeError('Field "{}" in entry "{}" either misspelled or in wrong order'.format(field, info['name']))

    # iterate over found fields
    for field in fields:
        regex = re.compile(r"- {}: (.*)".format(field))
        matches = regex.findall(content)
        if len(matches) != 1:
            # every field should only be present once
            raise RuntimeError('Field "{}" in entry "{}" exist multiple times.'.format(field, info['name']))
        v = matches[0]

        # first store as is
        info[field.lower()+'-raw'] = v

        # remove parenthesis with content
        v = re.sub(r'\([^)]*\)', '', v)

        # split on ','
        v = v.split(',')

        # strip
        v = [x.strip() for x in v]

        # remove all being false (empty) that were for example just comments
        v = [x for x in v if x]

        # if entry is of structure <..> remove <>
        v = [x[1:-1] if x[0] is '<' and x[-1] is '>' else x for x in v]

        # empty fields will not be stored
        if not v:
            continue

        # store in info
        info[field.lower()] = v

    # now checks on the content of fields

    # name should not have spaces at the begin or end
    v = info['name']
    if len(v) != len(v.strip()):
        raise RuntimeError('No leading or trailing spaces in the entry name, "{}"'.format(info['name']))

    # state (essential field) must contain either beta or mature but not both, but at least one
    v = info['state']
    for t in v:
        if t != 'beta' and t != 'mature' and not t.startswith('inactive since '):
            raise RuntimeError('Unknown state tage "{}" in entry "{}"'.format(t, info['name']))
    if 'beta' in v != 'mature' in v:
        raise RuntimeError('State must be one of <"beta", "mature"> in entry "{}"'.format(info['name']))

    # extract inactive year
    phrase = 'inactive since '
    inactive_year = [x[len(phrase):] for x in v if x.startswith(phrase)]
    assert len(inactive_year) <= 1
    if inactive_year:
        info['inactive'] = inactive_year[0]

    # urls in home, download, play and code repositories must start with http or https (or git) and should not contain spaces
    for field in ['home', 'download', 'play', 'code repository']:
        if field in info:
            for url in info[field]:
                if not (url.startswith('http://') or url.startswith('https://') or url.startswith('git://')):
                    raise RuntimeError('URL "{}" in entry "{}" does not start with http'.format(url, info['name']))
                if ' ' in url:
                    raise RuntimeError('URL "{}" in entry "{}" contains a space'.format(url, info['name']))

    # github repositories should end on .git
    if 'code repository' in info:
        for repo in info['code repository']:
            if repo.startswith('https://github.com/') and not repo.endswith('.git'):
                raise RuntimeError('Github repo {} in entry "{}" should end on .git.'.format(repo, info['name']))

    # check that all platform tags are valid tags and are existing in that order
    if 'platform' in info:
        index = 0
        for platform in info['platform']:
            while index < len(valid_platforms) and platform != valid_platforms[index]:
                index += 1
            if index == len(valid_platforms):
                raise RuntimeError('Platform tag "{}" in entry "{}" either misspelled or in wrong order'.format(platform, info['name']))

    # there must be at least one keyword
    if 'keywords' not in info:
        raise RuntimeError('Need at least one keyword in entry "{}"'.format(info['name']))

    # check for existence of at least one recommended keywords
    fail = True
    for recommended_keyword in recommended_keywords:
        if recommended_keyword in info['keywords']:
            fail = False
            break
    if fail:
        raise RuntimeError('Entry "{}" contains no recommended keyword'.format(info['name']))

    return info


def assemble_infos(games_path):
    """
    Parses all entries and assembles interesting infos about them.
    """

    print('assemble game infos')

    # a database of all important infos about the entries
    infos = []

    # iterate over all entries
    for entry, _, content in entry_iterator(games_path):

        # parse entry
        info = parse_entry(content)

        # add file information
        info['file'] = entry

        # add to list
        infos.append(info)

    return infos