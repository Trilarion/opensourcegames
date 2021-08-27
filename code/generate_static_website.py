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

# pre-release

# project LICENSE file not auto recognized by Github (use https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md instead)

# TODO contribute.html add content

# TODO more icons - missing categories
# TODO replace or remove @notices in entries (maybe different entries format)

# TODO everywhere: singular, plural (game, entries, items)

# TODO statistics: better and more statistics with links where possible
# TODO statistics: with nice graphics (pie charts in SVG) with matplotlib, seaborn, plotly?
# TODO statistics: get it from common statistics generator

# TODO frameworks: icons for frameworks/libraryies/tools

# TODO filter by category: icons too large (overlapping)

# TODO games: @see-home/@see-download/@add (ignore or replace?)
# TODO games: top 50 list from Github via their stars with download links (add to entries) and with screenshot
# TODO games: add screenshot ability (add screenshot to database, at least for top 50)

# release

# TODO update Bulma
# TODO everywhere: optimize jinja for line breaks and indention and minimal amount of spaces (and size of files) and minimal amount of repetition of tags

# post-release

# TODO everywhere: meta/title tag
# TODO everywhere: style URLs (Github, Wikipedia, Internet archive, SourceForge, ...)

# TODO inspirations: icon full lamp (not contained in icomoon.io)

# TODO games: developers if more than a single line (collapse, expand?) without JS? (https://stackoverflow.com/questions/41220717/collapse-without-javascript, https://codeconvey.com/html-expand-collapse-text-without-javascript/)
# TODO games: technical info (collapse on click)
# TODO games: link to dependencies (either if existing or if url)
# TODO games: javascript table
# TODO games: repositories comments have too much space after( and before )

# TODO SEO optimizations, google search ...
# TODO sitemap
# TODO Google search console
# TODO <a> rel attribute https://www.w3schools.com/TAGS/att_a_rel.asp

# TODO inspirations: if included in the database, link instead to game

import os
import shutil
import math
import datetime
import time
from functools import partial
from utils import osg, constants as c, utils
from jinja2 import Environment, FileSystemLoader
import html5lib

alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
extra = '0'
extended_alphabet = alphabet + extra
extended_alphabet_names = {k: k for k in extended_alphabet}
alphabet_replacements = {'Á': 'A', 'Å': 'A', 'É': 'E', 'Ł': 'L', 'Ľ': 'L', 'А': 'A', 'Б': 'B', 'Д': 'D', 'И': 'I', 'К': 'K', 'П': 'P'}


games_path = ['games']
frameworks_path = ['frameworks']
inspirations_path = ['inspirations']
developers_path = ['developers']

games_index_path = games_path + ['index.html']
frameworks_index_path = frameworks_path + ['index.html']
inspirations_index_path = inspirations_path + ['index.html']
developers_index_path = developers_path + ['index.html']

games_by_language_path = games_path + ['languages.html']
games_by_genres_path = games_path + ['genres.html']
games_by_platform_path = games_path + ['platforms.html']
games_top50_path = games_path + ['top50.html']

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
    'Linux': 'tux',
    'macOS': 'appleinc',
    'Android': 'android',
    'iOS': 'ios',
    'Web': 'earth',
    'Unspecified': 'device_unknown'
}

genre_icon_map = {
    'Action': 'target',
    'Adventure': 'dice',
    'Arcade': 'pacman',
    'Educational': 'graduation-cap',
    'Game engine': 'car',
    'Puzzle': 'puzzle-piece',
    'Remake': 'undo',
    'Role playing': 'user-secret',
    'Simulation': 'rocket1',
    'Strategy': 'fort-awesome',
    'Cards': 'spades',
    'Music': 'music',
    'Visual novel': 'book',
    'Framework': 'stack',
    'Library': 'library'
}

plurals = {k: k+'s' for k in ('Assets license', 'Contact', 'Code language', 'Code license', 'Developer', 'Download', 'Inspiration', 'Game', 'Keyword', 'Home', 'Homepage', 'Organization', 'Platform', 'Tag')}
for k in ('Media', 'Play', 'Play online', 'State'):
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


