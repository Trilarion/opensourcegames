"""

osgameclones has the following fields:
'updated', 'video', 'repo', 'license', 'originals', 'status', 'multiplayer', 'info', 'lang', 'feed', 'content', 'images', 'url', 'name', 'framework', 'type', 'development'

mandatory fields are: 'name', 'license', 'type', 'originals'

possible values:
osgc-development: ['active', 'complete', 'halted', 'sporadic', 'very active']
osgc-multiplayer: ['Co-op', 'Competitive', 'Hotseat', 'LAN', 'Local', 'Online', 'Split-screen']
osgc-type: ['clone', 'remake', 'similar', 'tool']
osgc-status: ['playable', 'semi-playable', 'unplayable']


Mapping osgameclones -> ours

name -> name
type -> keywords, description
originals -> keywords
repo -> code repository
url -> home
feed (-> home)
development -> state
status -> state
multiplayer -> keywords
lang -> code language
framework -> code dependencies
license -> code license / assets license
content -> keywords
info ??
updated not used
images not used
video: not used
"""

import ruamel_yaml as yaml
from difflib import SequenceMatcher
from utils.osg import *

# should change on osgameclones
osgc_name_aliases = {'parpg': 'PARPG', 'OpenRails': 'Open Rails', 'c-evo': 'C-evo', 'Stepmania': 'StepMania', 'Mechanized Assault and eXploration Reloaded': 'Mechanized Assault & eXploration Reloaded',
                     'Jagged Alliance 2 - Stracciatella': 'Jagged Alliance 2 Stracciatella', "Rocks'n'diamonds": "Rocks'n'Diamonds",
                     'Gusanos': 'GUSANOS', 'MicropolisJS': 'micropolisJS'}

# conversion between licenses
osgc_licenses_map = {'GPL2': 'GPL-2.0', 'GPL3': 'GPL-3.0', 'AGPL3': 'AGPL-3.0'}

def similarity(a, b):
    return SequenceMatcher(None, str.casefold(a), str.casefold(b)).ratio()


def unique_field_contents(entries, field):
    """
    """
    unique_content = set()
    for entry in entries:
        if field in entry:
            field_content = entry[field]
            if type(field_content) is str:
                unique_content.add(field_content)
            else:
                unique_content.update(field_content)
    unique_content = sorted(list(unique_content), key=str.casefold)
    return unique_content

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

    # fix names (so they are not longer detected as deviations downstreams)
    for index, entry in enumerate(osgc_entries):
        name = entry['name']
        if name in osgc_name_aliases:
            entry['name'] = osgc_name_aliases[name]
            osgc_entries[index] = entry

    # which fields do they have
    osgc_fields = set()
    for osgc_entry in osgc_entries:
        osgc_fields.update(osgc_entry.keys())
    print('osgc-fields: {}'.format(osgc_fields))

    # which fields are mandatory
    for osgc_entry in osgc_entries:
        remove_fields = [field for field in osgc_fields if field not in osgc_entry]
        osgc_fields -= set(remove_fields)
    print('mandatory osfg-fields: {}'.format(osgc_fields))

    # some field statistics
    print('osgc-development: {}'.format(unique_field_contents(osgc_entries, 'development')))
    print('osgc-multiplayer: {}'.format(unique_field_contents(osgc_entries, 'multiplayer')))
    print('osgc-type: {}'.format(unique_field_contents(osgc_entries, 'type')))
    print('osgc-languages: {}'.format(unique_field_contents(osgc_entries, 'lang')))
    print('osgc-licenses: {}'.format(unique_field_contents(osgc_entries, 'license')))
    print('osgc-status: {}'.format(unique_field_contents(osgc_entries, 'status')))
    print('osgc-framework: {}'.format(unique_field_contents(osgc_entries, 'framework')))

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
    #for osgc_name in osgc_names:
    #    for our_name in our_names:
    #        if similarity(osgc_name, our_name) > similarity_threshold:
    #            print('{} - {}'.format(osgc_name, our_name))

    for osgc_entry in osgc_entries:
        osgc_name = osgc_entry['name']

        is_included = False
        for our_entry in our_entries:
            our_name = our_entry['name']

            # find those that entries in osgameclones that are also in our database and compare them
            if osgc_name == our_name:
                is_included = True
                # a match, check the fields
                name = osgc_name

                # lang field
                if 'lang' in osgc_entry:
                    languages = osgc_entry['lang']
                    if type(languages) == str:
                        languages = [languages]
                    our_languages = our_entry['code language'] # essential field
                    for lang in languages:
                        if lang not in our_languages:
                            print('{}: language {}'.format(name, lang))

                # license
                if 'license' in osgc_entry:
                    licenses = osgc_entry['license']
                    our_code_licenses = our_entry['code license'] # essential field
                    our_assets_licenses = our_entry.get('assets license', [])
                    for license in licenses:
                        # transform
                        if license in osgc_licenses_map:
                            license = osgc_licenses_map[license]
                        if license not in our_code_licenses and license not in our_assets_licenses:
                            print('{}: code/assets license {}'.format(name, license))

                # framework
                if 'framework' in osgc_entry:
                    frameworks = osgc_entry['framework']
                    if type(frameworks) == str:
                        frameworks = [frameworks]
                    our_frameworks = our_entry.get('code dependencies', [])
                    for framework in frameworks:
                        if framework not in our_frameworks:
                            print('{}: code dependency {}'.format(name, framework))

                # repo
                if 'repo' in osgc_entry:
                    repos = osgc_entry['repo']
                    if type(repos) == str:
                        repos = [repos]
                    our_repos = our_entry['code repository']
                    for repo in repos:
                        if (repo not in our_repos) and (repo+'.git' not in our_repos): # add .git automatically and try it too
                            print('{}: code repository {}'.format(name, repo))

                # url
                if 'url' in osgc_entry:
                    urls = osgc_entry['url']
                    if type(urls) == str:
                        urls = [urls]
                    our_urls = our_entry['home']
                    for url in urls:
                        if url not in our_urls:
                            print('{}: home {}'.format(name, url))

                # status
                if 'status' in osgc_entry:
                    status = osgc_entry['status']
                    our_status = our_entry['state'] # essential field
                    if status == 'playable' and 'mature' not in our_status:
                        print('{}: status playable, not mature with us'.format(name))
                    if status != 'playable' and 'mature' in our_status:
                        print('{}: status not playable, mature with us'.format(name))
                    if status == 'unplayable':
                        print('{}: status unplayable'.format(name))

                # development
                if 'development' in osgc_entry:
                    development = osgc_entry['development']
                    our_inactive = 'inactive' in our_entry
                    our_status = our_entry['state']  # essential field
                    if development == 'halted' and not our_inactive:
                        print('{}: development halted, not inactive with us'.format(name))
                    if (development == 'very active' or development == 'active' or development == 'sporadic') and our_inactive:
                        print('{}: development sporadic-very active, inactive with us'.format(name))
                    if development == 'complete' and 'mature' not in our_status:
                        print('{}: development complete, not mature with us'.format(name))

        if not is_included:
            # a new entry, that we have never seen, maybe we should make an entry of our own
            continue

            print('create new entry for {}'.format(osgc_name))
            file_name = regex_sanitze_name.sub('', osgc_name).replace(' ', '_').lower()
            entry = '# {}\n\n'.format(osgc_name)

            # for now only make remakes or clones
            game_type = osgc_entry['type'] # do not overwrite type!
            if game_type not in ('remake', 'clone'):
                continue
            description = '{} of {}'.format(game_type.capitalize(), ', '.join(osgc_entry['originals']))
            entry += '_{}_\n\n'.format(description)



