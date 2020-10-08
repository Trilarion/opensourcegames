"""
Generates the static website

Uses Jinja2 (see https://jinja.palletsprojects.com/en/2.11.x/)

Listing:

- title: top level title
- items: list of items
  - anchor-id, name: title of each item
  - fields: list of fields in item
    - type: one of 'linebreak', 'text', 'enumeration'
    if type == 'text': // macro render_text
      content: the text to display
      class: the class of the text modifications (optional)
    if type == 'enumeration': // macro render_enumeration

"""

# TODO index.html tiles, content
# TODO index.html image (maybe downloaded and assembled from osgameclones)
# TODO index.html only count games
# TODO Font awesome 4 or others (icons for OS, for Github, Gitlab and maybe others like external link)
# TODO contribute.html tiles? content?
# TODO games: links to licenses (wikipedia)
# TODO indexes: make categories bold that have a certain amount of entries!
# TODO everywhere: style URLs (Github, Wikipedia, Internet archive, SourceForge, ...)
# TODO developers: links to games and more information, styles
# TODO inspirations: add link to games and more information, styles
# TODO statistics page: better and more statistics with links where possible
# TODO meaningful information (links, license, last updated with lower precision)
# TODO singular, plural everywhere (game, entries, items)
# TODO rename fields (Home to Homepage, Inspirations to Inspiration)
# TODO developers: contact expand to links to Github, Sourceforge
# TODO games: keywords as labels (some as links)
# TODO games: links languages
# TODO games: platforms as labels and with links
# TODO games: Building, Build system missing
# TODO games: links to md files
# TODO games: contribute/edit, link to md file unten in klein
# TODO games: use top level for genre and status
# TODO games/developers/inspirations: split template
# TODO split games in libraries/tools/frameworks and real games, add menu
# TODO statistics with nice graphics (pie charts in SVG) with matplotlib, seaborn, plotly?
# TODO statistics, get it from common statistics generator
# TODO optimize jinja for line breaks and indention and minimal amount of spaces
# TODO replace or remove @notices in entries (maybe different entries format)
# TODO icons: for the main categories (devs, games, statistics, home, ...)
# TODO SEO optimizations, google search ...

import os
import shutil
import math
import datetime
from functools import partial
from utils import osg, constants as c, utils
from jinja2 import Environment, FileSystemLoader
import html5lib

alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
extra = '0'
extended_alphabet = alphabet + extra

games_path = ['games']
frameworks_path = ['frameworks']
inspirations_path = ['inspirations']
developers_path = ['developers']

games_by_language_path = games_path + ['languages.html']

platform_color = {
    'Windows': 'is-danger',
    'Linux': 'is-link',
    'macOS': 'is-success',
    'Android': 'is-black',
    'iOS': 'is-primary',
    'Web': 'is-warning',
}

platform_icon_map = {
    'Windows': 'windows',
    'Linux': 'linux',
    'iOS': 'ios',
    'Web': 'sphere'
}

plurals = {k: k+'s' for k in ('Assets license', 'Contact', 'Code language', 'Code license', 'Developer', 'Download', 'Inspiration', 'Game', 'Keyword', 'Home', 'Organization', 'Platform')}
for k in ('Media', 'Play', 'State'):
    plurals[k] = k
for k in ('Code repository', 'Code dependency'):
    plurals[k] = k[:-1] + 'ies'

code_language_references = {l: games_by_language_path[:-1] + ['{}#{}'.format(games_by_language_path[-1], osg.canonical_name(l))] for l in c.known_languages}

def get_plural_or_singular(name, amount):
    if not name in plurals.keys():
        raise RuntimeError('"{}" not a known singular!'.format(name))
    if amount == 1:
        return name
    return plurals[name]


html5parser = html5lib.HTMLParser(strict=True)


def raise_helper(msg):
    raise Exception(msg)


def write(text, file):
    """

    :param text:
    :param file:
    """
    # validate text
    if isinstance(file, str):
        file = [file]
    try:
        html5parser.parse(text)
    except Exception as e:
        utils.write_text(os.path.join(c.web_path, 'invalid.html'), text)  # for further checking with https://validator.w3.org/
        raise RuntimeError(e)
    # output file
    file = os.path.join(c.web_path, *file)
    # create output directory if necessary
    containing_dir = os.path.dirname(file)
    if not os.path.isdir(containing_dir):
        os.mkdir(containing_dir)
    # write text
    utils.write_text(file, text)


