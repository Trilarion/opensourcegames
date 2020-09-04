"""
Specific functions working on the games.
"""

import re
from difflib import SequenceMatcher
from utils import utils
import lark

from utils.constants import *


class ListingTransformer(lark.Transformer):
    """
    Transforms content parsed by grammar_listing.lark further.
    Used for the developer and inspirations list.
    """

    def unquoted_value(self, x):
        return x[0].value

    def quoted_value(self, x):
        return x[0].value[1:-1]  # remove quotation marks

    def property(self, x):
        """
        The key of a property will be converted to lower case and the value part is the second part
        :param x:
        :return:
        """
        return x[0].lower(), x[1:]

    def name(self, x):
        """
        The name part is treated as a property with key "name"
        :param x:
        :return:
        """
        return 'name', x[0].value

    def entry(self, x):
        """
        All (key, value) tuples are inserted into a dictionary.
        :param x:
        :return:
        """
        d = {}
        for key, value in x:
            if key in d:
                raise RuntimeError('Key in entry appears twice')
            d[key] = value
        return d

    def start(self, x):
        return x


# transformer
class EntryTransformer(lark.Transformer):

    def unquoted_value(self, x):
        return x[0].value

    def quoted_value(self, x):
        return x[0].value[1:-1]  # remove quotation marks

    def property(self, x):
        """
        The key of a property will be converted to lower case and the value part is the second part
        :param x:
        :return:
        """
        return x[0].lower(), x[1:]

    def title(self, x):
        return 'title', x[0].value

    def description(self, x):
        return 'description', x[0].value

    def note(self, x):
        """
        Optional
        :param x:
        :return:
        """
        if not x:
            raise lark.Discard
        return 'note', ''.join((x.value for x in x))

    def building(self, x):
        d = {}
        for key, value in x:
            if key in d:
                raise RuntimeError('Key in entry appears twice')
            d[key] = value
        return 'building', d

    def start(self, x):
        d = {}
        for key, value in x:
            if key in d:
                raise RuntimeError('Key in entry appears twice')
            d[key] = value
        return d


regex_sanitize_name = re.compile(r"[^A-Za-z 0-9-+]+")
regex_sanitize_name_space_eater = re.compile(r" +")


def name_similarity(a, b):
    return SequenceMatcher(None, str.casefold(a), str.casefold(b)).ratio()


def split_infos(infos):
    """
    Split into games, tools, frameworks, libraries
    """
    games = [x for x in infos if not any([y in x['keywords'] for y in ('tool', 'framework', 'library')])]
    tools = [x for x in infos if 'tool' in x['keywords']]
    frameworks = [x for x in infos if 'framework' in x['keywords']]
    libraries = [x for x in infos if 'library' in x['keywords']]
    return games, tools, frameworks, libraries


def entry_iterator():
    """

    """

    # get all entries (ignore everything starting with underscore)
    entries = os.listdir(entries_path)

    # iterate over all entries
    for entry in entries:
        entry_path = os.path.join(entries_path, entry)

        # ignore directories ("tocs" for example)
        if os.path.isdir(entry_path):
            continue

        # read entry
        content = utils.read_text(entry_path)

        # yield
        yield entry, entry_path, content


def canonical_entry_name(name):
    """
    Derives a canonical game name from an actual game name (suitable for file names, ...)
    """
    name = name.casefold()
    name = name.replace('ö', 'o').replace('ä', 'a').replace('ü', 'u')
    name = regex_sanitize_name.sub('', name)
    name = regex_sanitize_name_space_eater.sub('_', name)
    name = name.replace('_-_', '-')
    name = name.replace('--', '-').replace('--', '-')

    return name


