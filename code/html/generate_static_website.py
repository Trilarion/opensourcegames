"""
Generates the static website.

Uses

- Jinja2 (https://jinja.palletsprojects.com/en/2.11.x/)
- Simple-DataTables (https://github.com/fiduswriter/Simple-DataTables)

Sitemap is not needed, only for large projects with lots of JavaScript und many pages that aren't discoverable.
"""

# TODO tab: new filter tab (playable in a browser) with tiles (https://bulma.io/documentation/layout/tiles/) sorted by genre (just as normal list so far, no tiles yet)
# TODO tab: new filter tab (my top 100) with games I really like (mature and I tried them and there is a download for each of them) and some categories with explanation why and possible link to a review on the blog (like evil cult), still need to to that

# TODO table: state, os, license smaller

# TODO categories: put more explanations on the category pages and the categories (number and short sentences)
# TODO categories: use moon year as shortcut for inactive, only make an alt tag for the moon (inactive since)

# TODO keywords: content, multiplayer replace by icons (open, commercial (dollar signs))
# TODO keywords: explain most common ones (as alt-text maybe?)

# TODO general: most people only come to the main page, put more information there (direct links to genres, ...)
# TODO general: minimize tag usage: jinja template optimization for line breaks and indention and minimal amount of spaces (and size of files) and minimal amount of repetition of tags
# TODO general: too many spans, especially for text (maybe just plain text), also text with URLs inside is difficult (but why)
# TODO general: replace or remove @notices like @add in entries (these notices should go to () comments anyway
# TODO general: check singular, plural (game, entries, items) although support is already quite good for that (Code Languages, ...)
# TODO general: better link replacements for showing the urls of links
# TODO general: style URLs (Github, Wikipedia, Internet archive, SourceForge, ...)
# TODO general: update Bulma (already at latest version)
# TODO general: meta/title+description tag
# TODO general: meta description of the pages, fill them
# TODO general: optimize layout for mobile view (quite good already)
# TODO general: meta titles for all pages, make them nice because they appear in search results! (https://www.contentpowered.com/blog/good-ctr-search-console/)
# TODO general: <a> rel attribute https://www.w3schools.com/TAGS/att_a_rel.asp

# TODO idea: text description automatically generate from keywords, state, and technical informations for example: First-person action shooter written in C++, inspired by ... but inactive for 7 years.

# TODO statistics: should have disclaimer (warning or info box) about accuracy with link to contribute guidelines at the top
# TODO statistics: better and more statistics with links where possible
# TODO statistics: get it from common statistics generator
# TODO statistics: normalization, what if there are multiple entries per field (pie chart would be wrong, better to show bar chart instead)
# TODO statistics: state (beta, mature x active, inactive)
# TODO statistics: non essential keywords

# TODO games: developer details is too small to click on some devices, maybe details is-size6 instead (make technical details size 6 but with more)
# TODO games: keyword tags underlined to indicate links
# TODO games: @see-home/@see-download/@add (ignore or replace?)
# TODO games: top 50 list from Github via their stars with download links (add to entries)
# TODO games: order: homepage, inspiration, download, developer
# TODO games: link to dependencies (either if existing or if url)
# TODO games: repositories comments have too much space after( and before ) (use icons without span and with pr-0 on the icon
# TODO games: show or not show additional game description (info field)?? show only first line of info (which should be a short description or make it a field (only for popular ones), otherwise rely on keywords)
# TODO games: cross-references for code dependencies if included
# TODO games: "for adults" tagged need a special icon warning (not safe for work or something)
# TODO games: use genre icon after the game title (or before)
# TODO games: use moon or sun icon before inactive, not afterwards

# TODO contribute: contribute.html add content (especially what volunteers can be done)

# TODO developers: anchors to non-latin written developers do not work (chinese names have simply xxxxx)
# TODO developers: developers without a name (or with a zero width name)
# TODO developers: level with github, sourceforge links in one item (on mobile on one line)
# TODO developers: gitlab and bitbucket user profiles

# TODO inspirations: icon full lamp (not contained in icomoon.io)
# TODO inspirations: if included in the database, link instead to game (cross-reference)
# TODO inspirations: add media links and genres, maybe also years and original developer

import os
import shutil
import math
import datetime
import time
import json
from functools import partial
from utils import osg, constants as c, utils, osg_statistics as stat, osg_parse
from jinja2 import Environment, FileSystemLoader
import html5lib

# the categories for the alphabetical indices, letters A-Z, used for identification and as link names internally
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
# the internal category name for all names not starting with a letter
extra = '0'
extended_alphabet = alphabet + extra
# and how they are displayed
extended_alphabet_names = {k: k for k in alphabet}
extended_alphabet_names[extra] = '0-9'
# especially for developers, replacements from other alphabets
alphabet_replacements = {'Á': 'A', 'Å': 'A', 'Ä': 'A', 'É': 'E', 'ⴹ': 'E', 'Ł': 'L', 'Ľ': 'L', 'А': 'A', 'Б': 'B', 'Д': 'D', 'И': 'I', 'К': 'K', 'П': 'P', 'Ö': 'O', 'Ü': 'U', 'ζ': 'Z'}

TOP_INSPIRATION_THRESHOLD = 4  # at least that many inspired games
TOP_DEVELOPER_THRESHOLD = 4    # at least that many developed games

