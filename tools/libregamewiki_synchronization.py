"""
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

"""

import json
from utils.osg import *


def get_unique_field_content(field, entries):
    """

    """
    unique_content = {}
    for entry in entries:
        for element in entry.get(field, []):
            unique_content[element] = unique_content.get(element, 0) + 1
    unique_content = list(unique_content.items())
    unique_content.sort(key=lambda x: -x[1])
    unique_content = ['{}({})'.format(k, v) for k, v in unique_content]
    return unique_content



name_replacements = {'Eat the Whistle': 'Eat The Whistle', 'Scorched 3D': 'Scorched3D', 'Silver Tree': 'SilverTree', 'Blob Wars Episode 1 : Metal Blob Solid': 'Blobwars: Metal Blob Solid', 'Adventure': 'Colossal Cave Adventure',
                     'Fall Of Imiryn': 'Fall of Imiryn', 'Liquid War 6': 'Liquid War', 'Gusanos': 'GUSANOS', 'Corewars': 'Core War', 'FLARE': 'Flare', 'Vitetris': 'vitetris', 'Powder Toy': 'The Powder Toy', 'Asylum': 'SDL Asylum',
                     'Atanks': 'Atomic Tanks'}
ignored_names = ['Hetris', '8 Kingdoms', 'Antigravitaattori', 'Arena of Honour', 'Arkhart', 'Ascent of Justice', 'Balazar III', 'Balder3D', 'Barbie Seahorse Adventures', 'Barrage', 'Gnome Batalla Naval', 'User:AVRS/sandbox']
ignored_languages = ['HTML', 'XML', 'WML', 'English']

ignored_categories = ['GPL', 'C++', 'C', 'ECMAScript', 'Python', 'Java', 'CC BY-SA', 'Lua', 'LGPL', 'CC-BY', 'BSD', 'MIT', 'Qt', 'SDL', 'OpenGL', 'Pygame', 'PD', 'GLUT', 'Haskell', 'Allegro', 'Ruby', 'Zlib/libpng', 'OpenAL', 'Perl', 'Free Pascal', 'LÖVE', 'HTML5', 'Id Tech 1']

genre_replacements = {'rpg': 'role playing', 'fps': 'first person, shooter', 'tbs': 'turn based, strategy', 'rts': 'real time, strategy'}

platform_replacements = {'Mac': 'macOS'}

library_replacements = {'Pygame': 'pygame', 'QT': 'Qt'}


def list_compare(a, b, k):
    """

    """
    x = [x for x in a if x not in b]
    p = ''
    for x in x:
        p += ' {} {} missing\n'.format(k, x)
    return p