def parse_entry(content):
    """
    Returns a dictionary of the features of the content.

    Raises errors when a major error in the structure is expected, prints a warning for minor errors.
    """

    info = {}

    # read name
    regex = re.compile(r"^# (.*)")  # start of content, starting with "# " and then everything until the end of line
    matches = regex.findall(content)
    if len(matches) != 1 or not matches[0]:  # name must be there
        raise RuntimeError('Name not found in entry "{}" : {}'.format(content, matches))
    info['name'] = matches[0]

    # read description
    regex = re.compile(r"^.*\n\n_(.*)_\n")  # third line from top, everything between underscores
    matches = regex.findall(content)
    if len(matches) != 1 or not matches[0]:  # description must be there
        raise RuntimeError('Description not found in entry "{}"'.format(content))
    info['description'] = matches[0]

    # first read all field names
    regex = re.compile(r"^- (.*?): ",
                       re.MULTILINE)  # start of each line having "- ", then everything until a colon, then ": "
    fields = regex.findall(content)

    # check that essential fields are there
    for field in essential_fields:
        if field not in fields:  # essential fields must be there
            raise RuntimeError('Essential field "{}" missing in entry "{}"'.format(field, info['name']))

    # check that all fields are valid fields and are existing in that order
    index = 0
    for field in fields:
        while index < len(valid_fields) and field != valid_fields[index]:
            index += 1
        if index == len(valid_fields):  # must be valid fields and must be in the right order
            raise RuntimeError(
                'Field "{}" in entry "{}" either misspelled or in wrong order'.format(field, info['name']))

    # iterate over found fields
    for field in fields:
        regex = re.compile(r"- {}: (.*)".format(field))
        matches = regex.findall(content)
        if len(matches) != 1:  # every field must be present only once
            raise RuntimeError('Field "{}" in entry "{}" exist multiple times.'.format(field, info['name']))
        v = matches[0]

        # first store as is
        info[field.lower() + '-raw'] = v

        # remove parenthesis with content
        v = re.sub(r'\([^)]*\)', '', v)

        # split on ', '
        v = v.split(', ')

        # strip
        v = [x.strip() for x in v]

        # remove all being false (empty) that were for example just comments
        v = [x for x in v if x]

        # if entry is of structure <..> remove <>
        v = [x[1:-1] if x[0] == '<' and x[-1] == '>' else x for x in v]

        # empty fields will not be stored
        if not v:
            continue

        # store in info
        info[field.lower()] = v

    # check again that essential fields made it through
    for field in ('home', 'state', 'keywords', 'code language', 'code license'):
        if field not in info:  # essential fields must still be inside
            raise RuntimeError('Essential field "{}" empty in entry "{}"'.format(field, info['name']))

    # now checks on the content of fields

    # name and description should not have spaces at the begin or end
    for field in ('name', 'description'):
        v = info[field]
        if len(v) != len(v.strip()):  # warning about that
            print('Warning: No leading or trailing spaces in field {} in entry "{}"'.format(field, info['name']))

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
                if not any(
                        [url.startswith(x) for x in ['http://', 'https://', 'git://', 'svn://', 'ftp://', 'bzr://']]):
                    raise RuntimeError(
                        'URL "{}" in entry "{}" does not start with http/https/git/svn/ftp/bzr'.format(url,
                                                                                                       info['name']))
                if ' ' in url:
                    raise RuntimeError('URL "{}" in entry "{}" contains a space'.format(url, info['name']))

    # github/gitlab repositories should end on .git and should start with https
    if 'code repository' in info:
        for repo in info['code repository']:
            if any((x in repo for x in ('github', 'gitlab', 'git.tuxfamily', 'git.savannah'))):
                if not repo.startswith('https://'):
                    print('Warning: Repo {} in entry "{}" should start with https://'.format(repo, info['name']))
                if not repo.endswith('.git'):
                    print('Warning: Repo {} in entry "{}" should end on .git.'.format(repo, info['name']))

    # check that all platform tags are valid tags and are existing in that order
    if 'platform' in info:
        index = 0
        for platform in info['platform']:
            while index < len(valid_platforms) and platform != valid_platforms[index]:
                index += 1
            if index == len(valid_platforms):  # must be valid platforms and must be in that order
                raise RuntimeError(
                    'Platform tag "{}" in entry "{}" either misspelled or in wrong order'.format(platform,
                                                                                                 info['name']))

    # there must be at least one keyword
    if 'keywords' not in info:
        raise RuntimeError('Need at least one keyword in entry "{}"'.format(info['name']))

    # check for existence of at least one recommended keywords
    fail = True
    for recommended_keyword in recommended_keywords:
        if recommended_keyword in info['keywords']:
            fail = False
            break
    if fail:  # must be at least one recommended keyword
        raise RuntimeError('Entry "{}" contains no recommended keyword'.format(info['name']))

    # languages should be known
    languages = info['code language']
    for language in languages:
        if language not in known_languages:
            print('Warning: Language {} in entry "{}" is not a known language. Misspelled or new?'.format(language,
                                                                                                          info['name']))

    # licenses should be known
    licenses = info['code license']
    for license in licenses:
        if license not in known_licenses:
            print('Warning: License {} in entry "{}" is not a known license. Misspelled or new?'.format(license,
                                                                                                        info['name']))

    return info


