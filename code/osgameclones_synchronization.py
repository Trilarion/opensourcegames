"""

osgameclones has the following fields:
'updated', 'video', 'repo', 'license', 'originals', 'status', 'multiplayer', 'info', 'lang', 'feed', 'content', 'images', 'url', 'name', 'framework', 'type', 'development'

mandatory fields are: 'name', 'license', 'type', 'originals'

possible values:
osgc-development: active(337), complete(32), halted(330), sporadic(129), very active(6)
osgc-multiplayer: Co-op(5), Competitive(13), Hotseat(3), LAN(17), Local(3), Matchmaking(1), Online(33), Split-screen(7)
osgc-type: clone(171), remake(684), similar(11), tool(7)
osgc-status: playable(274), semi-playable(34), unplayable(34)
osgc-license: ['AFL3', 'AGPL3', 'Apache', 'Artistic', 'As-is', 'BSD', 'BSD2', 'BSD4', 'bzip2', 'CC-BY', 'CC-BY-NC', 'CC-BY-NC-ND', 'CC-BY-NC-SA', 'CC-BY-SA', 'CC0', 'Custom', 'GPL2', 'GPL3', 'IJG', 'ISC', 'JRL', 'LGPL2', 'LGPL3', 'Libpng', 'MAME', 'MIT', 'MPL', 'MS-PL', 'Multiple', 'NGPL', 'PD', 'WTFPL', 'Zlib']
osgc-content: commercial(104), free(32), open(61), swappable(5)

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
info -> after fields
updated not used
images not used
video: not used

TODO also ignore our rejected entries
"""

import ruamel.yaml as yaml
import os
from utils import constants, utils, osg

# should change on osgameclones
osgc_name_aliases = {'4DTris': '4D-TRIS', 'fheroes2': 'Free Heroes 2', 'DrCreep': 'The Castles of Dr. Creep',
                     'Duke3d_win32': 'Duke3d_w32', 'GNOME Atomix': 'Atomix', 'Head over Heels 2': 'Head over Heels',
                     'mewl': 'M.E.W.L.', 'LinWarrior': 'Linwarrior 3D', 'Mice Men Remix': 'Mice Men: Remix',
                     'OpenApoc': 'Open Apocalypse', 'open-cube': 'Open Cube', 'open-horizon': 'Open Horizon',
                     'opengl_test_drive_clone': 'OpenGL Test Drive Remake', "Freenukum Jump'n Run": 'Freenukum',
                     'Play Freeciv!': 'Freeciv-web', 'ProjectX': 'Forsaken', 'Lyon': 'Roton',
                     'Siege of Avalon Open Source': 'Siege of Avalon : Open Source', 'ss13remake': 'SS13 Remake',
                     'shadowgrounds': 'Shadowgrounds', 'RxWars': 'Prescription Wars',
                     'Super Mario Bros And Level Editor in C#': 'Mario Objects', 'Unitystation': 'unitystation',
                     'tetris': 'Just another Tetris™ clone', 'twin-e': 'TwinEngine', 'super-methane-brothers-gx': 'Super Methane Brothers for Wii and GameCube',
                     'CrossUO: Ultima Online': 'CrossUO', 'Doomsday': 'Doomsday Engine', 'OpMon': 'OPMon'}

# conversion between licenses syntax them and us
osgc_licenses_map = {'GPL2': 'GPL-2.0', 'GPL3': 'GPL-3.0', 'AGPL3': 'AGPL-3.0', 'LGPL3': 'LGPL-3.0',
                     'LGPL2': 'LGPL-2.0 or 2.1?', 'MPL': 'MPL-2.0', 'Apache': 'Apache-2.0',
                     'Artistic': 'Artistic License', 'Zlib': 'zlib', 'PD': 'Public domain', 'AFL3': 'AFL-3.0',
                     'BSD2': '2-clause BSD', 'JRL': 'Java Research License'}

