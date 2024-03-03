"""
Specific functions working on the games.
"""

import re
import pathlib
from difflib import SequenceMatcher
from utils import utils, osg_parse, constants as c

regex_sanitize_name = re.compile(r"[^A-Za-z 0-9-+]+")
regex_sanitize_name_space_eater = re.compile(r" +")


def name_similarity(a, b):
    return SequenceMatcher(None, str.casefold(a), str.casefold(b)).ratio()


def entry_iterator():
    """

    """

    # get all entries (ignore everything starting with underscore)
    entries = c.entries_path.iterdir()

    # iterate over all entries
    for entry in entries:
        # ignore directories ("tocs" for example)
        if entry.is_dir():
            continue

        # read entry
        content = utils.read_text(entry)

        # yield
        yield entry, entry.name, content


def canonical_name(name):
    """
    Derives a canonical name from an actual name (suitable for file names, anchor names, ...)
    """
    name = name.casefold()
    name = name.replace('ö', 'o').replace('ä', 'a').replace('ü', 'u')
    name = regex_sanitize_name.sub('', name)
    name = regex_sanitize_name_space_eater.sub('_', name)
    name = name.replace('_-_', '-')
    name = name.replace('--', '-').replace('--', '-')

    return name


def read_developers():
    """

    :return:
    """
    grammar_file = c.code_path / 'grammar_listing.lark'
    developers = osg_parse.read_and_parse(c.developer_file, grammar_file, osg_parse.ListingTransformer)

    # now developers is a list of dictionaries for every entry with some properties

    # check for duplicate names entries
    names = [dev['Name'] for dev in developers]
    duplicate_names = (name for name in names if names.count(name) > 1)
    duplicate_names = set(duplicate_names)  # to avoid duplicates in duplicate_names
    if duplicate_names:
        print(f"Warning: duplicate developer names: {', '.join(duplicate_names)}")

    # check for essential, valid fields
    for dev in developers:
        # check that essential fields are existing
        for field in c.essential_developer_fields:
            if field not in dev:
                raise RuntimeError(f"Essential field \"{field}\" missing in developer {dev['Name']}")
        # check that all fields are valid fields
        for field in dev.keys():
            if field not in c.valid_developer_fields:
                raise RuntimeError(f"Invalid field \"{field}\" in developer {dev['Name']}.")
        # url fields
        for field in c.url_developer_fields:
            if field in dev:
                content = dev[field]
                if any(not (x.startswith('http://') or x.startswith('https://')) for x in content):
                    raise RuntimeError(f"Invalid URL in field \"{field}\" in developer {dev['Name']}.")

    # convert to dictionary
    developers = {x['Name']: x for x in developers}

    return developers


def write_developers(developers):
    """

    :return:
    """
    # convert dictionary to list
    developers = list(developers.values())

    # comment
    content = f'{c.generic_comment_string}\n'

    # number of developer
    content += f'# Developer [{len(developers)}]\n\n'

    # sort by name
    developers.sort(key=lambda x: str.casefold(x['Name']))

    # iterate over them
    for dev in developers:
        keys = list(dev.keys())
        # developer name
        content += f"## {dev['Name']} [{len(dev['Games'])}]\n\n"
        keys.remove('Name')

        # all the remaining in alphabetical order, but 'games' first
        keys.remove('Games')
        keys.sort()
        keys = ['Games'] + keys
        for field in keys:
            value = dev[field]
            # lists get special treatment
            if isinstance(value, list):
                # remove duplicates
                value = list(set(value))
                # sort
                value.sort(key=str.casefold)
                # surround those with a comma with quotation marks
                value = [x if not ',' in x else f'"{x}"' for x in value]
                value = ', '.join(value)
            content += f'- {field}: {value}\n'
        content += '\n'

    # write
    utils.write_text(c.developer_file, content)


