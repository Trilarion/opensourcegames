"""
Checks the entries and tries to detect additional developer content, by retrieving websites or logging information from
stored Git repositories.
"""
# TODO bag of words (split, strip, lowercase) on dev names and try to detect sex and nationality
# TODO name is not unique (not even on GH) so maybe add name to profile name
# TODO for duplicate names, create ignore list
# TODO split devs with multiple gh or sf accounts (unlikely), start with most (like name Adam) - naming convention @01 etc.
# TODO check for devs without contact after gitlab/bitbucket/..
# TODO gitlab/bitbucket import
# TODO wikipedia search for all with more than 3 games
# TODO link check also for developers (also similar links w/wo slash at the end or http(s))

import time
from utils import osg, osg_ui


class DevelopersMaintainer:

    def __init__(self):
        self.developers = None
        self.entries = None

    def read_developer(self):
        self.developers = osg.read_developers()
        print(f'{len(self.developers)} developers read')

    def write_developer(self):
        if not self.developers:
            print('developers not yet loaded')
            return
        osg.write_developers(self.developers)
        print(f'{len(self.developers)} developers written')

    def check_for_duplicates(self):
        if not self.developers:
            print('developers not yet loaded')
            return
        start_time = time.process_time()
        developer_names = list(self.developers.keys())
        for index, name in enumerate(developer_names):
            current_dev = self.developers.get(name)
            current_contact_set = set(current_dev['Contact']) if 'Contact' in current_dev else set()
            for other_name in developer_names[index + 1:]:
                if osg.name_similarity(str.casefold(name), str.casefold(other_name)) > 0.85:
                    print(f' {name} - {other_name} is similar')
                other_dev = self.developers.get(other_name)
                if len(current_contact_set) > 0 and 'Contact' in other_dev:
                    other_contact_set = set(other_dev['Contact'])
                    intersecting = current_contact_set.intersection(other_contact_set)
                    if len(intersecting) > 0:
                        print(f' {name} - {other_name} share the {intersecting} contact(s)')
        print(f'duplicates checked (took {time.process_time() - start_time:.1f}s)')

    def check_for_orphans(self):
        """
        List developers without games.
        """
        if not self.developers:
            print('developers not yet loaded')
            return
        for dev in self.developers.values():
            if not dev['Games']:
                print(f" {dev['Name']} has no games")
        print('orphans checked')

    def remove_orphans(self):
        """
        Remove developers without games.
        """
        if not self.developers:
            print('developers not yet loaded')
            return
        self.developers = {k: v for k,v in self.developers.items() if v['Games']}
        print(f'orphans removed ({len(self.developers)} devs left)')
        
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
                    print(f'Entry "{entry_name}" listed as game of developer "{dev_name}" but this entry does not exist')
                else:
                    entry = x[0]
                    if 'Developer' not in entry or dev_name not in entry['Developer']:
                        print(f'Entry "{entry_name}" listed in developer "{dev_name}" but not listed in that entry')
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
                if entry_dev in self.developers:
                    self.developers[entry_dev]['Games'].append(entry_name)
                else:
                    # completely new developer
                    self.developers[entry_dev] = {'Name': entry_dev, 'Games': [entry_name]}
        print('developers updated')

    def read_entries(self):
        self.entries = osg.read_entries()
        print(f'{len(self.entries)} entries read')

    def special_ops(self):
        # need entries loaded
        if not self.entries:
            print('entries not yet loaded')
            return

        # remove all developer that are orphans
        remove = [k for k, v in self.developers.items() if not v['Games']]
        for k in remove:
            del self.developers[k]

        # # comments for developers
        # for entry in self.entries:
        #     for developer in entry.get('Developer', []):
        #         if developer.comment:
        #             print('{:<25} - {:<25} - {}'.format(entry['File'], developer, developer.comment))


if __name__ == "__main__":

    m = DevelopersMaintainer()

    actions = {
        'Read developers': m.read_developer,
        'Write developers': m.write_developer,
        'Check for duplicates': m.check_for_duplicates,
        'Check for orphans': m.check_for_orphans,
        'Remove orphans': m.remove_orphans,
        'Check for games in developers not listed': m.check_for_missing_developers_in_entries,
        'Update developers from entries': m.update_developers_from_entries,
        'Special': m.special_ops,
        'Read entries': m.read_entries
    }

    osg_ui.run_simple_button_app('Maintenance developer', actions)