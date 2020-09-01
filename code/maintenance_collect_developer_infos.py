"""
Checks the entries and tries to detect additional developer content, by retrieving websites or logging information from
stored Git repositories.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from utils import constants as c, utils, osg, osg_github


def developer_info_lookup(name):
    for dev in developer_info:
        if name == dev['name']:
            return dev
    return None


# author names in SF that aren't the author names how we have them
SF_alias_list = {'Erik Johansson (aka feneur)': 'Erik Johansson', 'Itms': 'Nicolas Auvray',
                 'Wraitii': 'Lancelot de Ferrière', 'Simzer': 'Simon Laszlo', 'armin bajramovic': 'Armin Bajramovic'}

if __name__ == "__main__":

    # read developer info
    developer_info = osg.read_developer_info()
    osg.write_developer_info(developer_info)  # write again just to make it nice and as sanity check

    sys.exit(0)



    # assemble info
    entries = osg.assemble_infos()

    # cross-check
    osg.compare_entries_developers(entries, developer_info)

    # loop over infos
    developers = ''
    try:
        i = 0
        # active = False
        for entry in entries:

            # if entry['name'] == 'Aleph One':
            #    active = True
            # if not active:
            #    continue

            # for testing purposes
            i += 1
            if i > 40:
                break

            # print
            entry_name = '{} - {}'.format(entry['file'], entry['name'])
            print(entry_name)
            content = ''

            entry_developer = entry.get('developer', [])

            # parse home
            home = entry['home']
            # sourceforge project site
            prefix = 'https://sourceforge.net/projects/'
            url = [x for x in home if x.startswith(prefix)]
            if len(url) == 1:
                url = url[0]
                print(' sourceforge project site: {}'.format(url))
                url = 'https://sourceforge.net/p/' + url[len(prefix):] + '_members/'
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                authors = soup.find('div', id='content_base').find('table').find_all('tr')
                authors = [author.find_all('td') for author in authors]
                authors = [author[1].a['href'] for author in authors if len(author) == 3]
                for author in authors:
                    # sometimes author already contains the full url, sometimes not
                    url = 'https://sourceforge.net' + author if not author.startswith('http') else author
                    response = requests.get(url)
                    url = response.url  # could be different now
                    if 'auth/?return_to' in url:
                        # for some reason authorisation is forbidden
                        author_name = author
                        nickname = author
                    else:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        author_name = soup.h1.get_text()
                        author_name = SF_alias_list.get(author_name, author_name)  # replace by alias if possible
                        nickname = soup.find('dl', class_='personal-data').find('dd').get_text()
                        nickname = nickname.replace('\n', '').strip()
                    dev = developer_info_lookup(author_name)
                    in_devs = dev and 'contact' in dev and nickname + '@SF' in dev['contact']
                    in_entry = author_name in entry_developer
                    if in_devs and in_entry:
                        continue  # already existing in entry and devs
                    content += ' {} : {}@SF'.format(author_name, nickname)
                    if not in_devs:
                        content += ' (not in devs)'
                    if not in_entry:
                        content += ' (not in entry)'
                    content += '\n'

            # parse source repository
            repos = entry.get('code repository', [])

            # Github
            urls = [x for x in repos if x.startswith('https://github.com/')]
            urls = []
            for url in urls:
                print(' github repo: {}'.format(url))
                github_info = osg_github.retrieve_repo_info(url)
                for contributor in github_info['contributors']:
                    name = contributor.name
                    dev = developer_info_lookup(name)
                    in_devs = dev and 'contact' in dev and contributor.login + '@GH' in dev['contact']
                    in_entry = name in entry_developer
                    if in_devs and in_entry:
                        continue  # already existing in entry and devs
                    content += ' {}: {}@GH'.format(name, contributor.login)
                    if contributor.blog:
                        content += ' url: {}'.format(contributor.blog)
                    if not in_devs:
                        content += ' (not in devs)'
                    if not in_entry:
                        content += ' (not in entry)'
                    content += '\n'

            if content:
                developers += '{}\n\n{}\n'.format(entry_name, content)

    except RuntimeError as e:
        raise e
        # pass
    finally:
        # store developer info
        utils.write_text(os.path.join(c.root_path, 'collected_developer_info.txt'), developers)