# the subfolder structure
games_path = ['games']
non_games_path = ['frameworks']
inspirations_path = ['inspirations']
developers_path = ['developers']
statistics_path = ['statistics']

# derived paths
games_index_path = games_path + ['index.html']
non_games_index_path = non_games_path + ['index.html']
inspirations_index_path = inspirations_path + ['index.html']
developers_index_path = developers_path + ['index.html']
statistics_index_path = statistics_path + ['index.html']

games_by_language_path = games_path + ['languages.html']
games_by_genres_path = games_path + ['genres.html']
games_by_platform_path = games_path + ['platforms.html']
games_top50_path = games_path + ['top50.html']
games_kids_path = games_path + ['kids.html']
games_web_path = games_path + ['web.html']
games_libre_path = games_path + ['libre.html']

# those either are repos with many projects in it or are projects that have commercial content and there is no binary
# release or there is only a commercial binary release, so you cannot play them right away for free
github_top50_ignored_repos = ('https://github.com/Hopson97/MineCraft-One-Week-Challenge.git', 'https://github.com/jdah/minecraft-weekend.git', 'https://github.com/TerryCavanagh/vvvvvv.git',
                              'https://github.com/nicholas-ochoa/OpenSC2K.git', 'https://github.com/BlindMindStudios/StarRuler2-Source.git', 'https://github.com/TheMozg/awk-raycaster.git',
                              'https://github.com/PistonDevelopers/hematite.git', 'https://github.com/keendreams/keen.git', 'https://github.com/ddevault/TrueCraft.git')

# TODO currently not used, use?
platform_color = {
    'Windows': 'is-danger',
    'Linux': 'is-link',
    'macOS': 'is-success',
    'Android': 'is-black',
    'iOS': 'is-primary',
    'Web': 'is-warning',
}

# map from supported OS name to icon name
platform_icon_map = {
    'Windows': 'windows',
    'Linux': 'tux',
    'macOS': 'appleinc',
    'Android': 'android',
    'iOS': 'ios',
    'Web': 'earth',
    'Unspecified': 'device_unknown'
}

# map from genre name to icon name
genre_icon_map = {
    'Action': 'target',
    'Arcade': 'pacman',
    'Adventure': 'dice',
    'Educational': 'graduation-cap',
    'Game engine': 'car',
    'Puzzle': 'puzzle-piece',
    'Remake': 'undo',
    'Role playing': 'user-secret',
    'Simulation': 'rocket1',
    'Strategy': 'fort-awesome',
    'Cards': 'spades',
    'Board': 'chess',
    'Music': 'music',
    'Visual novel': 'book',
    'Platform': 'directions_run',
    'Sports': 'soccer-court',
    'Framework': 'stack',
    'Library': 'library'
}

# cross-references to the language pages
code_language_references = {language: games_by_language_path[:-1] + ['{}#{}'.format(games_by_language_path[-1], language.lower())] for language in c.known_languages}

# map of internal non game names to display names (which are in plural)
non_game_category_names = {
    'tool': 'Tools',
    'framework': 'Frameworks',
    'library': 'Libraries',
    'game engine': 'Game Engines'
}

# we check the output html structure every time
html5parser = html5lib.HTMLParser(strict=True)

# file hashes for detecting changes
previous_files = {}

# pluralization (mostly with s, but there are a few exceptions)
plurals = {k: k+'s' for k in ('Assets license', 'Contact', 'Code language', 'Code license', 'Developer', 'Download', 'Inspiration', 'Game', 'Keyword', 'Home', 'Homepage', 'Organization', 'Platform', 'Tag')}
for k in ('Media', 'Play', 'Play online', 'State'):
    plurals[k] = k
for k in ('Code repository', 'Code dependency'):
    plurals[k] = k[:-1] + 'ies'


def get_plural_or_singular(name, amount):
    """
    Gets the pluralization of a known word for a known amount. Helper function.
    """
    if not name in plurals.keys():
        raise RuntimeError('"{}" not a known singular!'.format(name))
    if amount == 1:
        return name
    return plurals[name]


def file_hash(text):
    """
    Removes the last updated ... line from html file and the data line from svg and then computes a hash.
    :param text:
    :return:
    """
    text = text.split('\n')
    text = [t for t in text if not any(t.startswith(prefix) for prefix in ('  This website is built ', '    <dc:date>'))]
    text = ''.join(text)
    return hash(text)


def raise_helper(msg):
    """
    Helper, because raise in lambda expression is a bit cumbersome.
    (ref. https://stackoverflow.com/questions/8294618/define-a-lambda-expression-that-raises-an-exception)
    """
    raise Exception(msg)


def write(text, file):
    """
    Writes a generated HTML page to a file, but checks with a HTML parser before.
    :param text:
    :param file:
    """
    # output file
    if isinstance(file, str):
        file = [file]
    file = os.path.join(c.web_path, *file)

    # check file hash and use previous version
    if file in previous_files and previous_files[file]['hash'] == file_hash(text):
        # no significant change, use previous version instead
        text = previous_files[file]['text']
    else:
        # validate text
        try:
            html5parser.parse(text)
        except Exception as e:
            utils.write_text(os.path.join(c.web_path, 'invalid.html'), text)  # for further checking with https://validator.w3.org/
            print('problem with file {}, see invalid.html'.format(file))
            raise RuntimeError(e)

    # create output directory if necessary
    containing_dir = os.path.dirname(file)
    if not os.path.isdir(containing_dir):
        os.mkdir(containing_dir)

    # write text
    utils.write_text(file, text)