framework_names = {
    'tool': 'Tools',
    'framework': 'Frameworks',
    'library': 'Libraries'
}


html5parser = html5lib.HTMLParser(strict=True)


def raise_helper(msg):
    raise Exception(msg)


def is_list(obj):
    return isinstance(obj, list)


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
        print('probem with file {}, see invalid.html'.format(file))
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
        # special treatment of some variables
        start = alphabet_replacements.get(start, start)
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


def shortcut_url(url, name):

    # remove slash at the end
    if url.endswith('/'):
        url = url[:-1]

    # gitlab
    gl_prefix = 'https://gitlab.com/'
    if url.startswith(gl_prefix):
        return [make_text(url[len(gl_prefix):]), make_icon('gitlab')]

    # github
    gh_prefix = 'https://github.com/'
    if url.startswith(gh_prefix):
        return [make_text(url[len(gh_prefix):]), make_icon('github')]

    # sourceforge
    sf_prefix = 'https://sourceforge.net/projects/'
    if url.startswith(sf_prefix):
        return [make_text(url[len(sf_prefix):]), make_icon('sourceforge')]

    # archive link
    ia_prefix = 'https://web.archive.org/web/'
    if url.startswith(ia_prefix):
        return 'Archive: ' + url[len(ia_prefix):]

    # Wikipedia link
    wp_prefix = 'https://en.wikipedia.org/wiki/'
    if url.startswith(wp_prefix):
        # return 'WP: ' + url[len(wp_prefix):]
        return [make_text(name), make_icon('wikipedia')]

    # cutoff common prefixes
    for prefix in ('http://', 'https://'):
        if url.startswith(prefix):
            return url[len(prefix):]
    # as is
    return url


def make_url(href, content, title=None, css_class=None):
    if isinstance(content, str):
        content = make_text(content)
    url = {
        'type': 'url',
        'href': href,
        'content': content
    }
    if title:
        url['title'] = title
    if css_class:
        url['class'] = css_class
    return url


def make_repo_url(x, name):
    # parse comments
    comments = []
    if x.has_comment():
        for c in x.comment.split(','):
            c = c.strip()
            if not c.startswith('@'):
                continue
            c = c.split(' ')
            key = c[0][1:] # without the @
            if len(c) > 1:
                value = c[1]
            if key == 'archived':
                comments.append(make_text('archived', css_class='is-size-7'))
            if key == 'created':
                comments.append(make_text('since {}'.format(value), css_class='is-size-7'))
            if key == 'stars':
                value = int(value)
                if value > 200:
                    comments.append(make_icon('star', 'top rated'))
                elif value > 30:
                    comments.append(make_icon('star-half-full', 'medium rated'))
                else:
                    comments.append(make_icon('star-o', 'low rated'))
    # this is the default element
    url = make_url(x.value, shortcut_url(x.value, name), css_class='is-size-7')
    if comments:
        return make_enumeration([url, make_enclose(make_enumeration(comments), '(', ')')], '')
    else:
        return url


def make_icon(css_class, title=None):
    icon = {
        'type': 'icon',
        'class': css_class,
    }
    if title:
        icon['title'] = title
    return icon


def make_text(content, css_class=None):
    text = {
        'type': 'text',
        'text': content
    }
    if css_class:
        text['class'] = css_class
    return text


def make_nothing():
    return {
        'type': 'nothing'
    }


def make_enclose(entry, left, right):
    enclose = {
        'type': 'enclose',
        'entry': entry,
        'left': left,
        'right': right
    }
    return enclose


def make_enumeration(entries, divider=', '):
    enumeration = {
        'type': 'enumeration',
        'entries': entries,
        'divider': divider
    }
    return enumeration


def make_tags(entries):
    return {
        'type': 'tags',
        'enumeration': make_enumeration(entries, divider='')
    }