def read_inspirations():
    """
    Reads the info list about the games originals/inspirations from inspirations.md using the Lark parser grammar
    in grammar_listing.lark
    :return:
    """
    # read inspirations

    # read and parse inspirations
    grammar_file = c.code_path / 'grammar_listing.lark'
    inspirations = osg_parse.read_and_parse(c.inspirations_file, grammar_file, osg_parse.ListingTransformer)

    # now inspirations is a list of dictionaries for every entry with some properties

    # check for duplicate names entries
    names = [inspiration['Name'] for inspiration in inspirations]
    duplicate_names = (name for name in names if names.count(name) > 1)
    duplicate_names = set(duplicate_names)  # to avoid duplicates in duplicate_names
    if duplicate_names:
        raise RuntimeError(f"Duplicate inspiration names: {', '.join(duplicate_names)}")

    # check for essential, valid fields
    for inspiration in inspirations:
        # check that essential fields are existing
        for field in c.essential_inspiration_fields:
            if field not in inspiration:
                raise RuntimeError(f"Essential field \"{field}\" missing in inspiration {inspiration['Name']}")
        # check that all fields are valid fields
        for field in inspiration.keys():
            if field not in c.valid_inspiration_fields:
                raise RuntimeError(f"Invalid field \"{field}\" in inspiration {inspiration['Name']}.")
        # url fields
        for field in c.url_inspiration_fields:
            if field in inspiration:
                content = inspiration[field]
                if any(not (x.startswith('http://') or x.startswith('https://')) for x in content):
                    raise RuntimeError(f"Invalid URL in field \"{field}\" in inspiration {inspiration['Name']}.")

    # convert to dictionary
    inspirations = {x['Name']: x for x in inspirations}

    return inspirations


def write_inspirations(inspirations):
    """
    Given an internal dictionary of inspirations, write it into the inspirations file
    :param inspirations:
    :return:
    """
    # convert dictionary to list
    inspirations = list(inspirations.values())

    # comment
    content = f'{c.generic_comment_string}\n'

    # updated number of inspirations
    content += f'# Inspirations [{len(inspirations)}]\n\n'

    # sort by name
    inspirations.sort(key=lambda x: str.casefold(x['Name']))

    # iterate over them
    for inspiration in inspirations:
        keys = list(inspiration.keys())
        # inspiration name
        content += f"## {inspiration['Name']} [{len(inspiration['Inspired entries'])}]\n\n"
        keys.remove('Name')

        # all the remaining in alphabetical order, but "inspired entries" first
        keys.remove('Inspired entries')
        keys.sort()
        keys = ['Inspired entries'] + keys
        for field in keys:
            value = inspiration[field]
            # lists get special treatment
            if isinstance(value, list):
                value.sort(key=str.casefold)  # sorted alphabetically
                value = [x if not ',' in x else f'"{x}"' for x in value]  # surround those with a comma with quotation marks
                value = ', '.join(value)
            content += f'- {field}: {value}\n'
        content += '\n'

    # write
    utils.write_text(c.inspirations_file, content)


def read_entries():
    """
    Parses all entries and assembles interesting infos about them.
    """

    # setup parser and transformer
    grammar_file = c.code_path / 'grammar_entries.lark'
    grammar = utils.read_text(grammar_file)
    parse = osg_parse.create(grammar, osg_parse.EntryTransformer)

    # a database of all important infos about the entries
    entries = []

    # iterate over all entries
    exception_happened = None
    for file, _, content in entry_iterator():

        if not content.endswith('\n'):
            content += '\n'

        # parse and transform entry content
        try:
            entry = parse(content)
            entry = [('File', file),] + entry # add file information to the beginning
            entry = check_and_process_entry(entry)
        except Exception as e:
            print(f'{file} - {e}')
            exception_happened = e # just store last one
            continue

        # add to list
        entries.append(entry)
    if exception_happened:
        print('error(s) while reading entries')
        raise exception_happened

    return entries


