"""
Maintenance of inspirations.md and synchronization with the inspirations in the entries.
"""

import time
from utils import constants as c, utils, osg, osg_ui


def duplicate_check():
    """

    :param inspirations:
    :return:
    """
    print('\nduplicate check')
    inspiration_names = [x['name'] for x in inspirations]
    for index, name in enumerate(inspiration_names):
        for other_name in inspiration_names[index+1:]:
            if osg.name_similarity(name, other_name) > similarity_threshold:
                print(' {} - {} is similar'.format(name, other_name))


if __name__ == "__main__":

    similarity_threshold = 0.8

    # load inspirations
    inspirations = osg.read_inspirations_info()
    print('{} inspirations in the inspirations database'.format(len(inspirations)))
    osg.write_inspirations_info(inspirations)  # write again just to check integrity

    #osg_ui.run_simple_button_app('Maintenance inspirations', (('Duplicate check', duplicate_check),))



    # assemble info
    t0 = time.process_time()
    entries = osg.read_entries()
    print('took {}s'.format(time.process_time()-t0))
    t0 = time.process_time()
    # entries = osg.assemble_infos()
    osg.write_entries(entries)
    print('took {}s'.format(time.process_time()-t0))


    # assemble inspirations info from entries
    entries_inspirations = {}
    for entry in entries:
        entry_name = entry['name']
        keywords = entry['keywords']
        entry_inspirations = [x for x in keywords if x.startswith('inspired by')]
        if entry_inspirations:
            entry_inspirations = entry_inspirations[0][len('inspired by'):]
            entry_inspirations = entry_inspirations.split('+')
            entry_inspirations = [x.strip() for x in entry_inspirations]
            for entry_inspiration in entry_inspirations:
                if entry_inspiration in entries_inspirations:
                    entries_inspirations[entry_inspiration].append(entry_name)
                else:
                    entries_inspirations[entry_inspiration] = [ entry_name ]
    print('{} inspirations in the entries'.format(len(entries_inspirations)))

    # first check if all inspiration in entries are also in inspirations
    inspiration_names = [x['name'] for x in inspirations]
    for inspiration, entries in entries_inspirations.items():
        if inspiration not in inspiration_names:
            print('new inspiration {} for games {}'.format(inspiration, ', '.join(entries)))
            similar_names = [x for x in inspiration_names if osg.name_similarity(inspiration, x) > 0.8]
            if similar_names:
                print(' similar names {}'.format(', '.join(similar_names)))

    # now the other way around
    for index, name in enumerate(inspiration_names):
        if name not in entries_inspirations:
            print('potential removed inspiration {} from games {}'.format(name, inspirations[index]['inspired entries']))
            similar_names = [x for x in entries_inspirations.keys() if osg.name_similarity(name, x) > 0.8]
            if similar_names:
                print(' similar names {}'.format(', '.join(similar_names)))