def assemble_infos():
    """
    Parses all entries and assembles interesting infos about them.
    """

    print('assemble game infos')

    # a database of all important infos about the entries
    infos = []

    # iterate over all entries
    for entry, _, content in entry_iterator():

        # parse entry
        info = parse_entry(content)

        # add file information
        info['file'] = entry

        # check canonical file name
        canonical_file_name = canonical_entry_name(info['name']) + '.md'
        # we also allow -X with X =2..9 as possible extension (because of duplicate canonical file names)
        if canonical_file_name != entry and canonical_file_name != entry[:-5] + '.md':
            print('Warning: file {} should be {}'.format(entry, canonical_file_name))
            source_file = os.path.join(entries_path, entry)
            target_file = os.path.join(entries_path, canonical_file_name)
            if not os.path.isfile(target_file):
                pass
                # os.rename(source_file, target_file)

        # add to list
        infos.append(info)

    return infos


def extract_links():
    """
    Parses all entries and extracts http(s) links from them
    """

    # regex for finding urls (can be in <> or in ]() or after a whitespace
    regex = re.compile(r"[\s\n]<(http.+?)>|]\((http.+?)\)|[\s\n](http[^\s\n,]+?)[\s\n,]")

    # iterate over all entries
    urls = set()
    for _, _, content in entry_iterator():

        # apply regex
        matches = regex.findall(content)

        # for each match
        for match in matches:

            # for each possible clause
            for url in match:

                # if there was something (and not a sourceforge git url)
                if url:
                    urls.add(url)
    urls = sorted(list(urls), key=str.casefold)
    return urls


def read_and_parse(content_file: str, grammar_file: str, transformer: lark.Transformer):
    """
    Reads a content file and a grammar file and parses the content with the grammar following by
    transforming the parsed output and returning the transformed result.
    :param content_file:
    :param grammar_file:
    :param transformer:
    :return:
    """
    content = utils.read_text(content_file)
    grammar = utils.read_text(grammar_file)
    parser = lark.Lark(grammar, debug=False, parser='lalr')
    tree = parser.parse(content)
    return transformer.transform(tree)


def read_developer_info():
    """

    :return:
    """
    grammar_file = os.path.join(code_path, 'grammar_listing.lark')
    transformer = ListingTransformer()
    developers = read_and_parse(developer_file, grammar_file, transformer)
    # now transform a bit more
    for index, dev in enumerate(developers):
        # check for valid keys
        for field in dev.keys():
            if field not in valid_developer_fields:
                raise RuntimeError('Unknown developer field "{}" for developer: {}.'.format(field, dev['name']))
        # strip from name or organization (just in case)
        for field in ('name', ):
            if field in dev:
                dev[field] = dev[field].strip()
        # split games, contact (are lists)
        for field in ('games', 'contact'):
            if field in dev:
                content = dev[field]
                content = [x.strip() for x in content]
                dev[field] = content
    # check for duplicate names entries
    names = [dev['name'] for dev in developers]
    duplicate_names = (name for name in names if names.count(name) > 1)
    duplicate_names = set(duplicate_names)  # to avoid duplicates in duplicate_names
    if duplicate_names:
        print('Warning: duplicate developer names: {}'.format(', '.join(duplicate_names)))
    return developers