def read_entry(file):
    """
    Reads a single entry
    :param file: the entry file (without path)
    :return: the entry
    """

    # setup parser and transformer
    grammar_file = c.code_path / 'grammar_entries.lark'
    grammar = utils.read_text(grammar_file)
    parse = osg_parse.create(grammar, osg_parse.EntryTransformer)

    # read entry file
    content = utils.read_text(c.entries_path / file)
    if not content.endswith('\n'):
        content += '\n'

    # parse and transform entry content
    try:
        entry = parse(content)
        entry = [('File', file),] + entry # add file information to the beginning
        entry = check_and_process_entry(entry)
    except Exception as e:
        print(f'{file} - {e}')
        raise RuntimeError(e)

    return entry


def check_and_process_entry(entry):
    """

    :param entry:
    :return:
    """
    message = ''

    # check that all fields are valid fields and are existing in that order
    index = 0
    for e in entry:
        field = e[0]
        while index < len(c.valid_fields) and field != c.valid_fields[index]:
            index += 1
        if index == len(c.valid_fields):  # must be valid fields and must be in the right order
            message += f'Field "{field}" either misspelled or in wrong order\n'

    # order is fine we can convert now to dictionary
    d = {}
    for field, value in entry:
        if field in d:
            message += f'Field "{field}" appears twice\n'
        d[field] = value
    entry = d

    # check for essential fields
    for field in c.essential_fields:
        if field not in entry:
            message += f'Essential property "{field}" missing\n'

    # now the same treatment for building
    building = entry['Building']
    d = {}
    for field, value in building:
        if field in d:
            message += f'Field "{field}" appears twice\n'
        d[field] = value
    building = d

    # check valid fields in building TODO should also check order
    for field in building.keys():
        if field not in c.valid_building_fields:
            message += f'Building field "{field}" invalid\n'
    entry['Building'] = building

    # check canonical file name
    file = entry['File']
    canonical_file_name = canonical_name(entry['Title']) + '.md'
    # we also allow -X with X =2..9 as possible extension (because of duplicate canonical file names)
    if canonical_file_name != file.name and canonical_file_name != file.name[:-5] + '.md':
        message += f'File name should be {canonical_file_name}\n'

    # check that fields without comments have no comments (i.e. are no Values)
    for field in c.fields_without_comments:
        if field in entry:
            content = entry[field]
            if any(isinstance(item, osg_parse.Value) for item in content):
                message += f'field without comments {field} has comment\n'

    # state must contain either beta or mature but not both
    state = entry['State']
    for t in state:
        if t != 'beta' and t != 'mature' and not t.startswith('inactive since '):
            message += f'Unknown state "{t}"'
    if 'beta' in state == 'mature' in state:
        message += 'State must be one of <"beta", "mature">'

    # check urls
    for field in c.url_fields:
        values = entry.get(field, [])
        for value in values:
            if value.startswith('<') and value.endswith('>'):
                value = value[1:-1]
            if not any(value.startswith(x) for x in c.valid_url_prefixes):
                message += f'URL "{value}" in field "{field}" does not start with a valid prefix'

    # github/gitlab repositories should end on .git and should start with https
    for repo in entry.get('Code repository', []):
        if any(repo.startswith(x) for x in ('@', '?')):
            continue
        repo = repo.split(' ')[0].strip()
        if any((x in repo for x in ('github', 'gitlab', 'git.tuxfamily', 'git.savannah'))):
                if not repo.startswith('https://'):
                    message += f'Repo "{repo}" should start with https://'
                if not repo.endswith('.git'):
                    message += f'Repo "{repo}" should end on .git.'

    # check that all platform tags are valid tags and are existing in that order
    if 'Platform' in entry:
        index = 0
        for platform in entry['Platform']:
            while index < len(c.valid_platforms) and platform != c.valid_platforms[index]:
                index += 1
            if index == len(c.valid_platforms):  # must be valid platforms and must be in that order
                message += f'Platform tag "{platform}" either misspelled or in wrong order'

    # there must be at least one keyword
    if not entry['Keyword']:
        message += 'Need at least one keyword'

    # check for existence of at least one recommended keywords
    keywords = entry['Keyword']
    if not any(keyword in keywords for keyword in c.recommended_keywords):
        message += 'Entry contains no recommended keywords'

    # languages should be known
    languages = entry['Code language']
    for language in languages:
        if language not in c.known_languages:
            message += f'Language "{language}" is not a known code language. Misspelled or new?'

    # licenses should be known
    licenses = entry['Code license']
    for license in licenses:
        if license not in c.known_licenses:
            message += f'License "{license}" is not a known license. Misspelled or new?'

    if message:
        raise RuntimeError(message)

    return entry


