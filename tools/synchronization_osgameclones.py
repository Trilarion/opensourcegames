"""


Mapping osgameclones, ours

name - name
lang - code language
license - code license
development - state
status - state
type - keywords
url - home
multiplayer - keywords
content - asset license, keywords
"""

import ruamel_yaml as yaml
from difflib import SequenceMatcher
from utils.osg import *

# should change on osgameclones
osgc_name_aliases = {'parpg': 'PARPG', 'OpenRails': 'Open Rails', 'c-evo': 'C-evo', 'Stepmania': 'StepMania', 'Mechanized Assault and eXploration Reloaded': 'Mechanized Assault & eXploration Reloaded',
                     'Jagged Alliance 2 - Stracciatella': 'Jagged Alliance 2 Stracciatella', 'xu4': 'XU4', "Rocks'n'diamonds": "Rocks'n'Diamonds",
                     'Gusanos': 'GUSANOS', 'MicropolisJS': 'micropolisJS'}

def similarity(a, b):
    return SequenceMatcher(None, str.casefold(a), str.casefold(b)).ratio()

if __name__ == "__main__":

    # paths
    similarity_threshold = 0.8
    root_path  = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir))

    # import the osgameclones data
    osgc_path = os.path.realpath(os.path.join(root_path, os.path.pardir, 'osgameclones', 'games'))
    files = os.listdir(osgc_path)

    # iterate over all yaml files in osgameclones/data folder
    osgc_entries = []
    for file in files:
        # read yaml
        with open(os.path.join(osgc_path, file), 'r') as stream:
            try:
                _ = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                raise  exc

        # add to entries
        osgc_entries.extend(_)
    print('{} entries in osgameclones'.format(len(osgc_entries)))

    # fix names
    for index, entry in enumerate(osgc_entries):
        name = entry['name']
        if name in osgc_name_aliases:
            entry['name'] = osgc_name_aliases[name]
            osgc_entries[index] = entry

    # get all osgc 'lang' fields
    osgc_langs = set([x['lang'] for x in osgc_entries if 'lang' in x])
    print('osgc-languages: {}'.format(osgc_langs))


    # read our database
    games_path = os.path.join(root_path, 'games')
    our_entries = assemble_infos(games_path)
    print('{} entries with us'.format(len(our_entries)))

    # just the names
    osgc_names = set([x['name'] for x in osgc_entries])
    our_names = set([x['name'] for x in our_entries])
    common_names = osgc_names & our_names
    osgc_names -= common_names
    our_names -= common_names
    print('{} in both, {} only in osgameclones, {} only with us'.format(len(common_names), len(osgc_names), len(our_names)))

    # find similar names among the rest
    for osgc_name in osgc_names:
        for our_name in our_names:
            if similarity(osgc_name, our_name) > similarity_threshold:
                print('{} - {}'.format(osgc_name, our_name))

    # find those that entries in osgameclones that are also in our database
    for osgc_entry in osgc_entries:
        osgc_name = osgc_entry['name']

        for our_entry in our_entries:
            our_name = our_entry['name']

            if osgc_name == our_name:
                # a match, check the fields
                if osgc_entry['lang'] not in our_name['code language']:
                    print()