# ignore osgc entries (for various reasons like unclear license etc.)
osgc_ignored_entries = ["A Mouse's Vengeance", 'achtungkurve.com', 'AdaDoom3', 'Agendaroids', 'Alien 8', 'Ard-Reil',
                        'Balloon Fight', 'bladerunner (Engine within SCUMMVM)', 'Block Shooter', 'Bomb Mania Reloaded',
                        'boulder-dash', 'Cannon Fodder', 'Contra_remake', 'CosmicArk-Advanced', 'Deuteros X',
                        'datastorm', 'div-columns', 'div-pacman2600', 'div-pitfall', 'div-spaceinvaders2600', 'EXILE',
                        'Free in the Dark', 'Prepare Carefully', 'OpenKKnD',
                        'Football Manager', 'Fight Or Perish', 'EarthShakerDS', 'Entombed!', 'FreeRails 2',
                        'Glest Advanced Engine', 'FreedroidClassic', 'FreeFT', 'Future Blocks', 'HeadOverHeels',
                        'Herzog 3D', 'Homeworld SDL', 'imperialism-remake', 'Jumping Jack 2: Worryingly Familiar',
                        'Jumping Jack: Further Adventures', 'Jumpman', 'legion', 'KZap', 'LastNinja', 'Lemmix', 'LixD',
                        'luminesk5', 'Manic Miner', 'Meridian 59 Server 105', 'Meridian 59 German Server 112',
                        'Mining Haze', 'OpenGeneral', 'MonoStrategy', 'New RAW', 'OpenDeathValley', 'OpenOutcast',
                        'openStrato', 'OpenPop', 'pacman',
                        'Phavon', 'Project: Xenocide', 'pyspaceinvaders', 'PyTouhou', 'Racer',
                        'Ruby OMF 2097 Remake', 'Snipes', 'Spaceship Duel', 'Space Station 14', 'Starlane Empire',
                        'Styx', 'Super Mario Bros With SFML in C#', 'thromolusng', 'Tile World 2', 'Tranzam',
                        'Voxelstein 3D', 'XQuest 2',
                        'xrick', 'zedragon', 'Uncharted waters 2 remake', 'Desktop Adventures Engine for ScummVM',
                        'Open Sonic', 'Aladdin_DirectX', 'Alive_Reversing']


def unique_field_contents(entries, field):
    """
    """
    unique_content = set()
    for entry in entries:
        if field in entry:
            field_content = entry[field]
            if type(field_content) is list:
                unique_content.update(field_content)
            else:
                unique_content.add(field_content)
    unique_content = sorted(list(unique_content), key=str.casefold)
    return unique_content


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
        p += ' {} : us :  {}\n'.format(name, ', '.join(d))
    d = sorted(list(b - a))
    if d and limit != 'notthem':
        p += ' {} : them : {}\n'.format(name, ', '.join(d))
    return p