def developer_profile_link(link):
    if link.endswith('@SF'):
        return make_url('https://sourceforge.net/u/{}/profile/'.format(link[:-3]), make_icon('sourceforge'), 'Profile on Sourceforge')
    if link.endswith('@GH'):
        return make_url('https://github.com/{}'.format(link[:-3]), make_icon('github'), 'Profile on Github')
    if link.endswith('@GL'):
        return make_url('https://gitlab.com/{}'.format(link[:-3]), make_icon('gitlab'), 'Profile on Gitlab')
    if link.endswith('@BB'):
        return make_url('https://bitbucket.org/{}/'.format(link[:-3]), make_icon('bitbucket'), 'Profile on BitBucket')
    raise RuntimeError('Unknown profile link {}'.format(link))


def convert_inspirations(inspirations, entries):
    entries_references = {entry['Title']:entry['href'] for entry in entries}
    for inspiration in inspirations:
        name = inspiration['Name']
        inspiration['name'] = name

        # media
        if 'Media' in inspiration:
            entries = inspiration['Media']
            entries = [make_url(url, shortcut_url(url, name)) for url in entries]
            inspiration['media'] = [make_text('Media: '), make_enumeration(entries)]

        # inspired entries (with links to them)
        inspired_entries = inspiration['Inspired entries']
        entries = [make_url(entries_references[entry], make_text(entry, 'has-text-weight-semibold')) for entry in inspired_entries]
        name = make_text('Inspired {}: '.format(get_plural_or_singular('Game', len(entries)).lower()), 'has-text-weight-semibold')
        inspiration['inspired'] = [name, make_enumeration(entries)]


def convert_developers(developers, entries):
    entries_references = {entry['Title']:entry['href'] for entry in entries}
    for developer in developers:
        name = developer['Name']
        developer['name'] = name

        # games
        developed_entries = developer['Games']
        entries = [make_url(entries_references[entry], make_text(entry, 'has-text-weight-semibold')) for entry in developed_entries]
        name = make_text('Developed {}:'.format(get_plural_or_singular('Game', len(entries)).lower()), 'has-text-weight-semibold')
        developer['games'] = [name, make_enumeration(entries)]

        # contacts
        contacts = developer.get('Contact', [])
        entries = [developer_profile_link(entry) for entry in contacts]
        developer['contact'] = entries

        # other fields
        for field in ('Organization',):
            if field in developer:
                entries = developer[field]
                if field in c.url_developer_fields:
                    entries = [make_url(entry, shortcut_url(entry, name)) for entry in entries]
                else:
                    entries = [make_text(entry) for entry in entries]
                developer[field.lower()] = [make_text(get_plural_or_singular(field, len(entries))+': '), make_enumeration(entries)]


def create_keyword_tag(keyword):
    if keyword in c.recommended_keywords:
        if keyword in c.framework_keywords:
            url = frameworks_index_path.copy()
        else:
            url = games_by_genres_path.copy()
        url[-1] += '#{}'.format(keyword)
        if keyword.capitalize() in genre_icon_map:
            return make_url(url, [make_icon(genre_icon_map[keyword.capitalize()]), make_text(keyword)], '{} games'.format(keyword), 'tag is-info')
        else:
            return make_url(url, make_text(keyword), '{} games'.format(keyword), 'tag is-info')
    else:
        return make_text(keyword, 'tag is-light')


def create_state_texts(states):
    texts = []
    if 'mature' in states:
        texts.append(make_text('mature', 'is-size-7 has-text-weight-bold has-text-info'))
    else:
        texts.append(make_text('beta', 'is-size-7 has-text-gray-lighter'))
    inactive = [x for x in states if x.startswith('inactive since')]
    if inactive:
        texts.append([make_text(inactive[0], 'is-size-7 has-text-gray-lighter'), make_icon('brightness_3')])
    else:
        texts.append([make_text('active', 'is-size-7 has-text-weight-bold has-text-info'), make_icon('sun')])
    return texts


