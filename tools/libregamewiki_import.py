"""
Imports game details from libregamewiki by scraping the website, starting from https://libregamewiki.org/Category:Games

Also parse rejected games (https://libregamewiki.org/Libregamewiki:Rejected_games_list) and maybe https://libregamewiki.org/Libregamewiki:Suggested_games

Unique left column names in the game info boxes:
['Code license', 'Code licenses', 'Developer', 'Developers', 'Engine', 'Engines', 'Genre', 'Genres', 'Libraries', 'Library', 'Media license', 'Media licenses', 'P. language', 'P. languages', 'Platforms']

TODO there are games on LGW which are not part of the Games category but part of XXX-Games sub-categories, find them
"""

import os
import requests
import json
import re
from bs4 import BeautifulSoup
from utils import constants, utils, osg


def download_lgw_content():
    """

    :return:
    """

    # parameters
    base_url = 'https://libregamewiki.org'
    destination_path = os.path.join(constants.root_path, 'tools', 'lgw-import')
    utils.recreate_directory(destination_path)

    # read and process the base url (get all games and categories)
    url = base_url + '/Category:Games'
    games = []
    while True:
        text = requests.get(url).text
        soup = BeautifulSoup(text, 'html.parser')
        #categories = soup.find('div', id='mw-subcategories').find_all('li')
        #categories = [(x.a['href'], x.a.string) for x in categories]

        # game pages
        pages = soup.find('div', id='mw-pages').find_all('li')
        games.extend(((x.a['href'], x.a.string) for x in pages))

        # next page
        next_page = soup.find('a', string='next page')
        if not next_page:
            break
        url = base_url + next_page['href']

    # remove all those that start with user
    games = [game for game in games if not any(game[1].startswith(x) for x in ('User:', 'Template:', 'Bullet'))]

    print('current number of games in LGW {}'.format(len(games)))

    for game in games:
        print(game[1])
        url = base_url + game[0]
        destination_file = os.path.join(destination_path, osg.canonical_game_name(game[0][1:]) + '.html')

        text = requests.get(url).text
        utils.write_text(destination_file, text)


def parse_lgw_content():

    # paths
    import_path = os.path.join(constants.root_path, 'tools', 'lgw-import')
    entries_file = os.path.join(import_path, '_lgw.json')

    # iterate over all imported files
    files = os.listdir(import_path)
    entries = []
    for file in files:
        if file.startswith('_lgw'):
            continue

        text = utils.read_text(os.path.join(import_path, file))

        # parse the html
        soup = BeautifulSoup(text, 'html.parser')
        title = soup.h1.get_text()
        print(title)
        entry = {'name': title}

        # get all external links
        ignored_external_links = ('libregamewiki.org', 'freegamedev.net', 'freegamer.blogspot.com', 'opengameart.org', 'gnu.org', 'creativecommons.org', 'freesound.org', 'freecode.com', 'freenode.net')
        links = [(x['href'], x.get_text()) for x in soup.find_all('a', href=True)]
        links = [x for x in links if x[0].startswith('http') and not any([y in x[0] for y in ignored_external_links])]
        entry['external links'] = links

        # get meta description
        description = soup.find('meta', attrs={"name":"description"})
        entry['description'] = description['content']

        # parse gameinfobox
        infos = soup.find('div', class_='gameinfobox')
        if not infos:
            print(' no gameinfobox')
        else:
            infos = infos.find_all('tr')
            for x in infos:
                if x.th and x.td:
                    # row with header
                    key = x.th.get_text()
                    content = x.td.get_text()
                    content = content.split(',')
                    content = [x.strip() for x in content]
                    entry[key] = content
                if not x.th and x.td:
                    # row without header: contribute section
                    x = x.find_all('li')
                    x = [(x.a.string, x.a['href']) for x in x if x.a]
                    for key, content in x:
                        entry[key] = content

        # parse "for available as package in"
        tables = soup.find_all('table', class_='wikitable')
        tables = [table for table in tables if table.caption and table.caption.string.startswith('Available as package')]
        if len(tables) > 0:
            if len(tables) > 1:
                raise RuntimeError()
            table = tables[0]
            packages = table.find_all('tr')
            packages = [x.td.a['href'] for x in packages]
            entry['linux-packages'] = packages

        # categories
        categories = soup.find_all('div', id='mw-normal-catlinks')
        if not categories:
            print(' no categories')
            categories = []
        else:
            if len(categories) > 1:
                raise RuntimeError()
            categories = categories[0]
            categories = categories.find_all('li')
            categories = [x.a.string for x in categories]
            if 'Games' not in categories:
                print(' "Games" not in categories')
            else:
                categories.remove('Games') # should be there
            # strip games at the end
            phrase = ' games'
            categories = [x[:-len(phrase)] if x.endswith(phrase) else x for x in categories]
            ignored_categories = ['Articles lacking reference', 'Stubs']
            categories = [x for x in categories if x not in ignored_categories]
        entry['categories'] = categories

        entries.append(entry)


    # save entries
    text = json.dumps(entries, indent=1)
    utils.write_text(entries_file, text)


