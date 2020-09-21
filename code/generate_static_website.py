"""
Generates the static website

Uses Jinja2 (see https://jinja.palletsprojects.com/en/2.11.x/)
"""

# TODO index.html tiles, content
# TODO index.html image
# TODO index.html only count games
# TODO Font awesome 5 (icons for OS, for Github, Gitlab and maybe others)
# TODO contribute.html tiles? content
# TODO games pages links to licenses (wikipedia)
# TODO games pages edit/contribute button
# TODO indexes: make categories bold that have a certain amount of entries!
# TODO everywhere: style URLs (Github, Wikipedia, Internet archive, SourceForge, ...)
# TODO developers pages links to games and more information, styles, block around entry, edit/contribute button
# TODO inspirations pages, add link to games and more information, styles, block around entry, edit/contribute button
# TODO navbar add is active
# TODO statistics page: better and more statistics with links where possible
# TODO meaningful information (links, license, last updated with lower precision)
# TODO singular, plural everywhere (game, entries, items)

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

games_path = 'games'
inspirations_path = 'inspirations'
developers_path = 'developers'

html5parser = html5lib.HTMLParser(strict=True)


def write(text, file):
    """

    :param text:
    :param file:
    """
    # validate text
    try:
        html5parser.parse(text)
    except Exception as e:
        utils.write_text(os.path.join(c.web_path, 'invalid.html'), text)  # for further checking with https://validator.w3.org/
        raise RuntimeError(e)
    # output file
    file = os.path.join(c.web_path, file)
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


def url_to(current, target):
    """

    :param current:
    :param target:
    :return:
    """
    # split by slash
    if current:
        current = current.split('/')
    target = target.split('/')
    # reduce by common elements
    while len(current) > 0 and len(target) > 1 and current[0] == target[0]:
        current = current[1:]
        target = target[1:]
    # add .. as often as length of current still left
    target = ['..'] * len(current) + target
    # join by slash again
    url = '/'.join(target)
    return url


def preprocess(list, key, path):
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
        item['href'] = os.path.join(path, '{}.html#{}'.format(start, anchor))


def game_index(entry):
    e = {
        'name': entry['Title'],
        'href': entry['href'],
        'anchor-id': entry['anchor-id']
    }
    tags = []
    if 'beta' in entry['State']:
        tags.append('beta')
    if osg.is_inactive(entry):
        tags.append('inactive since {}'.format(osg.extract_inactive_year(entry)))
    if tags:
        e['tags'] = ', '.join(tags)
    return e


def inspiration_index(inspiration):
    e = {
        'name': inspiration['Name'],
        'href': inspiration['href'],
        'anchor-id': inspiration['anchor-id'],
    }
    n = len(inspiration['Inspired entries'])
    if n > 1:
        e['tags'] = n
    return e


def developer_index(developer):
    e = {
        'name': developer['Name'],
        'href': developer['href'],
        'anchor-id': developer['anchor-id']
    }
    n = len(developer['Games'])
    if n > 1:
        e['tags'] = n
    return e


def add_entries_links_to_inspirations(inspirations, entries):
    entries_references = {entry['Title']:entry['href'] for entry in entries}
    for inspiration in inspirations:
        inspired_entries = inspiration['Inspired entries']
        inspired_entries = [(entries_references[entry], entry) for entry in inspired_entries]
        inspiration['Inspired entries'] = inspired_entries


def add_entries_links_to_developers(developers, entries):
    entries_references = {entry['Title']:entry['href'] for entry in entries}
    for developer in developers:
        developed_entries = developer['Games']
        developed_entries = [(entries_references[entry], entry) for entry in developed_entries]
        developer['Games'] = developed_entries


def add_inspirations_and_developers_links_to_entries(entries, inspirations, developers):
    inspirations_references = {inspiration['Name']: inspiration['href'] for inspiration in inspirations}
    developer_references = {developer['Name']: developer['href'] for developer in developers}
    for entry in entries:
        if 'Inspirations' in entry:
            entry['Inspirations'] = [(inspirations_references[inspiration.value], inspiration.value) for inspiration in entry['Inspirations']]
        if 'Developer' in entry:
            entry['Developer'] = [(developer_references[developer.value], developer.value) for developer in entry['Developer']]