def is_inactive(entry):
    state = entry['State']
    phrase = 'inactive since '
    return any(x.startswith(phrase) for x in state)


def extract_inactive_year(entry):
    state = entry['State']
    phrase = 'inactive since '
    inactive_year = [x[len(phrase):] for x in state if x.startswith(phrase)]
    assert len(inactive_year) <= 1
    if inactive_year:
        return int(inactive_year[0])
    else:
        return None


def write_entries(entries):
    """

    :return:
    """

    # iterate over all entries
    for entry in entries:
        write_entry(entry)


def write_entry(entry, overwrite=True):
    """

    :param entry:
    :return:
    """
    # TODO check entry

    # get path
    entry_path = c.entries_path / entry['File']
    if not overwrite and os.path.isfile(entry_path):
        raise RuntimeError(f'File {entry_path} already existing and do not want to overwrite it.')

    # create output content
    content = create_entry_content(entry)

    # write entry
    utils.write_text(entry_path, content)


def render_value(value):
    """

    :param value:
    :return:
    """
    if isinstance(value, osg_parse.Value):
        comment = value.comment
    else:
        comment = None
    if any(x in value for x in (',', ' (')):
        value = f'"{value}"'
    if comment:
        return f'{value} ({comment})'
    else:
        return value


def create_entry_content(entry):
    """
    Creates the entry content from an internal representation as dictionary with fields to a text file representation
    that can be stored in the md files. It should be compatible with the grammar and reading a file and re-creating the
    content should not change the content. Importantly, the comments of the values have to be added here.
    :param entry:
    :return:
    """

    # title
    content = f"# {entry['Title']}\n\n"

    # we automatically sort some fields
    sort_fun = lambda x: str.casefold(x)
    for field in ('Media', 'Inspiration', 'Code Language', 'Developer', 'Build system'):
        if field in entry:
            values = entry[field]
            entry[field] = sorted(values, key=sort_fun)
    # we also sort keywords, but first the recommended ones and then other ones
    keywords = entry['Keyword']
    a = [x for x in keywords if x in c.recommended_keywords]
    b = [x for x in keywords if x not in c.recommended_keywords]
    entry['Keyword'] = sorted(a, key=sort_fun) + sorted(b, key=sort_fun)

    # now all properties are in the recommended order
    for field in c.valid_properties:
        if field in entry:
            e = entry[field]
            e = [render_value(x) for x in e]
            e = list(dict.fromkeys(e))  # this removes duplicates while keeping the sorting order
            content += f"- {field}: {', '.join(e)}\n"
    content += '\n'

    # if there is a note, insert it
    if 'Note' in entry:
        content += entry['Note'].strip() + '\n\n'

    # building header
    content += '## Building\n'

    # building properties if present
    has_properties = False
    for field in c.valid_building_properties:
        if field in entry['Building']:
            if not has_properties:
                has_properties = True
                content += '\n'
            e = entry['Building'][field]
            e = [render_value(x) for x in e]
            e = list(dict.fromkeys(e))  # this removes duplicates while keeping the sorting order
            content += f"- {field}: {', '.join(e)}\n"

    # if there is a note, insert it
    if 'Note' in entry['Building']:
        content += '\n'
        content += entry['Building']['Note']

    return content