if __name__ == "__main__":

    similarity_threshold = 0.8
    maximal_newly_created_entries = 40

    # paths
    root_path  = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir))

    # import lgw import
    json_path = os.path.join(root_path, os.pardir, 'lgw_import.json')
    text = read_text(json_path)
    lgw_entries = json.loads(text)

    # perform replacements and disregarding
    lgw_entries = [x for x in lgw_entries if x['name'] not in ignored_names]
    for index, lgw_entry in enumerate(lgw_entries):
        if lgw_entry['name'] in name_replacements:
            lgw_entry['name'] = name_replacements[lgw_entry['name']]
        if 'code language' in lgw_entry:
            languages = lgw_entry['code language']
            languages = ['Python' if x.startswith('Python') else x for x in languages]
            languages = ['PHP' if x.startswith('PHP') else x for x in languages]
            languages = ['Lua' if x.lower().startswith('lua') else x for x in languages]
            languages = ['JavaScript' if x.lower().startswith('javascript') else x for x in languages]
            h = []
            for l in languages:
                for g in ('/', 'and'):
                    if g in l:
                        l = l.split(g)
                        l = [x.strip() for x in l]
                if type(l) == str:
                    l = [l]
                h.extend(l)
            languages = ['C++' if x.startswith('C++') else x for x in h]
            languages = ['C' if x.startswith('C ') or x.startswith('C[') else x for x in languages]
            languages = [x for x in languages if x not in ignored_languages]
            if languages:
                lgw_entry['code language'] = languages
            else:
                del lgw_entry['code language']
        if 'categories' in lgw_entry:
            categories = lgw_entry['categories']
            categories = [x for x in categories if not x.startswith('Game')]
            categories = [x for x in categories if not x.startswith('Article')]
            categories = [x for x in categories if not x.startswith('Page')]
            categories = [x for x in categories if x not in ignored_categories]
            categories = [x.lower() if len(x) > 2 else x for x in categories]
            if categories:
                lgw_entry['categories'] = categories
            else:
                del lgw_entry['categories']
        if 'genre' in lgw_entry:
            genres = lgw_entry['genre']
            genres = [x for x in genres if len(x) > 0]
            genres = [x.lower() for x in genres]
            genres = [x[:-5] if x.endswith(' game') else x for x in genres]
            genres = [x[:-5] if x.endswith(' games') else x for x in genres]
            genres = [genre_replacements[x] if x in genre_replacements else x for x in genres]
            for h in ('platform',):
                genres = [h if x.startswith(h) else x for x in genres]
            if genres:
                lgw_entry['genre'] = genres
            else:
                del lgw_entry['genre']
        if 'library' in lgw_entry:
            libraries = lgw_entry['library']
            libraries = [library_replacements[x] if x in library_replacements else x for x in libraries]
            lgw_entry['library'] = libraries
        if 'code license' in lgw_entry:
            licenses = lgw_entry['code license']
            licenses = [x.strip() for x in licenses] # strip
            licenses = [x[1:] if x.startswith('"') else x for x in licenses] # cut " at the beginning
            licenses = [x[:-1] if x.endswith('"') else x for x in licenses]  # cut " at the end
            licenses = [x[4:] if x.startswith('GNU ') else x for x in licenses]
            licenses = [x[:-3] if x.endswith('[1]') or x.endswith('[2]') else x for x in licenses]
            licenses = [x[:-8] if x.lower().endswith(' license') else x for x in licenses]
            licenses = [x.strip() for x in licenses] # strip
            #licenses = ['GPL-2.0' if x.startswith('GPLv2') or x.startswith('GPL v2') or x.startswith('GPL 2') else x for x in licenses]
            #licenses = ['GPL-3.0' if x.startswith('GPLv3') or x.startswith('GPL v3') or x.startswith('GPL 3') or x.startswith('GPL v.3') else x for x in licenses]
            licenses = ['Public domain' if x.lower().startswith('public domain') else x for x in licenses]
            lgw_entry['code license'] = licenses
        if 'assets license' in lgw_entry:
            licenses = lgw_entry['assets license']
            licenses = [x.strip() for x in licenses] # strip
            licenses = [x[1:] if x.startswith('"') else x for x in licenses] # cut " at the beginning
            licenses = [x[:-1] if x.endswith('"') else x for x in licenses]  # cut " at the end
            licenses = [x[4:] if x.startswith('GNU ') else x for x in licenses]
            licenses = [x[:-3] if x.endswith('[1]') or x.endswith('[2]') else x for x in licenses]
            licenses = [x[:-8] if x.lower().endswith(' license') else x for x in licenses]
            licenses = [x.strip() for x in licenses] # strip
            licenses = ['GPL-2.0' if x.startswith('GPLv2') or x.startswith('GPL v2') or x.startswith('GPL 2') else x for x in licenses]
            licenses = ['GPL-3.0' if x.startswith('GPLv3') or x.startswith('GPL v3') or x.startswith('GPL 3') or x.startswith('GPL v.3') else x for x in licenses]
            licenses = ['Public domain' if x.lower().startswith('public domain') else x for x in licenses]
            lgw_entry['assets license'] = licenses

        lgw_entries[index] = lgw_entry


    # check for unique field names
    unique_fields = set()
    for lgw_entry in lgw_entries:
        unique_fields.update(lgw_entry.keys())
    print('unique lgw fields: {}'.format(sorted(list(unique_fields))))

    # which fields are mandatory
    for lgw_entry in lgw_entries:
        remove_fields = [field for field in unique_fields if field not in lgw_entry]
        unique_fields -= set(remove_fields)
    print('mandatory lgw fields: {}'.format(sorted(list(unique_fields))))

    # unique contents
    print('{}: {}'.format('platform', get_unique_field_content('platform', lgw_entries)))
    print('{}: {}'.format('code language', get_unique_field_content('code language', lgw_entries)))
    print('{}: {}'.format('categories', get_unique_field_content('categories', lgw_entries)))
    print('{}: {}'.format('genre', get_unique_field_content('genre', lgw_entries)))
    print('{}: {}'.format('library', get_unique_field_content('library', lgw_entries)))
    print('{}: {}'.format('code license', get_unique_field_content('code license', lgw_entries)))
    print('{}: {}'.format('assets license', get_unique_field_content('assets license', lgw_entries)))
    print('{}: {}'.format('engine', get_unique_field_content('engine', lgw_entries)))

    # read our database
    games_path = os.path.join(root_path, 'games')
    our_entries = assemble_infos(games_path)
    print('{} entries with us'.format(len(our_entries)))

    # just the names
    lgw_names = set([x['name'] for x in lgw_entries])
    our_names = set([x['name'] for x in our_entries])
    common_names = lgw_names & our_names
    lgw_names -= common_names
    our_names -= common_names
    print('{} in both, {} only in LGW, {} only with us'.format(len(common_names), len(lgw_names), len(our_names)))

    # find similar names among the rest
    #print('similar names')
    #for lgw_name in lgw_names:
    #    for our_name in our_names:
    #        if game_name_similarity(lgw_name, our_name) > similarity_threshold:
    #            print('{} - {}'.format(lgw_name, our_name))

    newly_created_entries = 0
    # iterate over their entries
    print('\n')
    for lgw_entry in lgw_entries:
        lgw_name = lgw_entry['name']
        
        is_included = False
        for our_entry in our_entries:
            our_name = our_entry['name']

            # find those that entries in LGW that are also in our database and compare them
            if lgw_name == our_name:
                is_included = True
                # a match, check the fields
                name = lgw_name

                p = ''

                # platform
                key = 'platform'
                p += list_compare(lgw_entry.get(key, []), our_entry.get(key, []), key)

                # code language
                key = 'code language'
                p += list_compare(lgw_entry.get(key, []), our_entry.get(key, []), key)

                if p:
                    print('{}\n{}'.format(name, p))

        if not is_included:
            # a new entry, that we have never seen, maybe we should make an entry of our own

            if newly_created_entries >= maximal_newly_created_entries:
                continue

            # determine file name
            print('create new entry for {}'.format(lgw_name))
            file_name = derive_canonical_file_name(lgw_name)
            target_file = os.path.join(games_path, file_name)
            if os.path.isfile(target_file):
                print('warning: file {} already existing, save under slightly different name'.format(file_name))
                target_file = os.path.join(games_path, file_name[:-3] + '-duplicate.md')
                if os.path.isfile(target_file):
                    continue # just for safety reasons

            # add name
            entry = '# {}\n\n'.format(lgw_name)

            # add empty description
            entry += '__\n\n'

            # empty home (mandatory on our side)
            entry += '- Home: \n'

            # state mandatory on our side
            entry += '- State: \n'

            # platform, if existing
            if 'platform' in lgw_entry:
                entry += 'Platform: {}\n'.format(', '.join(lgw_entry['platform']))

            # keywords (genre) (also mandatory)
            keywords = lgw_entry.get('genre', [])
            if 'assets license' in lgw_entry:
                keywords.append('open content')
            keywords.sort(key=str.casefold)
            if keywords:
                entry += '- Keywords: {}\n'.format(', '.join(keywords))

            # code repository (mandatory but not scraped from lgw)
            entry += '- Code repository: \n'

            # code language, mandatory on our side
            languages = lgw_entry.get('code language', [])
            languages.sort(key=str.casefold)
            entry += '- Code language: {}\n'.format(', '.join(languages))

            # code license, mandatory on our side
            licenses = lgw_entry.get('code license', [])
            licenses.sort(key=str.casefold)
            entry += '- Code license: {}\n'.format(', '.join(licenses))

            # code dependencies (only if existing)
            code_dependencies = lgw_entry.get('engine', [])
            code_dependencies.extend(lgw_entry.get('library', []))
            code_dependencies.sort(key=str.casefold)
            if code_dependencies:
                entry += '- Code dependencies: {}\n'.format(', '.join(code_dependencies))

            # assets licenses (only if existing)
            if 'assets license' in lgw_entry:
                entry += '- Assets license: {}\n'.format(', '.join(lgw_entry['assets license']))

            # free text
            if 'developer' in lgw_entry:
                entry += '\nDeveloper: {}\n'.format(', '.join(lgw_entry['developer']))
            if 'linux-packages' in lgw_entry:
                entry += '{}\n'.format(lgw_entry['linux-packages'])

            # write ## Building
            entry += '\n## Building\n'

            # finally write to file
            write_text(target_file, entry)
            newly_created_entries += 1