def sort_into_categories(items, categories, fit, unknown_category_name=None):
    """
    Given a list of items and a list of categories and a way to determine if an item fits into a category creates
    lists of items fitting in each category as well as a list of items that fit in no category.

    :return: A mapping category (or unknown_category_name) -> sub-list of items in that category
    """
    categorized_sublists = {}
    for category in categories:
        sublist = [item for item in items if fit(item, category)]
        categorized_sublists[category] = sublist
    if unknown_category_name:
        # now those that do not fit
        sublist = [item for item in items if not any(fit(item, category) for category in categories)]
        categorized_sublists[unknown_category_name] = sublist
    return categorized_sublists


def divide_in_three_columns_and_transform(categorized_lists, transform):
    """
    Used for creating table of content pages for the entries.
    :param transform:
    :param categorized_lists:
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


def preprocess(items, key, url):
    """
    Sets a few additional fields in the entries, inspirations, developers in order to generate the right content from
    them later.

    :param url:
    :param items:
    :param key:
    :return:
    """
    _ = set() # this is just to avoid duplicating anchors
    for item in items:
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


def entry_index(entry):
    """
    Prepares an entry for being an index in a categorical index page.
    """
    e = {
        'url': make_url(entry['href'], entry['Title']),
        'anchor-id': entry['anchor-id'],
        'bold': 'mature' in entry['State']
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
    """
    Prepares an inspiration for being an index in a categorical index page.
    """
    n = len(inspiration['Inspired entries'])
    e = {
        'url': make_url(inspiration['href'], inspiration['Name']),
        'anchor-id': inspiration['anchor-id'],
        'bold': n >= TOP_INSPIRATION_THRESHOLD
    }
    if n > 1:
        e['tags'] = make_text('({})'.format(n), 'is-light')
    return e


def developer_index(developer):
    """
    Prepares a developer for being an index in a categorical index page.
    """
    n = len(developer['Games'])
    e = {
        'url': make_url(developer['href'], developer['Name']),
        'anchor-id': developer['anchor-id'],
        'bold': n >= TOP_DEVELOPER_THRESHOLD
    }
    if n > 1:
        e['tags'] = make_text('({})'.format(n), 'is-light is-size-7')
    return e


def shortcut_url(url, name):
    """

    :param url:
    :param name:
    :return:
    """
    # remove slash at the end
    if url.endswith('/'):
        url = url[:-1]

    # gitlab
    gl_prefix = 'https://gitlab.com/'
    if url.startswith(gl_prefix):
        return [make_icon('gitlab', css='is-link'), make_text(url[len(gl_prefix):])]

    # github
    gh_prefix = 'https://github.com/'
    if url.startswith(gh_prefix):
        return [make_icon('github', css='is-link'), make_text(url[len(gh_prefix):])]

    # sourceforge
    sf_prefix = 'https://sourceforge.net/projects/'
    if url.startswith(sf_prefix):
        return [make_icon('sourceforge', css='is-link'), make_text(url[len(sf_prefix):])]

    # archive link
    ia_prefix = 'https://web.archive.org/web/'
    if url.startswith(ia_prefix):
        # return 'Archive: ' + url[len(ia_prefix):]
        return [make_icon('library', css='is-link'), make_text(url[len(ia_prefix):])]

    # Wikipedia link
    wp_prefix = 'https://en.wikipedia.org/wiki/'
    if url.startswith(wp_prefix):
        # return 'WP: ' + url[len(wp_prefix):]
        return [make_icon('wikipedia', css='is-link'), make_text(name)]

    # cutoff common prefixes
    for prefix in ('http://', 'https://'):
        if url.startswith(prefix):
            return url[len(prefix):]
    # as is
    return url


def make_url(href, content, title=None, css_class=None):
    """

    :param href:
    :param content:
    :param title:
    :param css_class:
    :return:
    """
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
    """

    :param x:
    :param name:
    :return:
    """
    # parse comments
    comments = []
    if isinstance(x, osg_parse.Value):
        for c in x.comment.split(','):
            c = c.strip()
            if not c.startswith('@'):
                continue
            c = c.split(' ')
            key = c[0][1:] # without the @
            if len(c) > 1:
                value = c[1]
            if key == 'archived':
                comments.append(make_text('archived'))
            if key == 'created':
                comments.append(make_text('since {}'.format(value)))
            if key == 'stars':
                value = int(value)
                if value > 200:
                    comments.append(make_icon('star', 'top rated'))
                elif value > 30:
                    comments.append(make_icon('star-half-full', 'medium rated'))
                else:
                    comments.append(make_icon('star-o', 'low rated'))
    # this is the default element
    url = make_url(x, shortcut_url(x, name))
    if comments:
        return make_enumeration([url, make_enclose(make_enumeration(comments), '(', ')')], '')
    else:
        return url


def make_icon(id, title=None, css=None):
    """

    :param id:
    :param title:
    :return:
    """
    if not css:
        css = 'has-text-black'  # safeguard
    icon = {
        'type': 'icon',
        'id': id,
        'css': css
    }
    if title:
        icon['title'] = title
    return icon


def make_text(content, css_class=None):
    """

    :param content:
    :param css_class:
    :return:
    """
    text = {
        'type': 'text',
        'text': content
    }
    if css_class:
        text['class'] = css_class
    return text


def make_enclose(entry, left, right):
    """

    :param entry:
    :param left:
    :param right:
    :return:
    """
    enclose = {
        'type': 'enclose',
        'entry': entry,
        'left': left,
        'right': right
    }
    return enclose


def make_enumeration(entries, divider=', '):
    """

    :param entries:
    :param divider:
    :return:
    """
    enumeration = {
        'type': 'enumeration',
        'entries': entries,
        'divider': divider
    }
    return enumeration


def make_tags(entries):
    """

    :param entries:
    :return:
    """
    return {
        'type': 'tags',
        'enumeration': make_enumeration(entries, divider='')
    }


def make_img(file, width, height):
    """

    :param file:
    :param width:
    :param height:
    :return:
    """
    return {
        'type': 'image',
        'file': file,
        'width': width,
        'height': height
    }


def developer_profile_link(link):
    """
    Creates links to developer profiles.

    :param link: Shortcut link from the developer contact field.
    :return: A URL to a profile page.
    """
    if link.endswith('@SF'):
        return make_url('https://sourceforge.net/u/{}/profile/'.format(link[:-3]), make_icon('sourceforge', css='has-text-link'), 'User {} on Sourceforge'.format(link[:-3]))
    if link.endswith('@GH'):
        return make_url('https://github.com/{}'.format(link[:-3]), make_icon('github', css='has-text-link'), 'User {} on Github'.format(link[:-3]))
    if link.endswith('@GL'):
        return make_url('https://gitlab.com/{}'.format(link[:-3]), make_icon('gitlab', css='has-text-link'), 'User {} on Gitlab'.format(link[:-3]))
    if link.endswith('@BB'):
        return make_url('https://bitbucket.org/{}/'.format(link[:-3]), make_icon('bitbucket', css='has-text-link'), 'User {} on BitBucket'.format(link[:-3]))
    raise RuntimeError('Unknown profile link {}'.format(link))


def convert_inspirations(inspirations, entries):
    """

    :param inspirations:
    :param entries:
    :return:
    """
    entries_references = {entry['Title']: entry['href'] for entry in entries}
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
        entries = [make_url(entries_references[entry], make_text(entry)) for entry in inspired_entries]
        name = make_text('Inspired {}: '.format(get_plural_or_singular('Game', len(entries)).lower()), 'has-text-weight-semibold')
        inspiration['inspired'] = [name, make_enumeration(entries)]


def convert_developers(developers, entries):
    """

    :param developers:
    :param entries:
    :return:
    """
    entries_references = {entry['Title']:entry['href'] for entry in entries}
    for developer in developers:
        name = developer['Name']
        developer['name'] = name

        # games
        developed_entries = developer['Games']
        entries = [make_url(entries_references[entry], make_text(entry)) for entry in developed_entries]
        name = make_text('Developed {}: '.format(get_plural_or_singular('Game', len(entries)).lower()), 'has-text-weight-semibold')
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
    """
    Creates the tag element for a single keyword.
    :param keyword:
    :return:
    """
    if keyword in c.recommended_keywords:
        if keyword in c.non_game_keywords:
            url = non_games_index_path.copy()
        else:
            url = games_by_genres_path.copy()
        url[-1] += '#{}'.format(keyword)
        # TODO are icons looking good in the keyword tags (I somehow doubt it), maybe put them separately somewhere?
        #if keyword.capitalize() in genre_icon_map:
        #    return make_url(url, [make_icon(genre_icon_map[keyword.capitalize()]), make_text(keyword)], '{} games'.format(keyword), 'tag is-light is-link')
        tooltip = non_game_category_names[keyword] if keyword in non_game_category_names else '{} games'.format(keyword.capitalize())
        return make_url(url, make_text(keyword), tooltip, 'tag is-light is-link') # TODO underline tag needs <u> and it should be generalized
    else:
        return make_text(keyword, 'tag is-light')


def create_state_texts(states):
    """
    State texts for level items on the right
    :param states:
    :return:
    """
    if 'mature' in states:
        state = make_text('mature', 'has-text-weight-bold')
    else:
        state = make_text('beta')
    inactive = [x for x in states if x.startswith('inactive since')]
    if inactive:
        activity = [make_icon('brightness_3'), make_text(inactive[0], '')]
    else:
        activity = [make_icon('sun'), make_text('active', 'has-text-weight-bold')]
    return [state, activity]


def convert_entries(entries, inspirations, developers):
    """

    :param entries:
    :param inspirations:
    :param developers:
    :return:
    """
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
        e = [create_keyword_tag(x) for x in entry['Keyword']]
        entry['keyword'] = make_tags(e)

        # other normal fields (not technical info)
        for field in ('Home', 'Inspiration', 'Media', 'Download', 'Play', 'Developer'):
            if field in entry:
                e = entry[field]
                divider = ', '
                if field == 'Inspiration':
                    e = [make_url(inspirations_references[x], make_text(x)) for x in e]
                elif field == 'Developer':
                    e = [make_url(developer_references[x], make_text(x)) for x in e]
                elif field in c.url_fields:
                    e = [make_url(x, shortcut_url(x, name)) for x in e]
                else:
                    e = [make_text(x) for x in e]
                if field == 'Home':  # Home -> Homepage
                    field = 'Homepage'
                    # first entry bold
                    e[0]['class'] = 'has-text-weight-semibold'
                elif field == 'Play':  # Play -> Play online
                    field = 'Play online'
                namex = make_text('{}: '.format(get_plural_or_singular(field, len(e))))
                entry[field.lower()] = [namex, make_enumeration(e, divider)]

        # platforms
        if 'Platform' in entry:
            e = entry['Platform']
        else:
            e = ['Unspecified']
        e = [make_url(games_by_platform_path[:-1] + ['{}#{}'.format(games_by_platform_path[-1], x.lower())], make_icon(platform_icon_map[x], css='has-text-link is-size-6'), x) if x in platform_icon_map else make_text(x) for x in e]
        # namex = make_text('{}: '.format(get_plural_or_singular('Platform', len(e))))
        # entry['state'].insert(0, [namex] + e)
        entry['state'].insert(0, e)

        # technical info fields
        for field in ('Code language', 'Code license', 'Code repository', 'Code dependency', 'Assets license'):
            if field in entry:
                e = entry[field]
                divider = ', '
                if not e:
                    continue
                if field == 'Code repository':
                    e = [make_repo_url(x, name) for x in e]
                elif field == 'Code language':
                    e = [make_url(code_language_references[x], make_text(x)) for x in e]
                elif field == 'Code license' or field == 'Assets license':
                    e = [make_url(c.license_urls[x], x) if x in c.license_urls else make_text(x) for x in e]
                elif field in c.url_fields:
                    e = [make_url(x, shortcut_url(x, name)) for x in e]
                else:
                    e = [make_text(x) for x in e]
                namex = make_text('{}: '.format(get_plural_or_singular(field.capitalize(), len(entries))))
                entry[field.lower()] = [namex, make_enumeration(e, divider)]

        # build system
        field = 'Build system'
        if field in entry['Building']:
            e = entry['Building'][field]
            divider = ', '
            e = [make_url(c.build_system_urls[x], x) if x in c.build_system_urls else make_text(x) for x in e]
            namex = make_text('{}: '.format(field))
            entry[field.lower()] = [namex, make_enumeration(e, divider)]

        entry['raw-path'] = 'https://raw.githubusercontent.com/Trilarion/opensourcegames/master/entries/' + entry['File']


def add_license_links_to_entries(entries):
    """

    :param entries:
    :return:
    """
    for entry in entries:
        licenses = entry['Code license']
        licenses = [(c.license_urls.get(license, ''), license) for license in licenses]
        entry['Code license'] = licenses


def get_top50_games(games):
    """

    :param games:
    :return:
    """
    top50_games = []
    for game in games:
        # get stars of repositories
        stars = 0
        for repo in game.get('Code repository', [])[:1]:  # take at most one
            if repo in github_top50_ignored_repos:
                continue
            if isinstance(repo, osg_parse.Value):
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
    top50_games = top50_games[:50]  # get top 50
    top50_games =[game for game, stars in top50_games]
    return top50_games


def add_screenshot_information(entries):
    """

    :param entries:
    :return:
d    """
    # read screenshot information
    overview = osg.read_screenshots_overview()

    # iterate over entries
    for entry in entries:
        # get screenshots entry
        name = osg.canonical_name(entry['Title'])  # TODO should be stored upon loading I guess
        info = overview.get(name, {})
        screenshots = []
        for id, item in info.items():
            width = item[0]
            height = item[1]
            if item[2] and not item[2].startswith('!'):
                url = item[2]
            else:
                url = None
            file = ['screenshots', '{}_{:02d}.jpg'.format(name, id)]
            img = make_img(file, width, height)
            if url:
                screenshot = make_url(url, img)
            else:
                screenshot = img
            screenshots.append(screenshot)
        if screenshots:
            entry['screenshots'] = screenshots


def create_table_json_data(entries):
    """
    We assume that everything including internal is setup correctly.
    Columns are Title, Link (entry, first homepage), State, Essential Keywords, Language, License
    :param entries:
    :return:
    """
    # create json structure
    db = {'headings': ['Title', 'State', 'Tags', 'Platform', 'Language', 'License']}
    data = []
    for entry in entries:
        title = '<a href="{}" class="has-text-weight-semibold">{}</a> <a href="{}"><i class="icon-new-tab"></i></a>'.format(url_to([], entry['href']), entry['Title'], entry['Home'][0])
        state = ', '.join(entry['State'])
        tags = entry['Keyword']
        tags = [tag for tag in tags if tag in c.interesting_keywords]
        tags = ', '.join(tags)
        platform = entry.get('Platform', ['-'])
        platform = ', '.join(platform)
        language = ', '.join(entry['Code language'])
        license = entry['Code license']
        license = ', '.join(license)
        data.append([title, state, tags, platform, language, license])
    data.sort(key=lambda x: str.casefold(x[0]))
    db['data'] = data

    # write out
    text = json.dumps(db, indent=1)
    os.makedirs(c.web_data_path, exist_ok=True)
    utils.write_text(os.path.join(c.web_data_path, 'entries.json'), text)


def create_statistics_section(entries, field, title, file_name, chartmaker, sub_field=None):
    """
    Creates a statistics section for a given field name from entries and a given chart type (see stat.export_xxx_chart)
    :return:
    """
    statistics = stat.get_field_statistics(entries, field, sub_field)
    statistics = stat.truncate_stats(statistics, 10)
    file = os.path.join(c.web_path, 'statistics', file_name)
    chartmaker([s for s in statistics if s[0] != 'N/A'], file)
    # read back and check if identical with old version (up to date)
    text = utils.read_text(file)
    if file in previous_files and previous_files[file]['hash'] == file_hash(text):
        # use old version instead
        text = previous_files[file]['text']
        utils.write_text(file, text)
    section = {
        'title': title,
        'id': osg.canonical_name(title),
        'items': ['{} ({})'.format(*item) for item in statistics],
        'chart': statistics_path + [file_name]
    }
    return section


def generate(entries, inspirations, developers):
    """
    Regenerates the whole static website given an already imported set of entries, inspirations and developers.
    These datasets must be valid for each other, i.e. each inspiration listed in entries must also have an
    entry in inspirations and the same holds for developers.
    """

    # split entries in games and non-games
    games, non_games = [], []
    for entry in entries:
        (games, non_games)[any([keyword in entry['Keyword'] for keyword in c.non_game_keywords])].append(entry)

    # preprocess
    preprocess(games, 'Title', games_path)
    preprocess(non_games, 'Title', non_games_path)
    # TODO preprocess doesn't set the urls for frameworks correctly fix here, do better later
    for non_game in non_games:
        keyword = [keyword for keyword in c.non_game_keywords if keyword in non_game['Keyword']][0]
        non_game['href'] = non_games_path + ['{}.html#{}'.format(keyword, non_game['anchor-id'])]
    entries = games + non_games
    preprocess(inspirations, 'Name', inspirations_path)
    preprocess(developers, 'Name', developers_path)

    # set internal links up
    convert_inspirations(inspirations, entries)
    convert_developers(developers, entries)
    convert_entries(games, inspirations, developers)
    convert_entries(non_games, inspirations, developers)

    # create entries.json for the table
    create_table_json_data(entries)

    # create statistics data
    statistics_data = {
        'title': 'Statistics',
        'sections': []
    }

    # supported platforms
    section = create_statistics_section(entries, 'Platform', 'Supported platforms', 'supported_platforms.svg', partial(stat.export_bar_chart, aspect_ratio=0.7, tick_label_rotation=45))
    statistics_data['sections'].append(section)

    # code languages
    section = create_statistics_section(entries, 'Code language', 'Code languages', 'code_languages.svg', partial(stat.export_bar_chart, aspect_ratio=1.5, tick_label_rotation=45))
    statistics_data['sections'].append(section)

    # code license
    section = create_statistics_section(entries, 'Code license', 'Code licenses', 'code_licenses.svg', partial(stat.export_bar_chart, aspect_ratio=1.5, tick_label_rotation=45))
    statistics_data['sections'].append(section)

    # code dependencies
    section = create_statistics_section(entries, 'Code dependency', 'Code dependencies', 'code_dependencies.svg', partial(stat.export_bar_chart, aspect_ratio=1.5, tick_label_rotation=45))
    statistics_data['sections'].append(section)

    # build-systems
    section = create_statistics_section(entries, 'Build system', 'Build systems', 'build_systems.svg', stat.export_pie_chart, sub_field='Building')
    statistics_data['sections'].append(section)

    # set external links up (statistics and entries.json doesn't work anymore beyond that point)
    add_license_links_to_entries(entries)

    # sort into categories
    sorter = lambda item, category: category == item['letter']
    games_by_alphabet = sort_into_categories(games, extended_alphabet, sorter)
    inspirations_by_alphabet = sort_into_categories(inspirations, extended_alphabet, sorter)
    developers_by_alphabet = sort_into_categories(developers, extended_alphabet, sorter)

    genres = [keyword.capitalize() for keyword in c.recommended_keywords if keyword not in c.non_game_keywords]
    genres.sort()
    games_by_genre = sort_into_categories(games, genres, lambda item, category: category.lower() in item['Keyword'])
    games_by_platform = sort_into_categories(entries, c.valid_platforms, lambda item, category: category in item.get('Platform', []), 'Unspecified')
    games_by_language = sort_into_categories(entries, c.known_languages, lambda item, category: category in item['Code language'])
    non_games_by_type = sort_into_categories(non_games, c.non_game_keywords, lambda item, category: category in item['Keyword'])

    # extract top 50 Github stars games
    top50_games = get_top50_games(games)

    # base dictionary
    base = {
        'title': 'OSGL',
        'creation-date': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M'),
        'css': ['bulma.min.css', 'osgl.min.css'],
        'js': ['osgl.js']
    }

    # copy css and js
    utils.copy_tree(os.path.join(c.web_template_path, 'css'), c.web_css_path)
    utils.copy_tree(os.path.join(c.web_template_path, 'js'), c.web_js_path)

    # copy screenshots path
    files = [file for file in os.listdir(c.screenshots_path) if file.endswith('.jpg')]
    os.makedirs(c.web_screenshots_path, exist_ok=True)
    for file in files:
        shutil.copyfile(os.path.join(c.screenshots_path, file), os.path.join(c.web_screenshots_path, file))

    # collage_image and google search console token and favicon.svg
    for file in ('collage_games.jpg', 'google1f8a3863114cbcb3.html', 'favicon.svg'):
        shutil.copyfile(os.path.join(c.web_template_path, file), os.path.join(c.web_path, file))

    # create Jinja Environment
    environment = Environment(loader=FileSystemLoader(c.web_template_path), autoescape=True)
    environment.globals['base'] = base
    environment.globals['raise'] = raise_helper
    environment.globals['is_list'] = lambda obj: isinstance(obj, list)

    # multiple times used templates
    template_categorical_index = environment.get_template('categorical_index.jinja')
    template_listing_entries = environment.get_template('listing_entries.jinja')

    # top level folder
    base['url_to'] = partial(url_to, [])

    # index.html
    base['active_nav'] = 'index'
    index = {'subtitle': make_text('Contains information about {} open source games and {} game engines/tools.'.format(len(games), len(non_games))) }
    template = environment.get_template('index.jinja')
    write(template.render(index=index), ['index.html'])

    # contribute page
    base['title'] = 'OSGL | Contributions'
    base['active_nav'] = 'contribute'
    template = environment.get_template('contribute.jinja')
    write(template.render(), ['contribute.html'])

    # statistics page in statistics folder
    base['title'] = 'OSGL | Statistics'
    base['url_to'] = partial(url_to, statistics_path)
    base['active_nav'] = 'statistics'

    # statistics preparation
    template = environment.get_template('statistics.jinja')
    # render and write statistics page
    write(template.render(data=statistics_data), statistics_index_path)

    # non-games folder
    base['title'] = 'OSGL | Game engines, frameworks, tools'
    base['url_to'] = partial(url_to, non_games_path)
    base['active_nav'] = 'frameworks'

    # non-games by type
    index = divide_in_three_columns_and_transform(non_games_by_type, entry_index)
    index['title'] = make_text('Open source game engines/frameworks/tools')
    index['subtitle'] = make_text('Index of {} game engines/frameworks/tools'.format(len(non_games)))
    index['categories'] = c.non_game_keywords
    index['category-names'] = non_game_category_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 0
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), non_games_index_path)

    # generate non-games pages
    for keyword in c.non_game_keywords:
        listing = {
            'title': non_game_category_names[keyword],
            'subtitle': make_url(non_games_index_path, 'Index'),
            'items': non_games_by_type[keyword]
        }
        write(template_listing_entries.render(listing=listing), non_games_path + ['{}.html'.format(keyword)])

    # games folder
    base['title'] = 'OSGL | Games | Alphabetical'
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
    index = divide_in_three_columns_and_transform(games_by_alphabet, entry_index)
    index['title'] = make_text('Open source games')
    index['subtitle'] = [make_text('Alphabetical index of {} games.'.format(len(games)))]
    index['categories'] = extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 20
    index['category-infos'] = {letter: make_text('{} games'.format(len(games_by_alphabet[letter]))) for letter in extended_alphabet}
    write(template_categorical_index.render(index=index), games_index_path)

    # genres
    base['title'] = 'OSGL | Games | Genres'
    base['active_nav'] = ['filter', 'genres']
    index = divide_in_three_columns_and_transform(games_by_genre, entry_index)
    index['title'] = make_text('Open source games')
    index['subtitle'] = [make_text('Index by game genre.')]
    index['categories'] = genres
    index['category-names'] = {k: make_text(k) for k in index['categories']}
    index['category-icons'] = {k: make_icon(genre_icon_map[k]) for k in index['categories'] if k in genre_icon_map}
    index['number_entries_per_category_threshold'] = 50
    index['category-infos'] = {genre: make_text('{} games'.format(len(games_by_genre[genre]))) for genre in genres}
    write(template_categorical_index.render(index=index), games_by_genres_path)

    # games by language
    base['title'] = 'OSGL | Games | Programming language'
    base['active_nav'] = ['filter', 'code language']
    index = divide_in_three_columns_and_transform(games_by_language, entry_index)
    index['title'] = 'Open source games and frameworks'
    index['subtitle'] = [make_text('Index by programming language.')]
    index['categories'] = c.known_languages
    index['category-names'] = {k:k for k in index['categories']}
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 15
    index['category-infos'] = {category: make_url(c.language_urls[category], 'Language information', css_class='is-size-7') for category in c.known_languages if category in c.language_urls}
    write(template_categorical_index.render(index=index), games_by_language_path)

    # games by platform
    base['title'] = 'OSGL | Games | Supported Platform'
    base['active_nav'] = ['filter', 'platforms']
    index = divide_in_three_columns_and_transform(games_by_platform, entry_index)
    index['title'] = 'Open source games and frameworks'
    index['subtitle'] = [make_text('Index by supported platform.')]
    index['categories'] = c.valid_platforms + ('Unspecified',)
    index['category-names'] = {k: make_text(k) for k in index['categories']}
    index['category-icons'] = {k: make_icon(platform_icon_map[k]) for k in index['categories']}
    index['number_entries_per_category_threshold'] = 15
    index['category-infos'] = {}
    index['category-infos'] = {category: make_text('{} entries'.format(len(games_by_platform[category]))) for category in index['categories']}
    write(template_categorical_index.render(index=index), games_by_platform_path)

    # for kids games
    base['title'] = 'OSGL | Games | For Kids'
    base['active_nav'] = ['filter', 'kids']
    kids_games = [game for game in games if 'for kids' in game['Keyword']]
    listing = {
        'title': 'Games for Kids',
        'subtitle': '{} games suitable for kids.'.format(len(kids_games)),
        'items': kids_games
    }
    write(template_listing_entries.render(listing=listing), games_kids_path)

    # playable in browser
    base['title'] = 'OSGL | Games | Web play'
    base['active_nav'] = ['filter', 'web']
    web_games = [game for game in games if 'Play' in game and 'Web' in game['Platform']]
    listing = {
        'title': 'Playable browser games',
        'subtitle': '{} games that can be played in your browser right away.'.format(len(web_games)),
        'items': web_games
    }
    write(template_listing_entries.render(listing=listing), games_web_path)

    # completely free games
    base['title'] = 'OSGL | Games | Free code and artwork'
    base['active_nav'] = ['filter', 'libre']
    libre_games = [game for game in games if 'content open' in game['Keyword']]
    listing = {
        'title': 'Completely free games',
        'subtitle': '{} games with open/libre code and artwork.'.format(len(libre_games)),
        'items': libre_games
    }
    write(template_listing_entries.render(listing=listing), games_libre_path)

    # top 50 github games
    base['title'] = 'OSGL | Games | GitHub Top 50'
    base['active_nav'] = ['filter', 'top50']
    # there are no other games coming afterwards, can actually number them
    for index, game in enumerate(top50_games):
        game['name'] = '{}. '.format(index+1) + game['name']
    listing = {
        'title': 'GitHub Stars Top 50',
        'subtitle': '50 highest rated (by stars on Github) playable open source games in the database', # that can be played online or downloaded
        'items': top50_games
    }
    write(template_listing_entries.render(listing=listing), games_top50_path)

    # inspirations folder
    base['title'] = 'OSGL | Inspirational games'
    base['url_to'] = partial(url_to, inspirations_path)
    base['active_nav'] = 'inspirations'

    # inspirations

    # inspirations single pages
    template_listing_inspirations = environment.get_template('listing_inspirations.jinja')
    for letter in extended_alphabet:
        listing = {
            'title': 'Inspirations ({})'.format(letter.capitalize()),
            'items': inspirations_by_alphabet[letter]
        }
        write(template_listing_inspirations.render(listing=listing), inspirations_path + ['{}.html'.format(letter.capitalize())])

    # inspirations index
    extended_alphabet_names['_'] = 'Most used'
    top_inspirations = [inspiration for inspiration in inspirations if len(inspiration['Inspired entries']) >= TOP_INSPIRATION_THRESHOLD]
    inspirations_by_alphabet['_'] = top_inspirations
    index = divide_in_three_columns_and_transform(inspirations_by_alphabet, inspiration_index)
    index['title'] = 'Inspirations'
    index['subtitle'] = make_text('Alphabetical index of {} games used as inspirations'.format(len(inspirations)))
    index['categories'] = '_' + extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 10
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), inspirations_index_path)

    # developers folder
    base['title'] = 'OSGL | Games | Developers'
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
    extended_alphabet_names['_'] = 'Most active'
    top_developers = [developer for developer in developers if len(developer['Games']) >= TOP_DEVELOPER_THRESHOLD]
    developers_by_alphabet['_'] = top_developers
    index = divide_in_three_columns_and_transform(developers_by_alphabet, developer_index)
    index['title'] = 'Open source game developers'
    index['subtitle'] = make_text('Alphabetical index of {} developers'.format(len(developers)))
    index['categories'] = '_' + extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 10
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), developers_index_path)

    # dynamic table (is in top level folder)
    base['title'] = 'OSGL | Entries | Table'
    base['url_to'] = partial(url_to, [])
    base['css'].append('simple-datatables.css')
    base['js'].append('simple-datatables.js')
    base['active_nav'] = 'table'
    template = environment.get_template('table.jinja')
    index['tags'] = make_text(', '.join(c.interesting_keywords))
    index['platforms'] = make_text(', '.join(c.valid_platforms))
    write(template.render(index=index), ['table.html'])


if __name__ == "__main__":

    start_time = time.process_time()

    # create dictionary of file hashes
    print('estimate file hashes')
    for dirpath, dirnames, filenames in os.walk(c.web_path):
        for file in filenames:
            if any(file.endswith(ext) for ext in ('.html', '.svg')):
                file = os.path.join(dirpath, file)
                text = utils.read_text(file)
                previous_files[file] = {'hash': file_hash(text), 'text': text}

    # clean the output directory
    print('clean current static website')
    utils.recreate_directory(c.web_path)

    # load entries, inspirations and developers and sort them alphabetically
    print('load entries, inspirations and developers')
    entries = osg.read_entries()
    entries.sort(key=lambda x: str.casefold(x['Title']))

    # add screenshot information
    add_screenshot_information(entries)

    inspirations = osg.read_inspirations()
    inspirations = list(inspirations.values())
    inspirations.sort(key=lambda x: str.casefold(x['Name']))
    # remove orphaned inspirations for the website creation
    inspirations = [inspiration for inspiration in inspirations if inspiration['Inspired entries']]

    developers = osg.read_developers()
    developers = list(developers.values())
    developers.sort(key=lambda x: str.casefold(x['Name']))
    # remove orphaned developers for the website creation
    developers = [developer for developer in developers if developer['Games']]

    # re-generate static website
    print('re-generate static website')
    generate(entries, inspirations, developers)

    # timing
    print('took {:.3f}s'.format(time.process_time()-start_time))