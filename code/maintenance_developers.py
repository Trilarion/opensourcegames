"""
Checks the entries and tries to detect additional developer content, by retrieving websites or logging information from
stored Git repositories.
"""
# TODO bag of words (split, strip, lowercase) on dev names and try to detect sex and nationality
# TODO for duplicate names, create ignore list
# TODO split devs with multiple gh or sf accounts (unlikely), start with most (like name Adam) - naming convention @01 etc.
# TODO check for devs without contact after gitlab/bitbucket/..
# TODO gitlab/bitbucket import

import time
from utils import osg, osg_ui


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
        print('{} developers written'.format(len(self.developers)))

    def check_for_duplicates(self):
        if not self.developers:
            print('developers not yet loaded')
            return
        start_time = time.process_time()
        developer_names = list(self.developers.keys())
        for index, name in enumerate(developer_names):
            for other_name in developer_names[index + 1:]:
                if osg.name_similarity(str.casefold(name), str.casefold(other_name)) > 0.85:
                    print(' {} - {} is similar'.format(name, other_name))
        print('duplicates checked (took {:.3f}s)'.format(time.process_time()-start_time))

    def check_for_orphans(self):
        if not self.developers:
            print('developers not yet loaded')
            return
        for dev in self.developers.values():
            if not dev['Games']:
                print(' {} has no games'.format(dev['Name']))
        print('orphans checked')
        
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
                entry_dev = entry_dev.value  # ignore a possible comment
                if entry_dev in self.developers:
                    self.developers[entry_dev]['Games'].append(entry_name)
                else:
                    # completely new developer
                    self.developers[entry_dev] = {'Name': entry_dev, 'Games': [entry_name]}
        print('developers updated')

    def read_entries(self):
        self.entries = osg.read_entries()
        print('{} entries read'.format(len(self.entries)))

    def special_ops(self):
        # need entries loaded
        if not self.entries:
            print('entries not yet loaded')
            return
        for entry in self.entries:
            for developer in entry.get('Developer', []):
                if developer.comment:
                    print('{:<25} - {:<25} - {}'.format(entry['File'], developer.value, developer.comment))


if __name__ == "__main__":

    m = DevelopersMaintainer()

    actions = {
        'Read developers': m.read_developer,
        'Write developers': m.write_developer,
        'Check for duplicates': m.check_for_duplicates,
        'Check for orphans': m.check_for_orphans,
        'Check for games in developers not listed': m.check_for_missing_developers_in_entries,
        'Update developers from entries': m.update_developers_from_entries,
        'Special': m.special_ops,
        'Read entries': m.read_entries
    }

    osg_ui.run_simple_button_app('Maintenance developer', actions)