def replace_content(entries, fields, replacement, search):
    if not isinstance(fields, tuple):
        fields = (fields, )
    for index, entry in enumerate(entries):
        for field in fields:
            if field in entry:
                content = entry[field]
                if not isinstance(content, list):
                    content = [content]
                entry[field] = [replacement if x in search else x for x in content]
        entries[index] = entry
    return entries


def ignore_content(entries, fields, ignored):
    if not isinstance(fields, tuple):
        fields = (fields, )
    for index, entry in enumerate(entries):
        for field in fields:
            if field in entry:
                content = entry[field]
                if not isinstance(content, list):
                    content = [content]
                content = [x for x in content if x not in ignored]
                if content:
                    entry[field] = content
                else:
                    del entry[field]
        entries[index] = entry
    return entries

def remove_prefix_suffix(entries, fields, prefixes, suffixes):
    if not isinstance(fields, tuple):
        fields = (fields, )
    for index, entry in enumerate(entries):
        for field in fields:
            if field in entry:
                content = entry[field]
                if not isinstance(content, list):
                    content = [content]
                for prefix in prefixes:
                    content = [x[len(prefix):] if x.startswith(prefix) else x for x in content]
                for sufix in suffixes:
                    content = [x[:-len(sufix)] if x.endswith(sufix) else x for x in content]
                content = [x.strip() for x in content]
                entry[field] = content
        entries[index] = entry
    return entries


def lower_case_content(entries, field):
    for index, entry in enumerate(entries):
        if field in entry:
            content = entry[field]
            if not isinstance(content, list):
                content = [content]
            entry[field] = [x.casefold() for x in content]
            entries[index] = entry
    return entries


def remove_parenthized_content(entries, fields):
    if not isinstance(fields, tuple):
        fields = (fields, )
    for index, entry in enumerate(entries):
        for field in fields:
            if field in entry:
                content = entry[field]
                if not isinstance(content, list):
                    content = [content]
                content = [re.sub(r'\([^)]*\)', '', c) for c in content] # remove parentheses content
                content = [x.strip() for x in content]
                content = list(set(content))
                entry[field] = content
        entries[index] = entry
    return entries


def ignore_nonnumbers(entries, fields):
    if not isinstance(fields, tuple):
        fields = (fields, )
    for index, entry in enumerate(entries):
        for field in fields:
            if field in entry:
                content = entry[field]
                if not isinstance(content, list):
                    content = [content]
                content = [x for x in content if x.isdigit()]
                entry[field] = content
        entries[index] = entry
    return entries