def generate(entries, inspirations, developers):
    """

    :param entries:
    :param inspirations:
    :param developers:
    """

    # preprocess
    preprocess(entries, 'Title', games_path)
    preprocess(inspirations, 'Name', inspirations_path)
    preprocess(developers, 'Name', developers_path)

    # set internal links up
    add_entries_links_to_inspirations(inspirations, entries)
    add_entries_links_to_developers(developers, entries)
    add_inspirations_and_developers_links_to_entries(entries, inspirations, developers)

    # sort into categories
    games_by_alphabet = sort_into_categories(entries, extended_alphabet, lambda item, category: category == item['letter'])
    inspirations_by_alphabet = sort_into_categories(inspirations, extended_alphabet, lambda item, category: category == item['letter'])
    developers_by_alphabet = sort_into_categories(developers, extended_alphabet, lambda item, category: category == item['letter'])

    genres = [keyword.capitalize() for keyword in c.recommended_keywords]
    games_by_genre = sort_into_categories(entries, genres, lambda item, category: category.lower() in item['Keywords'])
    games_by_platform = sort_into_categories(entries, c.valid_platforms, lambda item, category: category in item.get('Platform', []), 'Unspecified')
    games_by_language = sort_into_categories(entries, c.known_languages, lambda item, category: category in item['Code language'])

    # base dictionary
    base = {
        'title': 'OSGL',
        'creation-date': datetime.datetime.utcnow()
    }

    # copy bulma css
    os.mkdir(c.web_css_path)
    shutil.copy2(os.path.join(c.web_template_path, 'bulma.min.css'), c.web_css_path)

    # create Jinja Environment
    environment = Environment(loader=FileSystemLoader(c.web_template_path), autoescape=True)
    environment.globals['base'] = base

    # multiple times used templates
    template_categorical_index = environment.get_template('categorical_index.jinja')
    template_list = environment.get_template('list.jinja')

    # top level folder
    base['url_to'] = partial(url_to, '')

    # index.html
    index = {'number_games': len(entries)}
    template = environment.get_template('index.jinja')
    write(template.render(index=index), 'index.html')

    # contribute.html
    template = environment.get_template('contribute.jinja')
    write(template.render(), 'contribute.html')

    # statistics

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
    write(template.render(data=data), os.path.join('statistics.html'))

    # games folder
    base['url_to'] = partial(url_to, games_path)

    # generate games pages
    template = environment.get_template('games_for_letter.jinja')
    for letter in extended_alphabet:
        data = {
            'title': 'Games with {}'.format(letter.capitalize()),
            'games': games_by_alphabet[letter]
        }
        write(template.render(data=data), os.path.join(games_path, '{}.html'.format(letter.capitalize())))

    # generate games index
    index = divide_in_columns(games_by_alphabet, game_index)
    index['title'] = 'Alphabetical index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), os.path.join(games_path, 'index.html'))

    # genres
    index = divide_in_columns(games_by_genre, game_index)
    index['title'] = 'Games by genre'
    index['categories'] = genres
    write(template_categorical_index.render(index=index), os.path.join(games_path, 'genres.html'))

    # games by language
    index = divide_in_columns(games_by_language, game_index)
    index['title'] = 'Games by language'
    index['categories'] = c.known_languages
    write(template_categorical_index.render(index=index), os.path.join(games_path, 'languages.html'))

    # games by platform
    index = divide_in_columns(games_by_platform, game_index)
    index['title'] = 'Games by platform'
    index['categories'] = c.valid_platforms + ('Unspecified',)
    write(template_categorical_index.render(index=index), os.path.join(games_path, 'platforms.html'))

    # inspirations folder
    base['url_to'] = partial(url_to, inspirations_path)

    # inspirations

    # inspirations index
    index = divide_in_columns(inspirations_by_alphabet, inspiration_index)
    index['title'] = 'Inspirations index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), os.path.join(inspirations_path, 'index.html'))

    # inspirations single pages
    template = environment.get_template('inspirations_for_letter.jinja')
    for letter in extended_alphabet:
        write(template.render(letter=letter, inspirations=inspirations_by_alphabet[letter]), os.path.join(inspirations_path, '{}.html'.format(letter.capitalize())))

    # developers folder
    base['url_to'] = partial(url_to, developers_path)

    # developers single pages
    template = environment.get_template('developers_for_letter.jinja')
    for letter in extended_alphabet:
        write(template.render(letter=letter, developers=developers_by_alphabet[letter]), os.path.join(developers_path, '{}.html'.format(letter.capitalize())))

    # developers index
    index = divide_in_columns(developers_by_alphabet, developer_index)
    index['title'] = 'Developers index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), os.path.join(developers_path, 'index.html'))


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