"""
Imports game details from libregamewiki by scraping the website, starting from https://libregamewiki.org/Category:Games

Also parse rejected games (https://libregamewiki.org/Libregamewiki:Rejected_games_list) and maybe https://libregamewiki.org/Libregamewiki:Suggested_games

Unique left column names in the game info boxes:
['Code license', 'Code licenses', 'Developer', 'Developers', 'Engine', 'Engines', 'Genre', 'Genres', 'Libraries', 'Library', 'Media license', 'Media licenses', 'P. language', 'P. languages', 'Platforms']
"""

import os
import requests
import json
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
        if file == '_lgw.json':
            continue

        text = utils.read_text(os.path.join(import_path, file))

        # parse the html
        soup = BeautifulSoup(text, 'html.parser')
        title = soup.h1.get_text()
        print(title)
        entry = {'name': title}

        # get all external links
        links = [(x['href'], x.get_text()) for x in soup.find_all('a', href=True)]
        links = [x for x in links if x[0].startswith('http') and not x[0].startswith('https://libregamewiki.org/')]
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


def clean_lgw_content():

    # paths
    import_path = os.path.join(constants.root_path, 'tools', 'lgw-import')
    entries_file = os.path.join(import_path, '_lgw.json')
    cleaned_entries_file = os.path.join(import_path, '_lgw.cleaned.json')

    # load entries
    text = utils.read_text(entries_file)
    entries = json.loads(text)

    # rename keys
    key_replacements = (('developer', ('Developer', 'Developers')), ('code license', ('Code license', 'Code licenses')), ('engine', ('Engine', 'Engines')), ('genre', ('Genre', 'Genres')))
    for index, entry in enumerate(entries):
        for new_key, old_keys in key_replacements:
            for key in old_keys:
                if key in entry:
                    entry[new_key] = entry[key]
                    del entry[key]
                    break

        entries[index] = entry

    # check for unique field names
    unique_fields = set()
    for entry in entries:
        unique_fields.update(entry.keys())
    print('unique lgw fields: {}'.format(sorted(list(unique_fields))))

    # which fields are mandatory
    for entry in entries:
        remove_fields = [field for field in unique_fields if field not in entry]
        unique_fields -= set(remove_fields)
    print('mandatory lgw fields: {}'.format(sorted(list(unique_fields))))


if __name__ == "__main__":

    # stage one
    # download_lgw_content()

    # stage two
    # parse_lgw_content()

    # stage three
    clean_lgw_content()