def clean_lgw_content():

    # paths
    import_path = os.path.join(constants.root_path, 'tools', 'lgw-import')
    entries_file = os.path.join(import_path, '_lgw.json')
    cleaned_entries_file = os.path.join(import_path, '_lgw.cleaned.json')

    # load entries
    text = utils.read_text(entries_file)
    entries = json.loads(text)

    # rename keys
    key_replacements = (('developer', ('Developer', 'Developers')), ('code license', ('Code license', 'Code licenses')), ('engine', ('Engine', 'Engines')), ('genre', ('Genre', 'Genres')),
                        ('library', ('Library', 'Libraries')), ('assets license', ('Media license', 'Media licenses')), ('code language', ('P. language', 'P. languages')), ('home', ('Homepage',)),
                        ('platform', ('Platforms', )), ('tracker', ('Bug/Feature Tracker', )), ('repo', ('Source Code', )), ('forum', ('Forum', )), ('chat', ('Chat', )), ('origin', ('Origin', )),
                        ('dev home', ('Development Project', )), ('last active', ('Release date', )))
    for index, entry in enumerate(entries):
        for new_key, old_keys in key_replacements:
            for key in old_keys:
                if key in entry:
                    entry[new_key] = entry[key]
                    del entry[key]
                    break
        entries[index] = entry

    # ignore keys
    ignored_keys = ('origin', 'Latest\xa0release')
    for index, entry in enumerate(entries):
        for key in ignored_keys:
            if key in entry:
                del entry[key]
        entries[index] = entry

    # check for unique field names
    unique_fields = set()
    for entry in entries:
        unique_fields.update(entry.keys())
    print('unique lgw fields: {}'.format(sorted(list(unique_fields))))

    # which fields are mandatory
    mandatory_fields = unique_fields.copy()
    for entry in entries:
        remove_fields = [field for field in mandatory_fields if field not in entry]
        mandatory_fields -= set(remove_fields)
    print('mandatory lgw fields: {}'.format(sorted(list(mandatory_fields))))

    # statistics before
    print('field contents before')
    fields = sorted(list(unique_fields - set(('description', 'external links', 'dev home', 'forum', 'home', 'linux-packages', 'developer', 'chat', 'tracker', 'Latest release', 'name', 'repo', 'Release date', 'categories'))))
    for field in fields:
        content = [entry[field] for entry in entries if field in entry]
        # flatten
        flat_content = []
        for c in content:
            if isinstance(c, list):
                flat_content.extend(c)
            else:
                flat_content.append(c)
        statistics = utils.unique_elements_and_occurrences(flat_content)
        print('{}: {}'.format(field, ', '.join(statistics)))

    # content replacements
    entries = remove_parenthized_content(entries, ('assets license', 'code language', 'code license', 'engine', 'genre', 'last active', 'library'))
    entries = remove_prefix_suffix(entries, ('code license', 'assets license'), ('"', 'GNU', ), ('"', '[3]', '[2]', '[1]', 'only'))
    entries = replace_content(entries, ('code license', 'assets license'), 'GPL', ('General Public License', ))
    entries = replace_content(entries, ('code license', 'assets license'), 'GPL-2.0', ('GPLv2', )) # for LGW GPLv2 would be the correct writing
    entries = replace_content(entries, ('code license', 'assets license'), 'GPL-2', ('GPLv2', 'GPL v2', 'GPL version 2.0', 'GPL 2.0', 'General Public License v2', 'GPL version 2', 'Gplv2', 'GPL 2'))
    entries = replace_content(entries, ('code license', 'assets license'), 'GPL-2', ('GPL v2 or later', 'GPL 2+', 'GPL v2+', 'GPL version 2 or later'))
    entries = replace_content(entries, ('code license', 'assets license'), 'GPL-3.0', ('GPLv3', )) # for LGW GPLv3 would be the correct writing
    entries = replace_content(entries, ('code license', 'assets license'), 'GPL-3', ('GPL v3', 'GNU GPL v3', 'GPL 3'))
    entries = replace_content(entries, ('code license', 'assets license'), 'GPL-3', ('GPL v3+', 'GPL v.3 or later', 'GPL v3 or later'))
    entries = replace_content(entries, ('code license', 'assets license'), 'Public domain', ('public domain', 'Public Domain'))
    entries = replace_content(entries, ('code license', 'assets license'), 'zlib', ('zlib/libpng license', 'Zlib License'))
    entries = replace_content(entries, ('code license', 'assets license'), 'BSD', ('Original BSD License', ))
    entries = replace_content(entries, ('code license', 'assets license'), 'CC-BY-SA-3.0', ('Creative Commons Attribution-ShareAlike 3.0 Unported License', 'CC-BY-SA 3.0', 'CC BY-SA 3.0'))
    entries = replace_content(entries, ('code license', 'assets license'), 'CC-BY-SA', ('CC BY-SA',))
    entries = replace_content(entries, ('code license', 'assets license'), 'MIT', ('MIT License', 'MIT"'))
    entries = replace_content(entries, 'platform', 'macOS', ('Mac', ))
    entries = remove_prefix_suffix(entries, ('code language', 'developer'), (), ('[3]', '[2]', '[1]'))
    entries = ignore_content(entries, 'code language', ('HTML5', 'HTML', 'English', 'XML', 'WML'))
    entries = replace_content(entries, 'code language', 'Lua', ('lua', 'LUA'))
    entries = remove_prefix_suffix(entries, 'genre', (), ('game', 'games'))
    entries = lower_case_content(entries, 'genre')
    entries = replace_content(entries, 'genre', 'platform', ('platformer', ))
    entries = replace_content(entries, 'genre', 'role playing', ('rpg', ))
    entries = replace_content(entries, 'genre', 'first person, shooter', ('fps', ))
    entries = replace_content(entries, 'genre', 'real time, strategy', ('rts',))
    entries = replace_content(entries, 'genre', 'turn based, strategy', ('tbs',))
    entries = ignore_content(entries, 'categories', ('GPL', 'C++', 'C', 'ECMAScript', 'Python', 'Java', 'CC BY-SA', 'Lua', 'LGPL', 'CC-BY', 'BSD', 'MIT', 'Qt', 'SDL', 'OpenGL', 'Pygame', 'PD', 'GLUT', 'Haskell', 'Allegro', 'Ruby', 'Zlib/libpng', 'OpenAL', 'Perl', 'Free Pascal', 'LÖVE', 'HTML5', 'Id Tech 1'))
    entries = replace_content(entries, 'library', 'pygame', ('Pygame', ))
    entries = replace_content(entries, 'library', 'Qt', ('QT', ))
    entries = ignore_content(entries, 'library', ('C++', 'Lua', 'Mozilla Firefox'))
    entries = ignore_nonnumbers(entries, 'last active')
    entries = ignore_content(entries, 'last active', ('2019', ))
    entries = ignore_content(entries, 'platform', ('DOS', ))


    # list for every unique field
    print('\nfield contents after')
    fields = sorted(list(unique_fields - set(('description', 'external links', 'dev home', 'forum', 'home', 'linux-packages', 'developer', 'chat', 'tracker', 'Latest release', 'name', 'repo', 'Release date', 'categories'))))
    for field in fields:
        content = [entry[field] for entry in entries if field in entry]
        # flatten
        flat_content = []
        for c in content:
            if isinstance(c, list):
                flat_content.extend(c)
            else:
                flat_content.append(c)
        statistics = utils.unique_elements_and_occurrences(flat_content)
        print('{}: {}'.format(field, ', '.join(statistics)))

    # save entries
    text = json.dumps(entries, indent=1)
    utils.write_text(cleaned_entries_file, text)


if __name__ == "__main__":

    # stage one
    # download_lgw_content()

    # stage two
    # parse_lgw_content()

    # stage three
    clean_lgw_content()