def convert_entries(entries, inspirations, developers):
    inspirations_references = {inspiration['Name']: inspiration['href'] for inspiration in inspirations}
    developer_references = {developer['Name']: developer['href'] for developer in developers}
    for entry in entries:
        # name
        name = entry['Title']
        entry['name'] = name

        # state
        entry['state'] = create_state_texts(entry['State'])

        # note
        if 'Note' in entry:
            entry['note'] = make_text(entry['Note'], 'is-italic')

        # keywords as tags
        e = [create_keyword_tag(x.value) for x in entry['Keyword']]
        entry['keyword'] = make_tags(e)

        # other normal fields (not technical info)
        for field in ('Home', 'Inspiration', 'Media', 'Download', 'Play', 'Developer'):
            if field in entry:
                e = entry[field]
                divider = ', '
                if isinstance(e[0], osg.osg_parse.ValueWithComment):
                    e = [x.value for x in e]
                if field == 'Inspiration':
                    e = [make_url(inspirations_references[x], make_text(x, 'has-text-weight-semibold')) for x in e]
                elif field == 'Developer':
                    if len(e) > 10: # many devs, print smaller
                        e = [make_url(developer_references[x], make_text(x, 'has-text-weight-semibold is-size-7')) for x in e]
                    else:
                        e = [make_url(developer_references[x], make_text(x, 'has-text-weight-semibold')) for x in e]
                elif field in c.url_fields:
                    e = [make_url(x, shortcut_url(x, name)) for x in e]
                else:
                    e = [make_text(x) for x in e]
                if field == 'Home':  # Home -> Homepage
                    field = 'Homepage'
                elif field == 'Play':  # Play -> Play online
                    field = 'Play online'
                namex = make_text('{}: '.format(get_plural_or_singular(field, len(e))), 'has-text-weight-semibold')
                entry[field.lower()] = [namex, make_enumeration(e, divider)]

        # platforms
        if 'Platform' in entry:
            e = entry['Platform']
            if isinstance(e[0], osg.osg_parse.ValueWithComment):
                e = [x.value for x in e]
        else:
            e = ['Unspecified']
        e = [make_url(games_by_platform_path[:-1] + ['{}#{}'.format(games_by_platform_path[-1], x.lower())], make_icon(platform_icon_map[x]), x) if x in platform_icon_map else make_text(x, 'is-size-7') for x in e]
        namex = make_text('{}:'.format(get_plural_or_singular('Platform', len(e))), 'has-text-weight-semibold')
        entry['platform'] = [namex] + e

        # technical info fields
        for field in ('Code language', 'Code license', 'Code repository', 'Code dependency', 'Assets license'):
            if field in entry:
                e = entry[field]
                divider = ', '
                if not e:
                    continue
                if isinstance(e[0], osg.osg_parse.ValueWithComment) and field != 'Code repository':
                    e = [x.value for x in e]
                if field == 'Code repository':
                    e = [make_repo_url(x, name) for x in e]
                elif field == 'Code language':
                    e = [make_url(code_language_references[x], make_text(x, 'is-size-7')) for x in e]
                elif field == 'Code license' or field == 'Assets license':
                    e = [make_url(c.license_urls[x], x, css_class='is-size-7') if x in c.license_urls else make_text(x, 'is-size-7') for x in e]
                elif field in c.url_fields:
                    e = [make_url(x, shortcut_url(x, name), css_class='is-size-7') for x in e]
                else:
                    e = [make_text(x, 'is-size-7') for x in e]
                namex = make_text('{}: '.format(get_plural_or_singular(field, len(entries))), 'is-size-7')
                entry[field.lower()] = [namex, make_enumeration(e, divider)]

        # build system
        field = 'Build system'
        if field in entry['Building']:
            e = entry['Building'][field]
            divider = ', '
            if isinstance(e[0], osg.osg_parse.ValueWithComment):
                e = [x.value for x in e]
            e = [make_url(c.build_system_urls[x], x, css_class='is-size-7') if x in c.build_system_urls else make_text(x, 'is-size-7') for x in e]
            namex = make_text('{}: '.format(field), 'is-size-7')
            entry[field.lower()] = [namex, make_enumeration(e, divider)]

        entry['raw-path'] = 'https://raw.githubusercontent.com/Trilarion/opensourcegames/master/entries/' + entry['File']


def add_license_links_to_entries(entries):
    for entry in entries:
        licenses = entry['Code license']
        licenses = [(c.license_urls.get(license.value, ''), license.value) for license in licenses]
        entry['Code license'] = licenses


