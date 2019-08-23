"""
Imports game details from libregamewiki by scraping the website, starting from https://libregamewiki.org/Category:Games

Also parse rejected games (https://libregamewiki.org/Libregamewiki:Rejected_games_list) and maybe https://libregamewiki.org/Libregamewiki:Suggested_games

Unique left column names in the game info boxes:
['Code license', 'Code licenses', 'Developer', 'Developers', 'Engine', 'Engines', 'Genre', 'Genres', 'Libraries', 'Library', 'Media license', 'Media licenses', 'P. language', 'P. languages', 'Platforms']
"""

import requests
import json
from bs4 import BeautifulSoup, NavigableString
from utils.utils import *


def key_selection_gameinfobox(a, b):
    """
    Checks which of the two elements in a is in b or none but not both
    """
    if len(a) != 2:
        raise RuntimeError()
    c = [x in b for x in a]
    if all(c):
        raise RuntimeError
    if not any(c):
        return None, None
    d = [(k, i) for (i, k) in enumerate(a) if c[i]]
    return d[0]


def extract_field_content(key, idx, info):
    """
    From a game info field.
    """
    content = info[key].get_text()
    content = content.split(',')
    content = [x.strip() for x in content]
    content = [x if not (x.endswith('[1]') or x.endswith('[2]')) else x[:-3] for x in content]  # remove trailing [1,2]
    content = [x.strip() for x in content]
    if not content:
        raise RuntimeError
    if (len(content) > 1 and idx == 0) or (len(content) == 1 and idx == 1):
        print(' warning: {} Sg./Pl. mismatch'.format(key))
    return content


if __name__ == "__main__":

    # parameters
    base_url = 'https://libregamewiki.org'
    ignored_gameinfos = ['Contribute', 'Origin', 'Release date', 'Latest release']

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

    print('current number of games in LGW {}'.format(len(games)))

    # parse games
    counter = 0
    unique_gameinfo_fields = set()
    entries = []
    for game in games:
        url = base_url + game[0]
        text = requests.get(url).text
        soup = BeautifulSoup(text, 'html.parser')
        title = soup.h1.string
        print(title)
        entry = {'name': title}

        # parse gameinfobox
        info = soup.find('div', class_='gameinfobox')
        if not info:
            print(' no gameinfobox')
        else:
            info = info.find_all('tr')
            info = [(x.th.string, x.td) for x in info if x.th and x.th.string]
            info = [x for x in info if x[0] not in ignored_gameinfos]
            info = dict(info)
            unique_gameinfo_fields.update(info.keys())

            # consume fields of gameinfobox
            # genre
            key, idx = key_selection_gameinfobox(('Genre', 'Genres'), info.keys())
            if key:
                genres = extract_field_content(key, idx, info)
                entry['genre']
                del info[key]

            # platforms
            key = 'Platforms'
            if key in info:
                platforms = extract_field_content(key, 1, info)
                # platforms = [x if x != 'Mac' else 'macOS' for x in platforms] # replace Mac with macOS
                entry['platform'] = platforms
                del info[key]

            # developer
            key, idx = key_selection_gameinfobox(('Developer', 'Developers'), info.keys())
            if key:
                entry['developer'] = extract_field_content(key, idx, info)
                del info[key]

            # code license
            key, idx = key_selection_gameinfobox(('Code license', 'Code licenses'), info.keys())
            if key:
                entry['code license'] = extract_field_content(key, idx, info)
                del info[key]

            # media license
            key, idx = key_selection_gameinfobox(('Media license', 'Media licenses'), info.keys())
            if key:
                entry['assets license'] = extract_field_content(key, idx, info)
                del info[key]

            # engine
            key, idx = key_selection_gameinfobox(('Engine', 'Engines'), info.keys())
            if key:
                entry['engine'] = extract_field_content(key, idx, info)
                del info[key]

            # library
            key, idx = key_selection_gameinfobox(('Library', 'Libraries'), info.keys())
            if key:
                entry['library'] = extract_field_content(key, idx, info)
                del info[key]

            # programming language
            key, idx = key_selection_gameinfobox(('P. language', 'P. languages'), info.keys())
            if key:
                languages = extract_field_content(key, idx, info)
                languages = [x for x in languages if x != 'HTML5'] # ignore HTML5
                entry['code language'] = languages
                del info[key]

            # unconsumed
            if info:
                print('unconsumed gameinfo keys {}'.format(info.keys()))
                raise RuntimeError()

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
        # print(entry)

        counter += 1
        if counter > 20:
            # break
            pass

    unique_gameinfo_fields = sorted(list(unique_gameinfo_fields))
    print('unique gameinfo fields: {}'.format(unique_gameinfo_fields))

    # save entries
    json_path = os.path.join(os.path.dirname(__file__), 'lgw_import.json')
    text = json.dumps(entries, indent=1)
    write_text(json_path, text)

