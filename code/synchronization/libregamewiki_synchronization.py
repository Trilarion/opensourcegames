﻿"""
Once data from libregamewiki is imported, synchronize with our database, i.e. identify the entries both have in common,
estimate the differences in the entries both have in common, suggest to add the entries they have not in common to each
other.

unique imported fields: 'assets license', 'categories', 'code language', 'code license', 'developer', 'engine', 'genre', 'library', 'linux-packages', 'name', 'platform'
mandatory imported fields: 'categories', 'name'

Mapping lgw -> ours
assets license -> assets license
categories -> keywords
code language -> code language
code license -> code license
developer -> free text (info)
engine -> code dependencies
genre -> keywords
library -> code dependencies
linux-packages - > free text (info)
name -> name
platform -> platform

TODO also ignore our rejected entries
"""

import json
import pathlib
from utils import constants, utils, osg

lgw_name_aliases = {'Eat the Whistle': 'Eat The Whistle', 'Scorched 3D': 'Scorched3D',
                    'Blob Wars Episode 1 : Metal Blob Solid': 'Blobwars: Metal Blob Solid',
                    'Adventure': 'Colossal Cave Adventure',
                    'Liquid War 6': 'Liquid War', 'Gusanos': 'GUSANOS', 'Corewars': 'Core War', 'FLARE': 'Flare',
                    'Vitetris': 'vitetris', 'Powder Toy': 'The Powder Toy', 'Asylum': 'SDL Asylum',
                    'Atanks': 'Atomic Tanks', 'HeXon': 'heXon', 'Unnethack': 'UnNetHack',
                    'Nova Pinball': 'NOVA PINBALL', 'Jump n Bump': "Jump'n'Bump",
                    'Blades of Exile': 'Classic Blades of Exile',
                    'Colobot': 'Colobot: Gold Edition', 'Dead Justice': 'Cat Mother Dead Justice',
                    'FreeDink': 'GNU FreeDink', 'FRaBs': 'fRaBs', 'Harmonist': 'Harmonist: Dayoriah Clan Infiltration',
                    'Iris2 3D Client - for Ultima Online': 'Iris2',
                    'Java Classic Role Playing Game': 'jClassicRPG', 'Osgg': 'OldSkool Gravity Game',
                    'PyRacerz': 'pyRacerz', 'Starfighter': 'Project: Starfighter',
                    'TORCS': 'TORCS, The Open Racing Car Simulator', 'Vertigo (game)': 'Vertigo',
                    'XInvaders3D': 'XInvaders 3D', 'LambdaRogue': 'LambdaRogue: The Book of Stars',
                    'Maniadrive': 'ManiaDrive', 'Story of Seasons': "Greentwip's Harvest Moon", 'TinyTris': 'Tiny Tris',
                    'Which Way Is Up': 'Which Way Is Up?', 'CannonSmash': 'Cannon Smash', 'UFO:Alien Invasion': 'UFO: Alien Invasion'}
lgw_ignored_entries = ['Hetris', '8 Kingdoms', 'Antigravitaattori', 'Arena of Honour', 'Arkhart', 'Ascent of Justice',
                       'Balazar III', 'Balder3D', 'Barbie Seahorse Adventures', 'Barrage', 'Gnome Batalla Naval',
                       'Blocks',
                       'Brickshooter', 'Bweakfwu', 'Cheese Boys', 'Clippers', 'Codewars', 'CRAFT: The Vicious Vikings',
                       'DQM', 'EmMines', 'Eskimo-run', 'Farlands', 'Feuerkraft', 'Fight or Perish', 'Flatland', 'Forest patrol',
                       'Flare: Empyrean Campaign', 'Free Reign', 'GalaxyMage',
                       'Gloss', 'GRUB Invaders', 'Howitzer Skirmish', 'Imperium: Sticks', 'Interstate Outlaws',
                       'GNOME Games', 'KDE Games', 'LegacyClone', 'Memonix', 'Ninjapix', 'Neverputt', 'Militia Defense',
                       'Sudoku86', 'Look Around the Corner', 'GPSFish',
                       'Terminal Overload release history', 'Scions of Darkness', 'Sedtris', 'SilChess', 'SSTPong',
                       'Tesseract Trainer', 'TunnelWars', 'The Fortress', 'Tunnel']

licenses_map = {'GPLv2': 'GPL-2.0', 'GPLv2+': 'GPL-2.0', 'GPLv3': 'GPL-3.0', 'GPLv3+': 'GPL-3.0'}