def sort_into_categories(list, categories, fit, unknown_category_name=None):
    """

    :param list:
    :param categories:
    :param fit:
    :param unknown_category_name:
    :return:
    """
    categorized_sublists = {}
    for category in categories:
        sublist = [item for item in list if fit(item, category)]
        categorized_sublists[category] = sublist
    if unknown_category_name:
        # now those that do not fit
        sublist = [item for item in list if not any(fit(item, category) for category in categories)]
        categorized_sublists[unknown_category_name] = sublist
    return categorized_sublists


def divide_in_columns(categorized_lists, transform):
    """

    :param categorized_lists:
    :param key:
    :return:
    """
    number_entries = {category: len(categorized_lists[category]) for category in categorized_lists.keys()}
    entries = {}
    for category in categorized_lists.keys():
        e = categorized_lists[category]
        # transform entry
        e = [transform(e) for e in e]
        # divide in three equal lists
        n = len(e)
        n1 = math.ceil(n/3)
        n2 = math.ceil(2*n/3)
        e = [e[:n1], e[n1:n2], e[n2:]]
        entries[category] = e
    return {'number_entries': number_entries, 'entries': entries}


def url_to(current, target, info=None):
    """

    :param current: Current path
    :param target:
    :return:
    """
    # if it's an absolute url, just return
    if isinstance(target, str) and any(target.startswith(x) for x in ('http://', 'https://')):
        return target
    if isinstance(target, str):
        target = [target]
    # split by slash
    #if current:
    #    current = current.split('/')
    #target = target.split('/')
    # reduce by common elements
    while len(current) > 0 and len(target) > 1 and current[0] == target[0]:
        current = current[1:]
        target = target[1:]
    # add .. as often as length of current still left
    target = ['..'] * len(current) + target
    # join by slash again
    url = '/'.join(target)
    return url


def preprocess(list, key, url):
    """

    :param list:
    :param key:
    :return:
    """
    _ = set()
    for item in list:
        # add unique anchor ref
        anchor = osg.canonical_name(item[key])
        while anchor in _:
            anchor += 'x'
        _.add(anchor)
        item['anchor-id'] = anchor

        # for alphabetic sorting
        start = item[key][0].upper()
        if not start in alphabet:
            start = extra
        item['letter'] = start
        item['href'] = url + ['{}.html#{}'.format(start, anchor)]


def game_index(entry):
    e = {
        'url': make_url(entry['href'], entry['Title']),
        'anchor-id': entry['anchor-id']
    }
    tags = []
    if 'beta' in entry['State']:
        tags.append('beta')
    if osg.is_inactive(entry):
        tags.append('inactive since {}'.format(osg.extract_inactive_year(entry)))
    if tags:
        e['tags'] = make_text('({})'.format(', '.join(tags)), 'is-light is-size-7')
    return e


def inspiration_index(inspiration):
    e = {
        'url': make_url(inspiration['href'], inspiration['Name']),
        'anchor-id': inspiration['anchor-id'],
    }
    n = len(inspiration['Inspired entries'])
    if n > 1:
        e['tags'] = make_text('({})'.format(n), 'is-light is-size-7')
    return e


def developer_index(developer):
    e = {
        'url': make_url(developer['href'], developer['Name']),
        'anchor-id': developer['anchor-id']
    }
    n = len(developer['Games'])
    if n > 1:
        e['tags'] = make_text('({})'.format(n), 'is-light is-size-7')
    return e

def shortcut_url(url):

    # remove slash at the end
    if url.endswith('/'):
        url = url[:-1]

    # gitlab
    gl_prefix = 'https://gitlab.com/'
    if url.startswith(gl_prefix):
        return 'GL: ' + url[len(gl_prefix):]
    # github
    gh_prefix = 'https://github.com/'
    if url.startswith(gh_prefix):
        return 'GH: ' + url[len(gh_prefix):]

    # sourceforge
    sf_prefix = 'https://sourceforge.net/projects/'
    if url.startswith(sf_prefix):
        return 'SF: ' + url[len(sf_prefix):]

    # archive link
    ia_prefix = 'https://web.archive.org/web/'
    if url.startswith(ia_prefix):
        return 'Archive: ' + url[len(ia_prefix):]

    # Wikipedia link
    wp_prefix = 'https://en.wikipedia.org/wiki/'
    if url.startswith(wp_prefix):
        return 'WP: ' + url[len(wp_prefix):]

    # cutoff common prefixes
    for prefix in ('http://', 'https://'):
        if url.startswith(prefix):
            return url[len(prefix):]
    # as is
    return url


