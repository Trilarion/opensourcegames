"""
Generates the static website

Uses Jinja2 (see https://jinja.palletsprojects.com/en/2.11.x/)
"""

import os
import shutil
import math
import datetime
from utils import osg, constants as c, utils
from jinja2 import Environment, FileSystemLoader

alphabet = 'abcdefghijklmnopqrstuvwxyz'
extended_alphabet = '0' + alphabet

def write(text, file):
    """

    :param text:
    :param file:
    """
    file = os.path.join(c.web_path, file)
    containing_dir = os.path.dirname(file)
    if not os.path.isdir(containing_dir):
        os.mkdir(containing_dir)
    utils.write_text(file, text)


def sort_into_categories(list, categories, fit, unknown_category_name):
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

def sort_by_alphabet(list, key):
    """

    :param list:
    :param key:
    :return:
    """
    return sort_into_categories(list, alphabet, lambda item, category: item[key].lower().startswith(category), '0')

def divide_in_columns(categorized_lists, key):
    """

    :param categorized_lists:
    :param key:
    :return:
    """
    number_entries = {category: len(categorized_lists[category]) for category in categorized_lists.keys()}
    entries = {}
    for category in categorized_lists.keys():
        e = categorized_lists[category]
        e = [e[key] for e in e]
        # divide in three equal lists
        n = len(e)
        n1 = math.ceil(n/3)
        n2 = math.ceil(2*n/3)
        e = [e[:n1], e[n1:n2], e[n2:]]
        entries[category] = e
    return {'number_entries': number_entries, 'entries': entries}


def generate(entries, inspirations, developers):
    """

    :param entries:
    :param inspirations:
    :param developers:
    """

    # add anchor ref () to every entry
    for entry in entries:
        entry['title-anchor'] = osg.canonical_entry_name(entry['Title'])

    # base dictionary
    base = {
        'title': 'OSGL',
        'paths': {
            'css': 'css/bulma.min.css',
            'index': 'index.html',
            'index-games': 'games/index.html',
            'index-developers': 'developers/index.html',
            'index-inspirations': 'inspirations/index.html',
            'index-statistics': 'index-statistics'
        },
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

    # index.html
    index = {'number_games': len(entries)}  # TODO only count games
    template = environment.get_template('index.jinja')
    write(template.render(index=index), 'index.html')

    # generate games pages
    games_by_alphabet = sort_by_alphabet(entries, 'Title')
    template = environment.get_template('games_for_letter.jinja')
    for letter in extended_alphabet:
        write(template.render(letter=letter, games=games_by_alphabet[letter]), os.path.join('games', '{}.html'.format(letter.capitalize())))

    # generate games index
    index = divide_in_columns(games_by_alphabet, 'Title')
    index['title'] = 'Games index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), os.path.join('games', 'index.html'))

    ## inspirations
    inspirations_by_alphabet = sort_by_alphabet(inspirations, 'Name')

    # inspirations index
    index = divide_in_columns(inspirations_by_alphabet, 'Name')
    index['title'] = 'Inspirations index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), os.path.join('inspirations', 'index.html'))

    # inspirations single pages
    template = environment.get_template('inspirations_for_letter.jinja')
    for letter in extended_alphabet:
        write(template.render(letter=letter, inspirations=inspirations_by_alphabet[letter]), os.path.join('inspirations', '{}.html'.format(letter.capitalize())))

    ## developers

    # developers single pages
    developers_by_alphabet = sort_by_alphabet(developers, 'Name')
    template = environment.get_template('developers_for_letter.jinja')
    for letter in extended_alphabet:
        write(template.render(letter=letter, developers=developers_by_alphabet[letter]), os.path.join('developers', '{}.html'.format(letter.capitalize())))

    # developers index
    index = divide_in_columns(developers_by_alphabet, 'Name')
    index['title'] = 'Developers index'
    index['categories'] = extended_alphabet
    write(template_categorical_index.render(index=index), os.path.join('developers', 'index.html'))

    ## genres
    genres = c.recommended_keywords
    games_by_genre = sort_into_categories(entries, genres, lambda item, category: category in item['Keywords'], None)
    index = divide_in_columns(games_by_genre, 'Title')
    index['title'] = 'Games by genre'
    index['categories'] = genres
    write(template_categorical_index.render(index=index), os.path.join('games', 'genres.html'))

    ## games by language TODO make categories bold that have a certain amount of entries!
    languages = c.known_languages
    games_by_language = sort_into_categories(entries, languages, lambda item, category: category in item['Code language'], None)
    index = divide_in_columns(games_by_language, 'Title')
    index['title'] = 'Games by language'
    index['categories'] = languages  # it's fine if they get capitalized, because they are already capitalized
    write(template_categorical_index.render(index=index), os.path.join('games', 'languages.html'))

    ## games by platform
    platforms = c.valid_platforms
    games_by_platform = sort_into_categories(entries, platforms, lambda item, category: category in item.get('Platform', []), 'Unspecified')
    index = divide_in_columns(games_by_platform, 'Title')
    index['title'] = 'Games by platform'
    index['categories'] = platforms  # TODO (do not capitalize automatically)
    write(template_categorical_index.render(index=index), os.path.join('games', 'platforms.html'))

    ## statistics

    # index
    template = environment.get_template('statistics_index.jinja')
    write(template.render(), os.path.join('statistics', 'index.html'))

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
    data = {
        'title': 'Build system',
        'items': ['{} ({})'.format(*item) for item in unique_build_systems]
    }
    write(template_list.render(data=data), os.path.join('statistics', 'build-systems.html'))



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