def write_developer_info(developers):
    """

    :return:
    """
    # comment
    content = '{}\n'.format(generic_comment_string)

    # number of developer
    content += '# Developer [{}]\n\n'.format(len(developers))

    # sort by name
    developers.sort(key=lambda x: str.casefold(x['name']))

    # iterate over them
    for dev in developers:
        keys = list(dev.keys())
        # developer name
        content += '## {} [{}]\n\n'.format(dev['name'], len(dev['games']))
        keys.remove('name')

        # all the remaining in alphabetical order, but 'games' first
        keys.remove('games')
        keys.sort()
        keys = ['games'] + keys
        for field in keys:
            value = dev[field]
            field = field.capitalize()
            # lists get special treatment
            if isinstance(value, list):
                value.sort(key=str.casefold)
                value = [x if not ',' in x else '"{}"'.format(x) for x in value]  # surround those with a comma with quotation marks
                value = ', '.join(value)
            content += '- {}: {}\n'.format(field, value)
        content += '\n'

    # write
    utils.write_text(developer_file, content)


def read_inspirations_info():
    """
    Reads the info list about the games originals/inspirations from inspirations.md using the Lark parser grammar
    in grammar_listing.lark
    :return:
    """
    # read inspirations

    grammar_file = os.path.join(code_path, 'grammar_listing.lark')
    transformer = ListingTransformer()
    inspirations = read_and_parse(inspirations_file, grammar_file, transformer)

    # now inspirations is a list of dictionaries for every entry with keys (valid_developers_fields)

    # now transform a bit more
    for index, inspiration in enumerate(inspirations):
        # check that keys are valid keys
        for field in inspiration.keys():
            if field not in valid_inspiration_fields:
                raise RuntimeError('Unknown field "{}" for inspiration: {}.'.format(field, inspiration['name']))
        # split lists
        for field in ('inspired entries',):
            if field in inspiration:
                content = inspiration[field]
                content = [x.strip() for x in content]
                inspiration[field] = content

    # check for duplicate names entries
    names = [inspiration['name'] for inspiration in inspirations]
    duplicate_names = (name for name in names if names.count(name) > 1)
    duplicate_names = set(duplicate_names)  # to avoid duplicates in duplicate_names
    if duplicate_names:
        print('Warning: duplicate inspiration names: {}'.format(', '.join(duplicate_names)))

    return inspirations


def write_inspirations_info(inspirations):
    """
    Given an internal list of inspirations, write it into the inspirations file
    :param inspirations:
    :return:
    """
    # comment
    content = '{}\n'.format(generic_comment_string)

    # number of developer
    content += '# Inspirations [{}]\n\n'.format(len(inspirations))

    # sort by name
    inspirations.sort(key=lambda x: str.casefold(x['name']))

    # iterate over them
    for inspiration in inspirations:
        keys = list(inspiration.keys())
        # inspiration name
        content += '## {} [{}]\n\n'.format(inspiration['name'], len(inspiration['inspired entries']))
        keys.remove('name')

        # all the remaining in alphabetical order, but "inspired entries" first
        keys.remove('inspired entries')
        keys.sort()
        keys = ['inspired entries'] + keys
        for field in keys:
            value = inspiration[field]
            field = field.capitalize()
            # lists get special treatment
            if isinstance(value, list):
                value.sort(key=str.casefold)
                value = [x if not ',' in x else '"{}"'.format(x) for x in value]  # surround those with a comma with quotation marks
                value = ', '.join(value)
            content += '- {}: {}\n'.format(field, value)
        content += '\n'

    # write
    utils.write_text(inspirations_file, content)


