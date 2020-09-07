"""
Checks the entries and tries to detect additional developer content, by retrieving websites or logging information from
stored Git repositories.
"""

import os
import sys
import requests
from utils import osg, osg_ui
from bs4 import BeautifulSoup
from utils import constants as c, utils, osg, osg_github


# author names in SF that aren't the author names how we have them
SF_alias_list = {'Erik Johansson (aka feneur)': 'Erik Johansson', 'Itms': 'Nicolas Auvray',
                 'Wraitii': 'Lancelot de Ferrière', 'Simzer': 'Simon Laszlo', 'armin bajramovic': 'Armin Bajramovic'}

def test():
    # loop over infos
    developers = ''
    try:
        i = 0
        # active = False
        for entry in entries:

            # if entry['Name'] == 'Aleph One':
            #    active = True
            # if not active:
            #    continue

            # for testing purposes
            i += 1
            if i > 40:
                break

            # print
            entry_name = '{} - {}'.format(entry['file'], entry['Name'])
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



class DevelopersMaintainer:

    def __init__(self):
        self.developers = None
        self.entries = None

    def read_developer(self):
        self.developers = osg.read_developers()
        print('{} developers read'.format(len(self.developers)))

    def write_developer(self):
        if not self.developers:
            print('developers not yet loaded')
            return
        osg.write_developers(self.developers)
        print('developers written')

    def check_for_duplicates(self):
        if not self.developers:
            print('developers not yet loaded')
            return
        developer_names = list(self.developers.keys())
        for index, name in enumerate(developer_names):
            for other_name in developer_names[index + 1:]:
                if osg.name_similarity(name, other_name) > 0.8:
                    print(' {} - {} is similar'.format(name, other_name))
        print('duplicates checked')

    def check_for_orphans(self):
        if not self.developers:
            print('developers not yet loaded')
            return
        for dev in self.developers.values():
            if not dev['Games']:
                print(' {} has no games'.format(dev['Name']))
        print('orphanes checked')
        
    def check_for_missing_developers_in_entries(self):
        if not self.developers:
            print('developer not yet loaded')
            return
        if not self.entries:
            print('entries not yet loaded')
            return
        for dev in self.developers.values():
            dev_name = dev['Name']
            for entry_name in dev['Games']:
                x = [x for x in self.entries if x['Title'] == entry_name]
                assert len(x) <= 1
                if not x:
                    print('Entry "{}" listed as game of developer "{}" but this entry does not exist'.format(entry_name, dev_name))
                else:
                    entry = x[0]
                    if 'Developer' not in entry or dev_name not in entry['Developer']:
                        print('Entry "{}" listed in developer "{}" but not listed in that entry'.format(entry_name, dev_name))
        print('missed developer checked')

    def update_developers_from_entries(self):
        if not self.developers:
            print('developer not yet loaded')
            return
        if not self.entries:
            print('entries not yet loaded')
            return
        # loop over all developers and delete all games
        for dev in self.developers.values():
            dev['Games'] = []
        # loop over all entries and add this game to all developers of this game
        for entry in self.entries:
            entry_name = entry['Title']
            entry_devs = entry.get('Developer', [])
            for entry_dev in entry_devs:
                entry_dev = entry_dev.value  # ignored the comment
                if entry_dev in self.developers:
                    self.developers[entry_dev]['Games'].append(entry_name)
                else:
                    # completely new developer
                    self.developers[entry_dev] = {'Name': entry_dev, 'Games': entry_name}
        print('developers updated')

    def read_entries(self):
        self.entries = osg.read_entries()
        print('{} entries read'.format(len(self.entries)))


if __name__ == "__main__":

    m = DevelopersMaintainer()

    actions = {
        'Read developers': m.read_developer,
        'Write developers': m.write_developer,
        'Check for duplicates': m.check_for_duplicates,
        'Check for orphans': m.check_for_orphans,
        'Check for games in developers not listed': m.check_for_missing_developers_in_entries,
        'Update developers from entries': m.update_developers_from_entries,
        'Read entries': m.read_entries
    }

    osg_ui.run_simple_button_app('Maintenance developer', actions)