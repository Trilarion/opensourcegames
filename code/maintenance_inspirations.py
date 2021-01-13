"""
Maintenance of inspirations.md and synchronization with the inspirations in the entries.
"""

# TODO search fandom
# TODO which inspirations have wikipedia entries with open source games category by aren't included

import time
from utils import osg, osg_ui, osg_wikipedia, constants as c

valid_duplicates = ('Age of Empires', 'ARMA', 'Catacomb', 'Civilization', 'Company of Heroes', 'Descent', 'Duke Nukem', 'Dungeon Keeper',
                    'Final Fantasy', 'Heroes of Might and Magic', 'Jazz Jackrabbit', 'Marathon', 'Master of Orion', 'Quake',
                    'RollerCoaster Tycoon', 'Star Wars Jedi Knight', 'The Settlers', 'Ultima', 'Ship Simulator', 'Prince of Persia',
                    'Panzer General', 'LBreakout', 'Jagged Alliance')


class InspirationMaintainer:

    def __init__(self):
        self.inspirations = None
        self.entries = None

    def read_inspirations(self):
        self.inspirations = osg.read_inspirations()
        print('{} inspirations read'.format(len(self.inspirations)))

    def write_inspirations(self):
        if not self.inspirations:
            print('inspirations not yet loaded')
            return
        osg.write_inspirations(self.inspirations)
        print('inspirations written')

    def check_for_duplicates(self):
        if not self.inspirations:
            print('inspirations not yet loaded')
            return
        start_time = time.process_time()
        inspiration_names = list(self.inspirations.keys())
        for index, name in enumerate(inspiration_names):
            for other_name in inspiration_names[index + 1:]:
                if any((name.startswith(x) and other_name.startswith(x) for x in valid_duplicates)):
                    continue
                if osg.name_similarity(str.casefold(name), str.casefold(other_name)) > 0.9:
                    print(' {} - {} is similar'.format(name, other_name))
        print('duplicates checked took {:.1f}s'.format(time.process_time()-start_time))

    def check_for_orphans(self):
        if not self.inspirations:
            print('inspirations not yet loaded')
            return
        for inspiration in self.inspirations.values():
            if not inspiration['Inspired entries']:
                print(' {} has no inspired entries'.format(inspiration['Name']))
        print('orphanes checked')

    def check_for_missing_inspirations_in_entries(self):
        if not self.inspirations:
            print('inspirations not yet loaded')
            return
        if not self.entries:
            print('entries not yet loaded')
            return
        for inspiration in self.inspirations.values():
            inspiration_name = inspiration['Name']
            for entry_name in inspiration['Inspired entries']:
                x = [x for x in self.entries if x['Title'] == entry_name]
                assert len(x) <= 1
                if not x:
                    print('Entry "{}" listed in inspiration "{}" but this entry does not exist'.format(entry_name, inspiration_name))
                else:
                    entry = x[0]
                    if 'Inspiration' not in entry or inspiration_name not in entry['Inspiration']:
                        print('Entry "{}" listed in inspiration "{}" but not listed in this entry'.format(entry_name, inspiration_name))
        print('missed inspirations checked')

    def check_for_wikipedia_links(self):
        if not self.inspirations:
            print('inspirations not yet loaded')
            return
        for inspiration in self.inspirations.values():
            if 'Included' in inspiration:
                continue
            if 'Media' in inspiration and any(('https://en.wikipedia.org/wiki/' in x for x in inspiration['Media'])):
                continue
            name = inspiration['Name']
            # search in wikipedia
            results = osg_wikipedia.search(inspiration['Name'])

            # throw out all (disambiguation) pages
            results = [r for r in results if not any(x in r for x in ('disambiguation', 'film'))]

            # throw out those too dissimilar
            results = [r for r in results if osg.name_similarity(str.casefold(inspiration['Name']), str.casefold(r)) > 0.6]

            # get pages for the remaining
            pages = osg_wikipedia.pages(results)

            # throw out those that are no video games
            pages = [page for page in pages if any('video games' in category for category in page.categories)]

            # sort by similarity to title and only keep highest
            pages.sort(key=lambda page: osg.name_similarity(str.casefold(name), str.casefold(page.title)))
            pages = pages[:min(1, len(pages))]

            # if there is still one left, use it
            if pages:
                url = pages[0].url
                inspiration['Media'] = inspiration.get('Media', []) + [url]
                print('{} : {}'.format(name, url))

    def update_included_entries(self):
        if not self.inspirations:
            print('inspirations not yet loaded')
            return
        if not self.entries:
            print('entries not yet loaded')
            return
        # get all entry names
        entry_names = [entry['Title'] for entry in self.entries]
        # loop over all inspirations
        for inspiration in self.inspirations.values():
            name = inspiration['Name']
            included = name in entry_names and name not in inspiration['Inspired entries']
            if included:
                if 'Included' not in inspiration:
                    print('{} is included but was not marked as such'.format(name))
                for field in c.optional_inspiration_fields:
                    if field in inspiration:
                        del inspiration[field]
                inspiration['Included'] = 'Yes'
            elif 'Included' in inspiration:
                print('{} was marked as included but is not anymore'.format(name))
                del inspiration['Included']

    def update_inspired_entries(self):
        if not self.inspirations:
            print('inspirations not yet loaded')
            return
        if not self.entries:
            print('entries not yet loaded')
            return
        # loop over all inspirations and delete inspired entries
        for inspiration in self.inspirations.values():
            inspiration['Inspired entries'] = []
        # loop over all entries and add to inspirations of entry
        for entry in self.entries:
            entry_name = entry['Title']
            for inspiration in entry.get('Inspiration', []):
                inspiration = inspiration.value
                if inspiration in self.inspirations:
                    self.inspirations[inspiration]['Inspired entries'].append(entry_name)
                else:
                    self.inspirations[inspiration] = {'Name': inspiration, 'Inspired entries': [entry_name]}
        print('inspired entries updated')

    def read_entries(self):
        self.entries = osg.read_entries()
        print('{} entries read'.format(len(self.entries)))


if __name__ == "__main__":

    m = InspirationMaintainer()

    actions = {
        'Read inspirations': m.read_inspirations,
        'Write inspirations': m.write_inspirations,
        'Check for duplicates': m.check_for_duplicates,
        'Check for orphans': m.check_for_orphans,
        'Check for inspirations not listed': m.check_for_missing_inspirations_in_entries,
        'Check for wikipedia links': m.check_for_wikipedia_links,
        'Update included entries': m.update_included_entries,
        'Update inspirations from entries': m.update_inspired_entries,
        'Read entries': m.read_entries
    }

    osg_ui.run_simple_button_app('Maintenance inspirations', actions)