def read_entries():
    """
    Parses all entries and assembles interesting infos about them.
    """

    # setup parser
    grammar_file = os.path.join(code_path, 'grammar_entries.lark')
    grammar = utils.read_text(grammar_file)
    parser = lark.Lark(grammar, debug=False, parser='lalr')

    # setup transformer
    transformer = EntryTransformer()

    # a database of all important infos about the entries
    entries = []

    # iterate over all entries
    for file, _, content in entry_iterator():

        if not content.endswith('\n'):
            content += '\n'

        # parse and transform entry content
        try:
            tree = parser.parse(content)

            entry = transformer.transform(tree)
            # add file information
            entry['file'] = file

            check_entry(entry)
        except Exception as e:
            print('{} - {}'.format(file, e))
            continue

        # add to list
        entries.append(entry)

    return entries


def check_entry(entry):
    """

    :param entry:
    :return:
    """
    message = ''

    file = entry['file']

    # check canonical file name
    canonical_file_name = canonical_entry_name(entry['title']) + '.md'
    # we also allow -X with X =2..9 as possible extension (because of duplicate canonical file names)
    if canonical_file_name != file and canonical_file_name != file[:-5] + '.md':
        message += 'file name should be {}\n'.format(canonical_file_name)

    # title should not be also in description
    if entry['title'] in entry['description']:
        message += 'title included in description, should be removed'

    if message:
        raise RuntimeError(message)


def write_entries(entries):
    """

    :return:
    """

    # iterate over all entries
    for entry in entries:
        write_entry(entry)

def write_entry(entry):
    """

    :param entry:
    :return:
    """
    # TODO check entry

    # get path
    entry_path = os.path.join(entries_path, entry['file'])

    # create output content
    content = create_entry_content(entry)

    # write entry
    utils.write_text(entry_path, content)


def create_entry_content(entry):
    """

    :param entry:
    :return:
    """

    # title
    content = '# {}\n\n'.format(entry['title'])

    # now properties in the recommended order
    for field in valid_fields:
        field_name = field.lower()
        if field_name in entry:
            c = entry[field_name]
            c = ['"{}"'.format(x) if ',' in x else x for x in c]
            content += '- {}: {}\n'.format(field, ', '.join(c))
    content += '\n'

    # if there is a note, insert it
    if 'note' in entry:
        content += entry['note']

    # building header
    content += '## Building\n'

    # building properties if present
    has_properties = False
    for field in valid_building_fields:
        field_name = field.lower()
        if field_name in entry['building']:
            if not has_properties:
                has_properties = True
                content += '\n'
            content += '- {}: {}\n'.format(field, ', '.join(entry['building'][field_name]))

    # if there is a note, insert it
    if 'note' in entry['building']:
        content += '\n'
        content += entry['building']['note']

    return content

def compare_entries_developers(entries, developers):
    """
    Cross checks the game entries lists and the developers lists.
    :param entries: List of game entries
    :param developers: List of developers
    """

    # from the entries create a dictionary with developer names
    devs1 = {}
    for entry in entries:
        name = entry['name']
        for dev in entry.get('developer', []):
            if dev in devs1:
                devs1[dev].append(name)
            else:
                devs1[dev] = [name]
    devs1_names = set(devs1.keys())

    # from the developers create a dictionary with developer names
    devs2 = dict(zip((dev['name'] for dev in developers), (dev['games'] for dev in developers)))
    devs2_names = set(devs2.keys())

    # devs only in entries
    for dev in devs1_names - devs2_names:
        print('Warning: dev "{}" only in entries ({}), not in developers'.format(dev, ','.join(devs1[dev])))
    # devs only in developers
    for dev in devs2_names - devs1_names:
        print('Warning: dev "{}" only in developers ({}), not in entries'.format(dev, ','.join(devs2[dev])))
    # for those in both, check that the games lists are equal
    for dev in devs1_names.intersection(devs2_names):
        games1 = set(devs1[dev])
        games2 = set(devs2[dev])
        delta = games1 - games2
        if delta:
            print('Warning: dev "{}" has games in entries ({}) that are not present in developers'.format(dev,
                                                                                                          ', '.join(
                                                                                                              delta)))
        delta = games2 - games1
        if delta:
            print('Warning: dev "{}" has games in developers ({}) that are not present in entries'.format(dev,
                                                                                                          ', '.join(
                                                                                                              delta)))