def compare_sets(a, b, name, limit=None):
    """

    :param limit:
    :param a:
    :param b:
    :param name:
    :return:
    """
    p = ''
    if not isinstance(a, set):
        a = set(a)
    if not isinstance(b, set):
        b = set(b)
    d = sorted(list(a - b))
    if d and limit != 'notus':
        p += f" {name} : us :  {', '.join(d)}\n"
    d = sorted(list(b - a))
    if d and limit != 'notthem':
        p += f" {name} : them : {', '.join(d)}\n"
    return p


if __name__ == "__main__":

    # some parameter
    similarity_threshold = 0.8
    maximal_newly_created_entries = 40

    # paths
    lgw_import_path = constants.root_path / 'lgw-import'
    lgw_entries_file = lgw_import_path / '_lgw.cleaned.json'

    # import lgw import
    text = utils.read_text(lgw_entries_file)
    lgw_entries = json.loads(text)

    # eliminate the ignored entries
    _ = [x['name'] for x in lgw_entries if x['name'] in lgw_ignored_entries]  # those that will be ignored
    _ = set(lgw_ignored_entries) - set(_)  # those that shall be ignored minus those that will be ignored
    if _:
        print(f'Can un-ignore {_}')
    lgw_entries = [x for x in lgw_entries if x['name'] not in lgw_ignored_entries]

    # perform name and code language replacements
    _ = [x['name'] for x in lgw_entries if x['name'] in lgw_name_aliases.keys()]  # those that will be renamed
    _ = set(lgw_name_aliases.keys()) - set(_)  # those that shall be renamed minus those that will be renamed
    if _:
        print(f'Can un-rename {_}')
    for index, lgw_entry in enumerate(lgw_entries):
        if lgw_entry['name'] in lgw_name_aliases:
            lgw_entry['name'] = lgw_name_aliases[lgw_entry['name']]
        if 'code language' in lgw_entry:
            languages = lgw_entry['code language']
            h = []
            for l in languages:
                for g in ('/', 'and'):
                    if g in l:
                        l = l.split(g)
                        l = [x.strip() for x in l]
                if type(l) == str:
                    l = [l]
                h.extend(l)
            languages = h
            if languages:
                lgw_entry['code language'] = languages
            else:
                del lgw_entry['code language']
        lgw_entries[index] = lgw_entry

    # check for unique field names
    unique_fields = set()
    for lgw_entry in lgw_entries:
        unique_fields.update(lgw_entry.keys())
    print(f'unique lgw fields: {sorted(list(unique_fields))}')

    # which fields are mandatory
    mandatory_fields = unique_fields.copy()
    for lgw_entry in lgw_entries:
        remove_fields = [field for field in mandatory_fields if field not in lgw_entry]
        mandatory_fields -= set(remove_fields)
    print(f'mandatory lgw fields: {sorted(list(mandatory_fields))}')

    # read our database
    our_entries = osg.read_entries()
    print(f'{len(our_entries)} entries with us')

    # just the names
    lgw_names = set([x['name'] for x in lgw_entries])
    our_names = set([x['Title'] for x in our_entries])
    common_names = lgw_names & our_names
    lgw_names -= common_names
    our_names -= common_names
    print(f'{len(common_names)} in both, {len(lgw_names)} only in LGW, {len(our_names)} only with us')

    # find similar names among the rest
    print('similar names (them - us')
    for lgw_name in lgw_names:
        for our_name in our_names:
            if osg.name_similarity(lgw_name, our_name) > similarity_threshold:
                print(f'"{lgw_name}" - "{our_name}"')

    newly_created_entries = 0
    # iterate over their entries
    print('\n')
    for lgw_entry in lgw_entries:
        lgw_name = lgw_entry['name']

        is_included = False
        for our_entry in our_entries:
            our_name = our_entry['Title']

            # find those that entries in LGW that are also in our database and compare them
            if lgw_name == our_name:
                is_included = True
                # a match, check the fields
                name = lgw_name

                p = ''

                # TODO key names have changed on our side

                # platform
                key = 'platform'
                p += compare_sets(lgw_entry.get(key, []), our_entry.get(key, []), key)

                # categories/keywords
                # p += compare_sets(lgw_entry.get('categories', []), our_entry.get('keywords', []), 'categories/keywords')

                # code language
                key = 'code language'
                p += compare_sets(lgw_entry.get(key, []), our_entry.get(key, []), key)

                # code license (GPLv2)
                key = 'code license'
                p += compare_sets(lgw_entry.get(key, []), our_entry.get(key, []), key)

                # engine, library
                p += compare_sets(lgw_entry.get('engine', []), our_entry.get('code dependencies', []),
                                  'code dependencies', 'notthem')
                p += compare_sets(lgw_entry.get('library', []), our_entry.get('code dependencies', []),
                                  'code dependencies', 'notthem')
                p += compare_sets(lgw_entry.get('engine', []) + lgw_entry.get('library', []),
                                  our_entry.get('code dependencies', []), 'engine/library', 'notus')

                # assets license
                key = 'assets license'
                p += compare_sets(lgw_entry.get(key, []), our_entry.get(key, []), key)

                # TODO developer (need to introduce a field with us first)

                if p:
                    print(f'{name}\n{p}')

        if not is_included:
            # a new entry, that we have never seen, maybe we should make an entry of our own
            # TODO we could use the write capabilities to write the entry in our own format, the hardcoded format here might be brittle, on the other hand we can also write slightly wrong stuff here without problems

            if newly_created_entries >= maximal_newly_created_entries:
                continue

            # determine file name
            print(f'create new entry for {lgw_name}')
            file_name = osg.canonical_name(lgw_name) + '.md'
            target_file = constants.entries_path / file_name
            if os.path.isfile(target_file):
                print(f'warning: file {file_name} already existing, save under slightly different name')
                target_file = constants.entries_path / file_name[:-3] + '-duplicate.md'
                if os.path.isfile(target_file):
                    continue  # just for safety reasons

            # add name
            entry = f'# {lgw_name}\n\n'

            # empty home (mandatory on our side)
            home = lgw_entry.get('home', None)
            dev_home = lgw_entry.get('dev home', None)
            entry += f"- Home: {', '.join([x for x in [home, dev_home] if x])}\n"

            # state mandatory on our side
            entry += '- State: \n'

            # platform, if existing
            if 'platform' in lgw_entry:
                entry += f"- Platform: {', '.join(lgw_entry['platform'])}\n"

            # keywords (genre) (also mandatory)
            keywords = lgw_entry.get('genre', [])
            if 'assets license' in lgw_entry:
                keywords.append('open content')
            keywords.sort(key=str.casefold)
            if keywords:
                entry += f"- Keyword: {', '.join(keywords)}\n"

            # code repository (mandatory but not scraped from lgw)
            entry += f"- Code repository: {lgw_entry.get('repo', '')}\n"

            # code language, mandatory on our side
            languages = lgw_entry.get('code language', [])
            languages.sort(key=str.casefold)
            entry += f"- Code language: {', '.join(languages)}\n"

            # code license, mandatory on our side
            licenses = lgw_entry.get('code license', [])
            licenses = [licenses_map[x] if x in licenses_map else x for x in licenses]
            licenses.sort(key=str.casefold)
            entry += f"- Code license: {', '.join(licenses)}\n"

            # code dependencies (only if existing)
            code_dependencies = lgw_entry.get('engine', [])
            code_dependencies.extend(lgw_entry.get('library', []))
            code_dependencies.sort(key=str.casefold)
            if code_dependencies:
                entry += f"- Code dependency: {', '.join(code_dependencies)}\n"

            # assets licenses (only if existing)
            if 'assets license' in lgw_entry:
                licenses = lgw_entry.get('assets license', [])
                licenses = [licenses_map[x] if x in licenses_map else x for x in licenses]
                licenses.sort(key=str.casefold)
                entry += f"- Assets license: {', '.join(licenses)}\n"

            # developer
            if 'developer' in lgw_entry:
                entry += f"- Developer: {', '.join(lgw_entry['developer'])}\n"

            # add empty description (not anymore)
            entry += f"\n_{lgw_entry['description']}_\n\n"

            # external links
            ext_links = lgw_entry['external links']
            if ext_links:
                entry += '\nLinks: {}\n'.format('\n '.join(['{}: {}'.format(x[1], x[0]) for x in ext_links]))

            # linux packages
            if 'linux-packages' in lgw_entry:
                entry += f"{lgw_entry['linux-packages']}\n"

            # write ## Building
            entry += '\n## Building\n'

            # finally write to file
            utils.write_text(target_file, entry)
            newly_created_entries += 1
