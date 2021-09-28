"""
Synchronizes with awesome lists from
"""

import re
import requests
from utils import osg, osg_rejected

AWESOME_LIST = 'https://raw.githubusercontent.com/radek-sprta/awesome-game-remakes/master/README.md'
# Probably could fix them within the awesome lists
IGNORED = ('2006rebotted', 'raw(gl)', 'fheroes2', 'FS2OPEN', 'Barbarian', 'Hexen II: Hammer of Thyrion')

matcher = re.compile(r'\[(.*)?\]\((.*?)\) - (.*)')  # general structure: - [title](link) - description

if __name__ == "__main__":
    
    # read rejected
    rejected = osg_rejected.read_rejected_file()

    # read awesome list
    print('read {}'.format(AWESOME_LIST))
    r = requests.get(AWESOME_LIST, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}, timeout=20, allow_redirects=True)
    if r.status_code != requests.codes.ok:
        raise RuntimeError('Cannot download awesome list.')
    text = r.text
    text = text.split('\n##')[2:]
    entries = []
    for items in text:
        items = items.split('\n')
        category = items[0].strip()
        items = [item for item in items[1:] if item.startswith('-')]
        for item in items:
            matches = matcher.findall(item)[0]  # we know it will be exactly one
            title = matches[0]
            url = matches[1]
            description = matches[2]
            entries.append({'Title': title, 'URL': url, 'Description': description, 'Category': category})

    # remove those from the ignored list
    entries = [entry for entry in entries if not any(entry['Title'] == x for x in IGNORED)]

    # remove those that are in our rejected list
    rejected_titles = [x['Title'] for x in rejected]
    entries = [entry for entry in entries if entry['Title'] not in rejected_titles]
    print('after filtering for rejected entries {}'.format(len(entries)))

    # a bit of statistics about this awesome list
    print('contains {} entries in {} categories'.format(len(entries), len(text)))
    n = [0, 0]
    for entry in entries:
        if entry['URL'].startswith('https://github.com/'):
            n[0] += 1
        else:
            n[1] += 1
    print('{} links to Github, {} links not to Github'.format(*n))

    # read our database
    our_entries = osg.read_entries()
    print('{} entries read (osgl)'.format(len(our_entries)))

    # go through this awesome list entries one by one and compare to our list
    for entry in entries:
        title = entry['Title']
        url = entry['URL']
        # go through our entries
        similar_entries = []
        for our_entry in our_entries:
            title_equal = title == our_entry['Title']
            url_present = any(url in x for x in our_entry['Home']) or any(url in x for x in our_entry.get('Code repository', []))
            if title_equal or url_present:
                similar_entries.append(our_entry)
        if not similar_entries:
            print('Unknown entry "{}" {} - {} - {}'.format(entry['Title'], entry['URL'], entry['Category'], entry['Description']))