def convert_inspirations(inspirations, entries):
    entries_references = {entry['Title']:entry['href'] for entry in entries}
    for inspiration in inspirations:
        fields = []
        # media
        if 'Media' in inspiration:
            entries = inspiration['Media']
            entries = [make_url(url, shortcut_url(url)) for url in entries]
            field = make_enumeration(make_text('Media'), entries)
            fields.append(field)
        # inspired entries (with links to them)
        inspired_entries = inspiration['Inspired entries']
        entries = [make_url(entries_references[entry], make_text(entry, 'has-text-weight-semibold')) for entry in inspired_entries]
        name = make_text('Inspired {}'.format(get_plural_or_singular('Game', len(entries)).lower()), 'has-text-weight-semibold')
        field = make_enumeration(name, entries)
        fields.append(field)
        inspiration['fields'] = fields
        inspiration['name'] = inspiration['Name']

def make_url(href, content, title=None):
    if isinstance(content, str):
        content = make_text(content)
    url = {
        'type': 'url',
        'href': href,
        'content': content
    }
    if title:
        url['title'] = title
    return url

def make_icon(css_class):
    return {
        'type': 'icon',
        'class': css_class
    }


def make_text(content, css_class=None):
    text = {
        'type': 'text',
        'text': content
    }
    if css_class:
        text['class'] = css_class
    return text

def make_linebreak():
    return {
        'type': 'linebreak'
    }

def make_enumeration(name, entries, divider=', '):
    enumeration = {
        'type': 'enumeration',
        'name': name,
        'entries': entries,
        'divider': divider
    }
    return enumeration


def developer_profile_link(link):
    if link.endswith('@SF'):
        return 'https://sourceforge.net/u/{}/profile/'.format(link[:-3])
    if link.endswith('@GH'):
        return 'https://github.com/{}'.format(link[:-3])
    if link.endswith('@GL'):
        return 'https://gitlab.com/{}'.format(link[:-3])
    raise RuntimeError('Unknown profile link {}'.format(link))


def convert_developers(developers, entries):
    entries_references = {entry['Title']:entry['href'] for entry in entries}
    for developer in developers:
        fields = []
        # games field
        developed_entries = developer['Games']
        entries = [make_url(entries_references[entry], make_text(entry, 'has-text-weight-semibold')) for entry in developed_entries]
        name = make_text('Developed {}'.format(get_plural_or_singular('Game', len(entries)).lower()), 'has-text-weight-semibold')
        field = make_enumeration(name, entries)
        fields.append(field)
        for field in c.optional_developer_fields:
            if field in developer:
                entries = developer[field]
                if field == 'Contact':
                  # need to replace the shortcuts
                  entries = [make_url(developer_profile_link(entry), entry) for entry in entries]
                elif field in c.url_developer_fields:
                    entries = [make_url(entry, shortcut_url(entry)) for entry in entries]
                else:
                    entries = [make_text(entry) for entry in entries]
                field = make_enumeration(make_text(get_plural_or_singular(field, len(entries))), entries)
                fields.append(field)
        if len(fields) > 1: # if there is Game(s) and more, insert an additional break after games
            fields.insert(1, make_linebreak())
        developer['fields'] = fields
        developer['name'] = developer['Name']


def convert_entries(entries, inspirations, developers):
    inspirations_references = {inspiration['Name']: inspiration['href'] for inspiration in inspirations}
    developer_references = {developer['Name']: developer['href'] for developer in developers}
    for entry in entries:
        fields = []
        if 'Note' in entry:
            fields.append(make_text(entry['Note'], 'is-italic'))
            fields.append(make_linebreak())
        for field in ('Home', 'Inspiration', 'State', 'Media', 'Download', 'Play', 'Developer', 'Keyword'):
            if field in entry:
                e = entry[field]
                divider = ', '
                if isinstance(e[0], osg.osg_parse.ValueWithComment):
                    e = [x.value for x in e]
                if field == 'Inspiration':
                    e = [make_url(inspirations_references[x], make_text(x, 'has-text-weight-semibold')) for x in e]
                elif field == 'Developer':
                    e = [make_url(developer_references[x], make_text(x, 'has-text-weight-semibold')) for x in e]
                elif field == 'Keyword':
                    e = [make_text(x, 'tag ' + ('is-info' if x in c.recommended_keywords else 'is-light')) for x in e]
                    divider = ' '
                elif field in c.url_fields:
                    e = [make_url(x, shortcut_url(x)) for x in e]
                else:
                    e = [make_text(x) for x in e]
                name = make_text(get_plural_or_singular(field, len(e)), 'has-text-weight-semibold')
                field = make_enumeration(name, e, divider)
                fields.append(field)
        fields.append(make_linebreak())
        fields.append(make_text('Technical info', 'has-text-weight-semibold'))
        for field in ('Platform', 'Code language', 'Code license', 'Code repository', 'Code dependency', 'Assets license'):
            if field in entry:
                e = entry[field]
                divider = ', '
                if not e:
                    continue
                if isinstance(e[0], osg.osg_parse.ValueWithComment):
                    e = [x.value for x in e]
                if field == 'Platform':
                    # e = [make_text(x, 'is-size-7 tag {}'.format(platform_color[x])) for x in e]
                    e = [make_url('', make_icon(platform_icon_map[x]), 'Windows') if x in platform_icon_map else make_text(x, 'is-size-7') for x in e]
                    divider = ' '
                elif field == 'Code language':
                    e = [make_url(code_language_references[x], make_text(x, 'is-size-7')) for x in e]
                elif field in c.url_fields:
                    e = [make_url(x, make_text(shortcut_url(x), 'is-size-7')) for x in e]
                else:
                    e = [make_text(x, 'is-size-7') for x in e]
                name = make_text(get_plural_or_singular(field, len(entries)), 'is-size-7')
                field = make_enumeration(name, e, divider)
                fields.append(field)
        entry['fields'] = fields
        entry['name'] = entry['Title']


