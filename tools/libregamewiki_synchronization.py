"""
Once data from libregamewiki is imported, synchronize with our database, i.e. identify the entries both have in common,
estimate the differences in the entries both have in common, suggest to add the entries they have not in common to each
other.

unique imported fields: 'assets license', 'categories', 'code language', 'code license', 'developer', 'engine', 'genre', 'library', 'linux-packages', 'name', 'platform'
"""

import json
from utils.osg import *


def get_unique_field_content(field, entries):
    """

    """
    unique_content = set()
    for entry in entries:
        if field in entry:
            unique_content.update(entry[field])
    return sorted(list(unique_content))

platform_replacements = {'Mac': 'macOS'}
name_replacements = {'Eat the Whistle': 'Eat The Whistle', 'Scorched 3D': 'Scorched3D', 'Silver Tree': 'SilverTree', 'Blob Wars Episode 1 : Metal Blob Solid': 'Blobwars: Metal Blob Solid',
                     'Fall Of Imiryn': 'Fall of Imiryn', 'Liquid War 6': 'Liquid War', 'Gusanos': 'GUSANOS'}
language_replacements = {'lua': 'Lua'}
ignored_languages = ['HTML', 'XML', 'WML']


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

    # paths
    root_path  = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir))

    # import lgw import
    json_path = os.path.join(root_path, 'tools', 'lgw_import.json')
    text = read_text(json_path)
    lgw_entries = json.loads(text)

    # perform replacements and disregarding
    for index, lgw_entry in enumerate(lgw_entries):
        if lgw_entry['name'] in name_replacements:
            lgw_entry['name'] = name_replacements[lgw_entry['name']]
        if 'code language' in lgw_entry:
            languages = lgw_entry['code language']
            languages = ['Python' if x.startswith('Python') else x for x in languages]
            languages = ['PHP' if x.startswith('PHP') else x for x in languages]
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
            languages = ['C' if x.startswith('C ') else x for x in languages]
            languages = [language_replacements[x] if x in language_replacements else x for x in languages]
            languages = [x for x in languages if x not in ignored_languages]

            lgw_entry['code language'] = languages
        lgw_entries[index] = lgw_entry

    # check for unique field names
    unique_fields = set()
    for lgw_entry in lgw_entries:
        unique_fields.update(lgw_entry.keys())
    unique_fields = sorted(list(unique_fields))
    print('unique lgw fields: {}'.format(unique_fields))

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