if __name__ == "__main__":

    # some parameter
    similarity_threshold = 0.8
    maximal_newly_created_entries = 40

    # paths
    root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir))

    # import the osgameclones data
    osgc_path = os.path.realpath(os.path.join(root_path, os.path.pardir, 'osgameclones.git', 'games'))
    osgc_files = os.listdir(osgc_path)

    # iterate over all yaml files in osgameclones/data folder and load contents
    osgc_entries = []
    for file in osgc_files:
        # read yaml
        with open(os.path.join(osgc_path, file), 'r', encoding='utf-8') as stream:
            try:
                _ = yaml.safe_load(stream)
            except Exception as exc:
                print(file)
                raise exc

        # add to entries
        osgc_entries.extend(_)
    print('Currently {} entries in osgameclones'.format(len(osgc_entries)))

    # check: print all git repos with untypical structure
    untypical_structure = ''
    for osgc_entry in osgc_entries:
        name = osgc_entry['name']
        if 'repo' in osgc_entry:
            osgc_repos = osgc_entry['repo']
            if isinstance(osgc_repos, str):
                osgc_repos = [osgc_repos]
            for repo in osgc_repos:
                if 'github' in repo and any((repo.endswith(x) for x in ('/', '.git'))):
                    untypical_structure += ' {} : {}\n'.format(osgc_entry['name'], repo)
    if untypical_structure:
        print('Git repos with untypical URL\n{}'.format(untypical_structure))

    # which fields do they have
    osgc_fields = set()
    for osgc_entry in osgc_entries:
        osgc_fields.update(osgc_entry.keys())
    osgc_fields = sorted(list(osgc_fields))
    print('Unique osgc-fields\n {}'.format(', '.join(osgc_fields)))

    for field in osgc_fields:
        if field in ('video', 'feed', 'url', 'repo', 'info', 'updated', 'images', 'name', 'originals'):
            continue
        osgc_content = [entry[field] for entry in osgc_entries if field in entry]
        # flatten
        flat_content = []
        for c in osgc_content:
            if isinstance(c, list):
                flat_content.extend(c)
            else:
                flat_content.append(c)
        statistics = utils.unique_elements_and_occurrences(flat_content)
        statistics.sort(key=str.casefold)
        print('{}: {}'.format(field, ', '.join(statistics)))

    # eliminate the ignored entries
    _ = [x['name'] for x in osgc_entries if x['name'] in osgc_ignored_entries]  # those that will be ignored
    _ = set(osgc_ignored_entries) - set(_)  # those that shall be ignored minus those that will be ignored
    if _:
        print('Can un-ignore {}'.format(_))
    osgc_entries = [x for x in osgc_entries if x['name'] not in osgc_ignored_entries]

    # fix names and licenses (so they are not longer detected as deviations downstreams)
    _ = [x['name'] for x in osgc_entries if x['name'] in osgc_name_aliases.keys()]  # those that will be renamed
    _ = set(osgc_name_aliases.keys()) - set(_)  # those that shall be renamed minus those that will be renamed
    if _:
        print('Can un-rename {}'.format(_))
    for index, entry in enumerate(osgc_entries):
        name = entry['name']
        if name in osgc_name_aliases:
            entry['name'] = osgc_name_aliases[name]
        if 'license' in entry:
            osgc_licenses = entry['license']
            osgc_licenses = [osgc_licenses_map.get(x, x) for x in osgc_licenses]
            entry['license'] = osgc_licenses
        # fix content (add suffix content)
        if 'content' in entry:
            osgc_content = entry['content']
            if isinstance(osgc_content, str):
                osgc_content = [osgc_content]
            osgc_content = [x + ' content' for x in osgc_content]
            entry['content'] = osgc_content
        osgc_entries[index] = entry  # TODO is this necessary or is the entry modified anyway?

    # which fields do they have
    osgc_fields = set()
    for osgc_entry in osgc_entries:
        osgc_fields.update(osgc_entry.keys())
    print('unique osgc-fields: {}'.format(osgc_fields))

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
    print('osgc-content: {}'.format(unique_field_contents(osgc_entries, 'content')))

    # read our database
    our_entries = osg.assemble_infos()
    print('{} entries with us'.format(len(our_entries)))

    # just the names
    osgc_names = set([x['name'] for x in osgc_entries])
    our_names = set([x['name'] for x in our_entries])
    common_names = osgc_names & our_names
    osgc_names -= common_names
    our_names -= common_names
    print('{} in both, {} only in osgameclones, {} only with us'.format(len(common_names), len(osgc_names),
                                                                        len(our_names)))
    # find similar names among the rest
    # print('look for similar names')
    # for osgc_name in osgc_names:
    #    for our_name in our_names:
    #        if osg.name_similarity(osgc_name, our_name) > similarity_threshold:
    #            print(' {} - {}'.format(osgc_name, our_name))

    newly_created_entries = 0
    # iterate over their entries
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

                p = ''

                # compare their lang with our code language
                if 'lang' in osgc_entry:
                    osgc_languages = osgc_entry['lang']
                    if type(osgc_languages) == str:
                        osgc_languages = [osgc_languages]
                    our_languages = our_entry['code language']  # essential field
                    p += compare_sets(osgc_languages, our_languages, 'code language')

                # compare their license with our code and assets license
                if 'license' in osgc_entry:
                    osgc_licenses = osgc_entry['license']
                    our_code_licenses = our_entry['code license']  # essential field
                    our_assets_licenses = our_entry.get('assets license', [])
                    p += compare_sets(osgc_licenses, our_code_licenses + our_assets_licenses, 'licenses', 'notthem')
                    p += compare_sets(osgc_licenses, our_code_licenses, 'licenses', 'notus')

                # compare their framework with our code dependencies (capitalization is ignored for now, only starts are compared)
                our_framework_replacements = {'allegro4': 'allegro'}
                if 'framework' in osgc_entry:
                    osgc_frameworks = osgc_entry['framework']
                    if type(osgc_frameworks) == str:
                        osgc_frameworks = [osgc_frameworks]
                    our_frameworks = our_entry.get('code dependencies', [])
                    our_frameworks = [x.casefold() for x in our_frameworks]
                    our_frameworks = [x if x not in our_framework_replacements else our_framework_replacements[x] for x
                                      in our_frameworks]
                    osgc_frameworks = [x.casefold() for x in osgc_frameworks]
                    p += compare_sets(osgc_frameworks, our_frameworks, 'framework/dependencies')

                # compare their repo with our code repository and download
                if 'repo' in osgc_entry:
                    osgc_repos = osgc_entry['repo']
                    if type(osgc_repos) == str:
                        osgc_repos = [osgc_repos]
                    osgc_repos = [utils.strip_url(url) for url in osgc_repos]
                    osgc_repos = [x for x in osgc_repos if not x.startswith(
                        'sourceforge.net/projects/')]  # we don't need the general sites there
                    # osgc_repos = [x for x in osgc_repos if not x.startswith('https://sourceforge.net/projects/')] # ignore some
                    our_repos = our_entry.get('code repository', [])
                    our_repos = [utils.strip_url(url) for url in our_repos]
                    our_repos = [x for x in our_repos if not x.startswith(
                        'gitlab.com/osgames/')]  # we do not yet spread our own deeds (but we will some day)
                    our_repos = [x for x in our_repos if
                                 'cvs.sourceforge.net' not in x and 'svn.code.sf.net/p/' not in x]  # no cvs or svn anymore
                    our_downloads = our_entry.get('download', [])
                    our_downloads = [utils.strip_url(url) for url in our_downloads]
                    p += compare_sets(osgc_repos, our_repos + our_downloads, 'repo',
                                      'notthem')  # if their repos are not in our downloads or repos
                    p += compare_sets(osgc_repos, our_repos[:1], 'repo',
                                      'notus')  # if our main repo is not in their repo

                # compare their url (and feed) to our home (and strip urls)
                if 'url' in osgc_entry:
                    osgc_urls = osgc_entry['url']
                    if type(osgc_urls) == str:
                        osgc_urls = [osgc_urls]
                    osgc_urls = [utils.strip_url(url) for url in osgc_urls]
                    our_urls = our_entry['home']
                    our_urls = [utils.strip_url(url) for url in our_urls]
                    p += compare_sets(osgc_urls, our_urls, 'url/home', 'notthem')  # if their urls are not in our urls
                    # our_urls = [url for url in our_urls if
                    #             not url.startswith('github.com/')]  # they don't have them as url
                    p += compare_sets(osgc_urls, our_urls[:1], 'url/home',
                                      'notus')  # if our first url is not in their urls

                # compare their status with our state (playable can be beta/mature with us, but not playable must be beta)
                if 'status' in osgc_entry:
                    osgc_status = osgc_entry['status']
                    our_status = our_entry['state']  # essential field
                    if osgc_status != 'playable' and 'mature' in our_status:
                        p += ' status : mismatch : them {}, us mature\n'.format(osgc_status)

                # compare their development with our state
                if 'development' in osgc_entry:
                    osgc_development = osgc_entry['development']
                    our_inactive = 'inactive' in our_entry
                    our_status = our_entry['state']  # essential field
                    if osgc_development == 'halted' and not our_inactive:
                        p += ' development : mismatch : them halted - us not inactive\n'
                    if osgc_development in ['very active', 'active'] and our_inactive:
                        p += ' development : mismatch : them {}, us inactive\n'.format(osgc_development)
                    if osgc_development == 'complete' and 'mature' not in our_status:
                        p += ' development : mismatch : them complete, us not mature\n'

                # compare their originals to our keywords (inspired by)
                our_keywords = our_entry['keywords']
                if 'originals' in osgc_entry:
                    osgc_originals = osgc_entry['originals']
                    osgc_originals = [x.replace(',', '') for x in
                                      osgc_originals]  # we cannot have ',' or parts in parentheses in original names
                    our_originals = [x for x in our_keywords if x.startswith('inspired by ')]
                    if our_originals:
                        assert len(our_originals) == 1, '{}: {}'.format(our_name, our_originals)
                        our_originals = our_originals[0][11:].split('+')
                        our_originals = [x.strip() for x in our_originals]
                    our_originals = [x for x in our_originals if x not in ['Doom II']]  # ignore same
                    p += compare_sets(osgc_originals, our_originals, 'originals')

                # compare their multiplayer with our keywords (multiplayer) (only lowercase comparison)
                if 'multiplayer' in osgc_entry:
                    osgc_multiplayer = osgc_entry['multiplayer']
                    if type(osgc_multiplayer) == str:
                        osgc_multiplayer = [osgc_multiplayer]
                    osgc_multiplayer = [x.casefold() for x in osgc_multiplayer]
                    osgc_multiplayer = [x for x in osgc_multiplayer if x not in ['competitive']]  # ignored
                    our_multiplayer = [x for x in our_keywords if x.startswith('multiplayer ')]
                    if our_multiplayer:
                        if len(our_multiplayer) != 1:
                            print(our_entry)
                            raise RuntimeError()
                        assert len(our_multiplayer) == 1
                        our_multiplayer = our_multiplayer[0][11:].split('+')
                        our_multiplayer = [x.strip().casefold() for x in our_multiplayer]
                    p += compare_sets(osgc_multiplayer, our_multiplayer, 'multiplayer')

                # compare content with keywords
                if 'content' in osgc_entry:
                    osgc_content = osgc_entry['content']
                    if isinstance(osgc_content, str):
                        osgc_content = [osgc_content]
                    p += compare_sets(osgc_content, our_keywords, 'content/keywords',
                                      'notthem')  # only to us because we have more then them

                # compare their type to our keywords
                if 'type' in osgc_entry:
                    game_type = osgc_entry['type']
                    if isinstance(game_type, str):
                        game_type = [game_type]
                    p += compare_sets(game_type, our_keywords, 'type/keywords',
                                      'notthem')  # only to us because we have more then them

                if p:
                    print('{}\n{}'.format(name, p))

        if not is_included:
            # a new entry, that we have never seen, maybe we should make an entry of our own
            # continue

            if newly_created_entries >= maximal_newly_created_entries:
                continue

            game_type = osgc_entry.get('type', None)
            osgc_status = osgc_entry.get('status', None)

            # we sort some out here (maybe we want to have a closer look at them later)
            if osgc_status == 'unplayable':
                # for now not the unplayable ones
                continue
            if 'license' not in osgc_entry or 'As-is' in osgc_entry['license']:
                # for now not the ones without license or with as-is license
                continue

            # determine file name
            print('create new entry for {}'.format(osgc_name))
            file_name = osg.canonical_entry_name(osgc_name) + '.md'
            target_file = os.path.join(constants.entries_path, file_name)
            if os.path.isfile(target_file):
                print('warning: file {} already existing, save under slightly different name'.format(file_name))
                target_file = os.path.join(constants.entries_path, file_name[:-3] + '-duplicate.md')
                if os.path.isfile(target_file):
                    continue  # just for safety reasons

            # add name
            entry = '# {}\n\n'.format(osgc_name)

            # add description
            description = '{} of {}.'.format(game_type.capitalize(), ', '.join(osgc_entry['originals']))
            entry += '_{}_\n\n'.format(description)

            # home
            home = osgc_entry.get('url', None)
            entry += '- Home: {}\n'.format(home)

            # state
            entry += '- State: {}'.format(osgc_status)
            if 'development' in osgc_entry:
                if osgc_entry['development'] == 'halted':
                    entry += ', inactive since XX'
            entry += '\n'

            # language tags
            lang = osgc_entry.get('lang', [])
            if type(lang) == str:
                lang = [lang]
            # platform 'Web' if language == JavaScript or TypeScript
            if len(lang) == 1 and lang[0] in ('JavaScript', 'TypeScript'):
                entry += '- Platform: Web\n'

            # keywords
            keywords = []
            if game_type:
                keywords.append(game_type)
            if 'originals' in osgc_entry:
                osgc_originals = osgc_entry['originals']
                if type(osgc_originals) == str:
                    osgc_originals = [osgc_originals]
                keywords.append('inspired by {}'.format(' + '.join(osgc_originals)))
            if 'multiplayer' in osgc_entry:
                osgc_multiplayer = osgc_entry['multiplayer']
                if type(osgc_multiplayer) == str:
                    osgc_multiplayer = [osgc_multiplayer]
                keywords.append('multiplayer {}'.format(' + '.join(osgc_multiplayer)))
            if 'content' in osgc_entry:
                osgc_content = osgc_entry['content']  # it's a list
                osgc_content = ', '.join(osgc_content)
                keywords.append(osgc_content)
            if keywords:
                entry += '- Keywords: {}\n'.format(', '.join(keywords))

            # code repository (mandatory on our side)
            repo = osgc_entry.get('repo', None)
            if repo and repo.startswith('https://git') and not repo.endswith('.git'):
                # we have them with .git on github/gitlab
                repo += '.git'
            entry += '- Code repository: {}\n'.format(repo)

            # code language (mandatory on our side)
            entry += '- Code language: {}\n'.format(', '.join(lang))

            # code license
            entry += '- Code license: {}\n'.format(', '.join(osgc_entry['license']))

            # code dependencies (if existing)
            if 'framework' in osgc_entry:
                osgc_frameworks = osgc_entry['framework']
                if type(osgc_frameworks) == str:
                    osgc_frameworks = [osgc_frameworks]
                entry += '- Code dependencies: {}\n'.format(', '.join(osgc_frameworks))

            # write info (if existing)
            if 'info' in osgc_entry:
                entry += '\n{}\n'.format(osgc_entry['info'])

            # write ## Building
            entry += '\n## Building\n'

            # finally write to file
            utils.write_text(target_file, entry)
            newly_created_entries += 1

    # now iterate over our entries and test if we can add anything to them
    print('entry that could be added to them')
    for our_entry in our_entries:
        our_name = our_entry['name']

        # only if contains a keyword starting with "inspired by" and not "tool", "framework" or "library"
        our_keywords = our_entry['keywords']
        if not any([x.startswith('inspired by ') for x in our_keywords]):
            continue
        if any([x in ['tool', 'library', 'framework'] for x in our_keywords]):
            continue

        is_included = False
        for osgc_entry in osgc_entries:
            osgc_name = osgc_entry['name']

            if osgc_name == our_name:
                is_included = True

        if not is_included:
            # that could be added to them
            print('- [{}]({})'.format(our_name,
                                      'https://github.com/Trilarion/opensourcegames/blob/master/entries/' + our_entry[
                                          'file']))