def add_license_links_to_entries(entries):
    for entry in entries:
        licenses = entry['Code license']
        licenses = [(c.license_urls.get(license.value, ''), license.value) for license in licenses]
        entry['Code license'] = licenses


def generate(entries, inspirations, developers):
    """

    :param entries:
    :param inspirations:
    :param developers:
    """

    # split entries in games and frameworks
    games, frameworks = [], []
    for entry in entries:
        (games, frameworks)[any([keyword in entry['Keyword'] for keyword in c.framework_keywords])].append(entry)

    # preprocess
    preprocess(games, 'Title', games_path)
    preprocess(frameworks, 'Title', frameworks_path)
    entries = games + frameworks
    preprocess(inspirations, 'Name', inspirations_path)
    preprocess(developers, 'Name', developers_path)

    # set internal links up
    convert_inspirations(inspirations, entries)
    convert_developers(developers, entries)
    convert_entries(games, inspirations, developers)
    convert_entries(frameworks, inspirations, developers)

    # set external links up
    add_license_links_to_entries(games)

    # sort into categories
    sorter = lambda item, category: category == item['letter']
    games_by_alphabet = sort_into_categories(games, extended_alphabet, sorter)
    frameworks_by_alphabet = sort_into_categories(frameworks, extended_alphabet, sorter)
    inspirations_by_alphabet = sort_into_categories(inspirations, extended_alphabet, sorter)
    developers_by_alphabet = sort_into_categories(developers, extended_alphabet, sorter)

    genres = [keyword.capitalize() for keyword in c.recommended_keywords]
    games_by_genre = sort_into_categories(games, genres, lambda item, category: category.lower() in item['Keyword'])
    games_by_platform = sort_into_categories(games, c.valid_platforms, lambda item, category: category in item.get('Platform', []), 'Unspecified')
    games_by_language = sort_into_categories(games, c.known_languages, lambda item, category: category in item['Code language'])
    frameworks_by_type = sort_into_categories(frameworks, c.framework_keywords, lambda item, category: category in item['Keyword'])

    # base dictionary
    base = {
        'title': 'OSGL',
        'creation-date': datetime.datetime.utcnow()
    }

    # copy bulma css
    utils.copy_tree(os.path.join(c.web_template_path, 'css'), c.web_css_path)
    #os.mkdir(c.web_css_path)
    #shutil.copy2(os.path.join(c.web_template_path, 'bulma.min.css'), c.web_css_path)

    # create Jinja Environment
    environment = Environment(loader=FileSystemLoader(c.web_template_path), autoescape=True)
    environment.globals['base'] = base
    environment.globals['raise'] = raise_helper

    # multiple times used templates
    template_categorical_index = environment.get_template('categorical_index.jinja')
    template_listing = environment.get_template('listing.jinja')

    # top level folder
    base['url_to'] = partial(url_to, [])

    # index.html
    base['active_nav'] = 'index'
    index = {'subtitle': make_text('Contains information about {} open source games and {} frameworks/tools.'.format(len(games), len(frameworks))) }
    template = environment.get_template('index.jinja')
    write(template.render(index=index), ['index.html'])

    # contribute.html
    base['active_nav'] = 'contribute'
    template = environment.get_template('contribute.jinja')
    write(template.render(), ['contribute.html'])

    # statistics
    base['active_nav'] = 'statistics'

    # preparation
    template = environment.get_template('statistics.jinja')
    data = {
        'title': 'Statistics',
        'sections': []
    }

    # build-systems
    build_systems = []
    field = 'Build system'
    for entry in entries:
        if field in entry['Building']:
            build_systems.extend(entry['Building'][field])
    build_systems = [x.value for x in build_systems]

    unique_build_systems = set(build_systems)
    unique_build_systems = [(l, build_systems.count(l)) for l in unique_build_systems]
    unique_build_systems.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
    unique_build_systems.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)
    section = {
        'title': 'Build system',
        'items': ['{} ({})'.format(*item) for item in unique_build_systems]
    }
    data['sections'].append(section)
    write(template.render(data=data), ['statistics.html'])

    # frameworks folder
    base['url_to'] = partial(url_to, frameworks_path)
    base['active_nav'] = 'frameworks'

    # frameworks by type
    index = divide_in_columns(frameworks_by_type, game_index)
    index['title'] = 'Open source frameworks/tools'
    index['categories'] = c.framework_keywords
    write(template_categorical_index.render(index=index), frameworks_path + ['index.html'])

    # generate games pages
    for letter in extended_alphabet:
        listing = {
            'title': 'Frameworks/tools starting with {}'.format(letter.capitalize()),
            'items': frameworks_by_alphabet[letter]
        }
        write(template_listing.render(listing=listing), frameworks_path +['{}.html'.format(letter.capitalize())])

    # games folder
    base['url_to'] = partial(url_to, games_path)
    base['active_nav'] = 'games'

    # generate games pages
    for letter in extended_alphabet:
        listing = {
            'title': 'Games starting with {}'.format(letter.capitalize()),
            'items': games_by_alphabet[letter]
        }
        write(template_listing.render(listing=listing), games_path + ['{}.html'.format(letter.capitalize())])

    # generate games index
    index = divide_in_columns(games_by_alphabet, game_index)
    index['title'] = 'Open source games - Alphabetical index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), games_path + ['index.html'])

    # genres
    base['active_nav'] = 'filter genres'
    index = divide_in_columns(games_by_genre, game_index)
    index['title'] = 'Open source games - Genre index'
    index['categories'] = genres
    write(template_categorical_index.render(index=index), games_path + ['genres.html'])

    # games by language
    base['active_nav'] = 'filter code language'
    index = divide_in_columns(games_by_language, game_index)
    index['title'] = 'Open source games - Programming language index'
    index['categories'] = c.known_languages
    write(template_categorical_index.render(index=index), games_by_language_path)

    # games by platform
    base['active_nav'] = 'filter platforms'
    index = divide_in_columns(games_by_platform, game_index)
    index['title'] = 'Open source games - Supported platforms index'
    index['categories'] = c.valid_platforms + ('Unspecified',)
    write(template_categorical_index.render(index=index), games_path + ['platforms.html'])

    # inspirations folder
    base['url_to'] = partial(url_to, inspirations_path)
    base['active_nav'] = 'filter inspirations'

    # inspirations

    # inspirations index
    index = divide_in_columns(inspirations_by_alphabet, inspiration_index)
    index['title'] = 'Inspirations - Alphabetical index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), inspirations_path + ['index.html'])

    # inspirations single pages
    for letter in extended_alphabet:
        listing = {
            'title': 'Inspirations ({})'.format(letter.capitalize()),
            'items': inspirations_by_alphabet[letter]
        }
        write(template_listing.render(listing=listing), inspirations_path + ['{}.html'.format(letter.capitalize())])

    # developers folder
    base['url_to'] = partial(url_to, developers_path)
    base['active_nav'] = 'developers'

    # developers single pages
    for letter in extended_alphabet:
        listing = {
            'title': 'Open source game developers ({})'.format(letter.capitalize()),
            'items': developers_by_alphabet[letter]
        }
        write(template_listing.render(listing=listing), developers_path + ['{}.html'.format(letter.capitalize())])

    # developers index
    index = divide_in_columns(developers_by_alphabet, developer_index)
    index['title'] = 'Open source game developers - Alphabetical index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), developers_path + ['index.html'])


if __name__ == "__main__":

    # clean the output directory
    print('clean current static website')
    utils.recreate_directory(c.web_path)

    # load entries, inspirations and developers and sort them
    print('load entries, inspirations and developers')
    entries = osg.read_entries()
    entries.sort(key=lambda x: str.casefold(x['Title']))

    inspirations = osg.read_inspirations()
    inspirations = list(inspirations.values())
    inspirations.sort(key=lambda x: str.casefold(x['Name']))

    developers = osg.read_developers()
    developers = list(developers.values())
    developers.sort(key=lambda x: str.casefold(x['Name']))

    # re-generate static website
    print('re-generate static website')
    generate(entries, inspirations, developers)