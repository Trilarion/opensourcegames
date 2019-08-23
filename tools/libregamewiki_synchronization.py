"""
Once data from libregamewiki is imported, synchronize with our database, i.e. identify the entries both have in common,
estimate the differences in the entries both have in common, suggest to add the entries they have not in common to each
other.

unique imported fields: 'assets license', 'categories', 'code language', 'code license', 'developer', 'engine', 'genre', 'library', 'linux-packages', 'name', 'platform'
"""

import json
from utils.utils import *


def get_unique_field_content(field, entries):
    """

    """
    unique_content = set()
    for entry in entries:
        if field in entry:
            unique_content.update(entry[field])
    return sorted(list(unique_content))

platform_replacements = {'Mac': 'macOS'}

if __name__ == "__main__":

    # import lgw import
    json_path = os.path.join(os.path.dirname(__file__), 'lgw_import.json')
    text = read_text(json_path)
    lgw_entries = json.loads(text)

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