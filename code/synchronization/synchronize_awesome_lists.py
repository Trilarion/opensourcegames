"""
Synchronizes with awesome lists from
"""

import re
import requests
from utils import osg, osg_rejected

# TODO Probably could fix some of the ignored cases within the awesome lists (or fix the small deviations in structure)
# TODO not all of them are awesome actually

# AWESOME_LIST = 'https://raw.githubusercontent.com/radek-sprta/awesome-game-remakes/master/README.md'
# IGNORED = ('2006rebotted', 'raw(gl)', 'fheroes2', 'FS2OPEN', 'Barbarian', 'Hexen II: Hammer of Thyrion')

AWESOME_LIST = 'https://raw.githubusercontent.com/leereilly/games/master/README.md'
IGNORED = ('Warsow',)

# two different - signs are used sometimes
matcher = re.compile(r'\[(.*)?\]\((.*?)\) [-– ]*(.*)')  # general structure: - [title](link) - description

if __name__ == "__main__":
    
    # read rejected
    rejected = osg_rejected.read_rejected_file()

    # read awesome list
    print(f'read {AWESOME_LIST}')
    r = requests.get(AWESOME_LIST, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}, timeout=20, allow_redirects=True)
    if r.status_code != requests.codes.ok:
        raise RuntimeError('Cannot download awesome list.')
    text = r.text
    text = text.split('\n##')[2:]
    entries = []
    for items in text:
        items = items.split('\n')
        category = items[0].strip()
        items = [item for item in items[1:] if item.startswith('- ') or item.startswith('* ')]
        for item in items:
            # print(item)
            # print(matcher.findall(item))
            matches = matcher.findall(item)[0]  # we know it will be exactly one
            title = matches[0]
            url = matches[1]
            description = matches[2]
            entries.append({'Title': title, 'URL': url, 'Description': description, 'Category': category})
    print(f'contains {len(entries)} entries')

    # remove those from the ignored list
    entries = [entry for entry in entries if not any(entry['Title'] == x for x in IGNORED)]

    # remove those that are in our rejected list
    rejected_titles = [x['Title'] for x in rejected]
    entries = [entry for entry in entries if entry['Title'] not in rejected_titles]
    print(f'after filtering for rejected and ignored entries {len(entries)}')

    # a bit of statistics about this awesome list
    print(f'contains {len(entries)} entries in {len(text)} categories')
    n = [0, 0]
    for entry in entries:
        if entry['URL'].startswith('https://github.com/'):
            n[0] += 1
        else:
            n[1] += 1
    print('{} links to Github, {} links not to Github'.format(*n))

    # read our database
    our_entries = osg.read_entries()
    print(f'{len(our_entries)} entries read (osgl)')

    # go through this awesome list entries one by one and compare to our list
    index = 1
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
            print(f"Unknown entry ({index}) \"{entry['Title']}\" {entry['URL']} - {entry['Category']} - {entry['Description']}")
            index += 1