def get_top50_games(games):
    top50_games = []
    for game in games:
        # get stars of repositories
        stars = 0
        for repo in game.get('Code repository', []):
            if repo.has_comment():
                for c in repo.comment.split(','):
                    c = c.strip()
                    if not c.startswith('@'):
                        continue
                    c = c.split(' ')
                    key = c[0][1:]  # without the @
                    if len(c) > 1:
                        value = c[1]
                    if key == 'stars':
                        value = int(value)
                        if value > stars:
                            stars = value
        top50_games.append((game, stars))
    top50_games.sort(key=lambda x:x[1], reverse=True)
    top50_games = top50_games[:50]
    top50_games =[game for game, stars in top50_games]
    return top50_games


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
    # TODO preprocess doesn't set the urls for frameworks correctly fix here, do better later
    for framework in frameworks:
        keyword = [keyword for keyword in c.framework_keywords if keyword in framework['Keyword']][0]
        framework['href'] = frameworks_path + ['{}.html#{}'.format(keyword, framework['anchor-id'])]
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
    inspirations_by_alphabet = sort_into_categories(inspirations, extended_alphabet, sorter)
    developers_by_alphabet = sort_into_categories(developers, extended_alphabet, sorter)

    genres = [keyword.capitalize() for keyword in c.recommended_keywords if keyword not in c.framework_keywords]
    genres.sort()
    games_by_genre = sort_into_categories(games, genres, lambda item, category: category.lower() in item['Keyword'])
    games_by_platform = sort_into_categories(entries, c.valid_platforms, lambda item, category: category in item.get('Platform', []), 'Unspecified')
    games_by_language = sort_into_categories(entries, c.known_languages, lambda item, category: category in item['Code language'])
    frameworks_by_type = sort_into_categories(frameworks, c.framework_keywords, lambda item, category: category in item['Keyword'])

    # extract top 50 Github stars games
    top50_games = get_top50_games(games)


    # base dictionary
    base = {
        'title': 'OSGL',
        'creation-date': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')
    }

    # copy css
    utils.copy_tree(os.path.join(c.web_template_path, 'css'), c.web_css_path)

    # collage_image
    shutil.copyfile(os.path.join(c.web_template_path, 'collage_games.jpg'), os.path.join(c.web_path, 'collage_games.jpg'))

    # create Jinja Environment
    environment = Environment(loader=FileSystemLoader(c.web_template_path), autoescape=True)
    environment.globals['base'] = base
    environment.globals['raise'] = raise_helper
    environment.globals['is_list'] = is_list

    # multiple times used templates
    template_categorical_index = environment.get_template('categorical_index.jinja')
    template_listing_entries = environment.get_template('listing_entries.jinja')

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
    index['title'] = make_text('Open source game frameworks/tools')
    index['subtitle'] = make_text('Index of {} game frameworks/tools'.format(len(frameworks)))
    index['categories'] = c.framework_keywords
    index['category-names'] = framework_names
    index['number_entries_per_category_threshold'] = 0
    index['entry_bold'] = lambda x: 'tags' not in x
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), frameworks_index_path)

    # generate frameworks pages
    for keyword in c.framework_keywords:
        listing = {
            'title': framework_names[keyword],
            'subtitle': make_url(frameworks_index_path, 'Index'),
            'items': frameworks_by_type[keyword]
        }
        write(template_listing_entries.render(listing=listing), frameworks_path +['{}.html'.format(keyword)])

    # games folder
    base['url_to'] = partial(url_to, games_path)
    base['active_nav'] = 'games'

    # generate games pages
    for letter in extended_alphabet:
        listing = {
            'title': 'Games starting with {}'.format(letter.capitalize()),
            'items': games_by_alphabet[letter]
        }
        write(template_listing_entries.render(listing=listing), games_path + ['{}.html'.format(letter.capitalize())])

    # generate games index
    index = divide_in_columns(games_by_alphabet, game_index)
    index['title'] = make_text('Open source games')
    index['subtitle'] = make_text('Alphabetical index of {} games'.format(len(games)))
    index['categories'] = extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['number_entries_per_category_threshold'] = 20
    index['entry_bold'] = lambda x: 'tags' not in x
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), games_index_path)

    # genres
    base['active_nav'] = ['filter', 'genres']
    index = divide_in_columns(games_by_genre, game_index)
    index['title'] = make_text('Open source games')
    index['subtitle'] = make_text('Index by game genre')
    index['categories'] = genres
    index['category-names'] = {k:[make_icon(genre_icon_map[k]), make_text(k)] if k in genre_icon_map else make_text(k) for k in index['categories']}
    index['number_entries_per_category_threshold'] = 25
    index['entry_bold'] = lambda x: 'tags' not in x
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), games_by_genres_path)

    # games by language
    base['active_nav'] = ['filter', 'code language']
    index = divide_in_columns(games_by_language, game_index)
    index['title'] = 'Open source games and frameworks'
    index['subtitle'] = make_text('Index by programming language')
    index['categories'] = c.known_languages
    index['category-names'] = {k:k for k in index['categories']}
    index['number_entries_per_category_threshold'] = 15
    index['entry_bold'] = lambda x: 'tags' not in x
    index['category-infos'] = {category: make_url(c.language_urls[category], 'Language information', css_class='is-size-7') for category in c.known_languages if category in c.language_urls}
    write(template_categorical_index.render(index=index), games_by_language_path)

    # games by platform
    base['active_nav'] = ['filter', 'platforms']
    index = divide_in_columns(games_by_platform, game_index)
    index['title'] = 'Open source games and frameworks'
    index['subtitle'] = make_text('Index by supported platform')
    index['categories'] = c.valid_platforms + ('Unspecified',)
    index['category-names'] = {k:[make_icon(platform_icon_map[k]), make_text(k)] for k in index['categories']}
    index['number_entries_per_category_threshold'] = 15
    index['entry_bold'] = lambda x: 'tags' not in x
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), games_by_platform_path)

    # top 50 games
    base['active_nav'] = ['filter', 'top50']
    listing = {
        'title': 'GitHub Stars Top 50',
        'subtitle': '50 highest rated (by stars on Github) open source games in the database',
        'items': top50_games
    }
    write(template_listing_entries.render(listing=listing), games_top50_path)

    # inspirations folder
    base['url_to'] = partial(url_to, inspirations_path)
    base['active_nav'] = 'inspirations'

    # inspirations

    # inspirations index
    index = divide_in_columns(inspirations_by_alphabet, inspiration_index)
    index['title'] = 'Inspirations'
    index['subtitle'] = make_text('Alphabetical index of {} games used as inspirations'.format(len(inspirations)))
    index['categories'] = extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['number_entries_per_category_threshold'] = 10
    index['entry_bold'] = lambda x: 'tags' in x
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), inspirations_index_path)

    # inspirations single pages
    template_listing_inspirations = environment.get_template('listing_inspirations.jinja')
    for letter in extended_alphabet:
        listing = {
            'title': 'Inspirations ({})'.format(letter.capitalize()),
            'items': inspirations_by_alphabet[letter]
        }
        write(template_listing_inspirations.render(listing=listing), inspirations_path + ['{}.html'.format(letter.capitalize())])

    # developers folder
    base['url_to'] = partial(url_to, developers_path)
    base['active_nav'] = 'developers'

    # developers single pages
    template_listing_developers = environment.get_template('listing_developers.jinja')
    for letter in extended_alphabet:
        listing = {
            'title': 'Open source game developers ({})'.format(letter.capitalize()),
            'items': developers_by_alphabet[letter]
        }
        write(template_listing_developers.render(listing=listing), developers_path + ['{}.html'.format(letter.capitalize())])

    # developers index
    index = divide_in_columns(developers_by_alphabet, developer_index)
    index['title'] = 'Open source game developers'
    index['subtitle'] = make_text('Alphabetical index of {} developers'.format(len(developers)))
    index['categories'] = extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['number_entries_per_category_threshold'] = 10
    index['entry_bold'] = lambda x: 'tags' in x
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), developers_index_path)


if __name__ == "__main__":

    start_time = time.process_time()

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

    # timing
    print('took {:.3f}s'.format(time.process_time()-start_time))