def is_url(str):
    """
    Could be too generous. See https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not for other possibilities.
    :param str:
    :return:
    """
    if any(str.startswith(x) for x in c.valid_url_prefixes) and not ' ' in str:
        return True
    return False


def all_urls(entries):
    """
    Gets all urls of all entries in a dictionary (key=url value=list of entries (file name) with this url
    :param entries: 
    :return: 
    """
    # TODO there are other fields than c.url_fields and also in comments, maybe just regex on the whole content
    # TODO this might be part of the external link check or it might not, check for duplicate code
    urls = {}
    # iterate over entries
    for entry in entries:
        file = entry['File']
        for field in c.url_fields:
            for value in entry.get(field, []):
                for subvalue in value.split(' '):
                    subvalue = subvalue.strip()
                    if is_url(subvalue):
                        urls[subvalue] = urls.get(subvalue, []) + [file]
    return urls


def git_repo(repo):
    """
    Tests if a repo URL is a git repo, then returns the repo url.
    """

    # everything that starts with 'git://'
    if repo.startswith('git://'):
        return repo

    # generic (https://*.git) or (http://*.git) ending on git
    if (repo.startswith('https://') or repo.startswith('http://')) and repo.endswith('.git'):
        return repo

    # for all others we just check if they start with the typical urls of git services
    services = ['https://git.tuxfamily.org/', 'http://git.pond.sub.org/', 'https://gitorious.org/',
                'https://git.code.sf.net/p/']
    if any(repo.startswith(service) for service in services):
        return repo

    # the rest is not recognized as a git url
    return None


def svn_repo(repo):
    """
    Tests if a repo URL is a svn repo, then returns the repo url.
    """

    # we can just go for known providers of svn
    services = ('svn://', 'https://svn.code.sf.net/p/', 'http://svn.savannah.gnu.org/svn/', 'https://svn.icculus.org/', 'http://svn.icculus.org/', 'http://svn.uktrainsim.com/svn/', 'https://rpg.hamsterrepublic.com/source/wip')
    if any(repo.startswith(service) for service in services):
        return repo

    # not svn
    return None


def hg_repo(repo):
    """
    Tests if a repo URL is a hg repo, then returns the repo url.
    """
    if repo.startswith('https://bitbucket.org/') and not repo.endswith('.git'):
        return repo

    if repo.startswith('http://hg.'):
        return repo

    # not hg
    return None


def read_screenshots_overview():
    """

    :return:
    """
    # read screenshots readme and parse
    overview = {}
    text = utils.read_text(c.screenshots_file)
    for entry in text.split('\n# ')[1:]:  # skip first paragraph
        lines = entry.split('\n')  # split into lines
        name = lines[0]
        if name not in overview:
            overview[name] = {}
        lines = [line for line in lines[1:] if line]  # include only non-empty lines
        # for every screenshot
        for line in lines:
            values = line.split(' ')  # split into values
            values = [value for value in values if value]
            id = int(values[0])  # id (must be there)
            width = int(values[1])  # width can be 0, will be updated
            height = int(values[2])  # height can be 0, will be updated
            if len(values) > 3:  # optional an url
                url = values[3]
            else:
                url = None
            overview[name][id] = [width, height, url]
    return overview


def write_screenshots_overview(overview):
    """

    :param overview:
    :return:
    """
    # get preamble
    text = utils.read_text(c.screenshots_file)
    text = text.split('\n# ')[0] + '\n'

    # write out each entry sorted by name
    for name in sorted(overview.keys()):
        a = overview[name]
        t = f'# {name}\n\n'
        # write out each line sorted by id
        for id in sorted(a.keys()):
            ai = a[id]
            if ai[-1] is None:
                ai = ai[:-1]
            t += ' '.join([f'{id:02d}'] + [str(x) for x in ai]) + '\n'
        t += '\n'
        text += t

    utils.write_text(c.screenshots_file, text)