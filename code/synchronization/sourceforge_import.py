"""
Scrapes Sourceforge project sites and adds (mostly developer) information to our database.
"""

# TODO sourceforge sites that are not existing anymore but we have an archive link, also scrape

import pathlib
import json
import requests
from bs4 import BeautifulSoup
from utils import constants as c, utils, osg, osg_parse

sf_entries_file = c.code_path / 'sourceforge_entries.txt'
prefix = 'https://sourceforge.net/projects/'

# author names in SF that aren't the author names how we have them
SF_alias_list = {'Erik Johansson (aka feneur)': 'Erik Johansson', 'Itms': 'Nicolas Auvray',
                 'baris yuksel': 'Baris Yuksel',
                 'Wraitii': 'Lancelot de Ferrière', 'Simzer': 'Simon Laszlo', 'armin bajramovic': 'Armin Bajramovic',
                 'bleu tailfly': 'bleutailfly', 'dlh': 'DLH', 'Bjorn Hansen': 'Bjørn Hansen',
                 'Louens Veen': 'Lourens Veen',
                 'linley_henzell': 'Linley Henzell', 'Patrice DUHAMEL': 'Patrice Duhamel',
                 'Etienne SOBOLE': 'Etienne Sobole',
                 'L. H.    [Lubomír]': 'L. H. Lubomír', 'davidjoffe': 'David Joffe', 'EugeneLoza': 'Eugene Loza',
                 'Kenneth Gangsto': 'Kenneth Gangstø', 'Lucas GAUTHERON': 'Lucas Gautheron',
                 'Per I Mathisen': 'Per Inge Mathisen',
                 'wrtlprnft': 'Wrzlprnft', 'daniel_santos': 'Daniel Santos', 'Dark_Sylinc': 'darksylinc',
                 'Don Llopis': 'Don E. Llopis', 'dwachs': 'Dwachs', 'Pierre-Loup Griffais': 'Pierre-Loup A. Griffais',
                 'Richard Gobeille': 'Richard C. Gobeille', 'timfelgentreff': 'Tim Felgentreff',
                 'Dr. Martin Brumm': 'Martin Brumm', 'Dr. Wolf-Dieter Beelitz': 'Wolf-Dieter Beelitz'}

# authors to be ignored
SF_ignore_list = ('', 'Arianne Integration Bot')


def collect_sourceforge_entries():
    """
    Reads the entries of the database and collects all entries with sourceforge as project site
    """

    # read entries
    entries = osg.read_entries()
    print(f'{len(entries)} entries read')

    # loop over entries
    files = []
    for entry in entries:
        urls = [x for x in entry['Home'] if x.startswith(prefix)]
        if urls:
            files.append(entry['File'])

    # write to file
    print(f'{len(files)} entries with sourceforge projects')
    utils.write_text(sf_entries_file, json.dumps(files, indent=1))


def sourceforge_import():
    """
    Scraps Sourceforge project sites and adds developer information to the entries
    """

    # read entries that have sourceforge projects
    files = json.loads(utils.read_text(sf_entries_file))

    # read developer information
    all_developers = osg.read_developers()
    print(f' {len(all_developers)} developers read')
    all_developers_changed = False

    # all exceptions that happen will be eaten (but will end the execution)
    try:
        # loop over each entry with a sourceforge project
        for index, file in enumerate(files):
            print(f' process {file} ({index})')

            # read full entry
            entry = osg.read_entry(file)
            developers = entry.get('Developer', [])
            urls = [x for x in entry['Home'] if x.startswith('https://sourceforge.net/projects/')]

            # do we need to save it again
            entry_changed = False

            # for all sourceforge project urls in this entry
            for url in urls:
                print(f'  sf project {url}')

                if not url.endswith('/'):
                    print('error: sf project does not end with slash')
                    url += '/'

                # read and parse members page
                project_name = url[len(prefix):-1]
                if 'berlios' in project_name:  # berlios projects never have member pages
                    continue
                url_members = 'https://sourceforge.net/p/' + project_name + '/_members/'
                response = requests.get(url_members)
                if response.status_code != 200:
                    print(f'error: url {url_members} not accessible, status {response.status_code}')
                    raise RuntimeError()
                soup = BeautifulSoup(response.text, 'html.parser')
                authors = soup.find('div', id='content_base').find('table').find_all('tr')
                authors = [author.find_all('td') for author in authors]
                authors = [author[1].a['href'] for author in authors if len(author) == 3]
                # for every author in the list of scraped authors
                for author in authors:
                    # sometimes author already contains the full url, sometimes not
                    url_author = 'https://sourceforge.net' + author if not author.startswith('http') else author
                    # get the personal author page from sourceforge
                    response = requests.get(url_author)
                    if response.status_code != 200 and author not in ('/u/favorito/',):
                        print(f'error: url {url_author} not accessible, status {response.status_code}')
                        raise RuntimeError()
                    url_author = response.url  # could be different now (redirect)
                    if 'auth/?return_to' in url_author or response.status_code != 200:
                        # for some reason authorisation is forbidden or page was not available (happens for example for /u/kantaros)
                        author_name = author[3:-1]
                        nickname = author_name
                    else:
                        # this is the typical case
                        soup = BeautifulSoup(response.text, 'html.parser')
                        author_name = soup.h1.get_text().strip()  # lately they have a newline at the end, need to strip that
                        author_name = SF_alias_list.get(author_name, author_name)  # replace by alias if possible
                        nickname = soup.find('dl', class_='personal-data').find('dd').get_text()
                        nickname = nickname.replace('\n', '').strip()
                    nickname += '@SF'  # our indication of the platform to search for
                    author_name = author_name.strip()  # names could still have white spaces before or after

                    # some authors we ignore
                    if author_name in SF_ignore_list:
                        continue

                    # look author up in entry developers field, if not existing add
                    if author_name not in developers:
                        print(f'   dev "{author_name}" added to entry {file}')
                        entry['Developer'] = entry.get('Developer', []) + [author_name]
                        entry_changed = True
                        developers = entry.get('Developer', [])  # update developers

                    # look author and SF nickname up in developers data base
                    if author_name in all_developers:
                        # get existing developer information
                        dev = all_developers[author_name]
                        if nickname not in dev.get('Contact', []):
                            print(f' existing dev "{author_name}" added nickname ({nickname}) to developer database')
                            # check that name has not already @SF contact
                            if any(x.endswith('@SF') for x in dev.get('Contact', [])):
                                print('warning: already different SF contact existing')
                            all_developers[author_name]['Contact'] = dev.get('Contact', []) + [nickname]
                            all_developers_changed = True
                    else:
                        # new developer entry in the developers data base
                        print(f'   dev "{author_name}" ({nickname}) added to developer database')
                        all_developers[author_name] = {'Name': author_name, 'Contact': [nickname], 'Games': [entry['Title']]}
                        all_developers_changed = True

            if entry_changed:
                # save entry
                osg.write_entry(entry)
                print('  entry updated')
    except:
        raise
    finally:
        # shorten file list
        utils.write_text(sf_entries_file, json.dumps(files[index:], indent=1))

        # save entry
        osg.write_entry(entry)
        print(' entry updated')

        # maybe save all developers
        if all_developers_changed:
            # save all developers
            osg.write_developers(all_developers)
            print('developers database updated')


if __name__ == "__main__":
    # collect entries
    # collect_sourceforge_entries()

    # import information from sf
    sourceforge_import()
