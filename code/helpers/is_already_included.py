"""
Checks a list of game names (comma separated in text file) if they are already included in the database.
Is fuzzy, i.e. accepts a certain similarity of names.
"""

import json
import re
from difflib import SequenceMatcher
from utils.utils import *


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


if __name__ == "__main__":
    similarity_threshold = 0.7

    root_path = os.path.realpath(os.path.dirname(__file__) / os.path.pardir)

    # read docs/data.json
    data_file = root_path / 'docs', 'data.json'
    text = read_text(data_file)
    data = json.loads(text)

    # extract game names
    data = data['data']
    data = (x[0] for x in data)
    existing_names = list(re.sub(r' \([^)]*\)', '', x) for x in data)

    # read names to test
    test_file = root_path / 'is_already_included.txt'
    text = read_text(test_file)
    test_names = text.split(', ')

    # loop over all test names
    for test_name in test_names:
        matches = []
        # loop over all existing names
        for existing_name in existing_names:
            s = similarity(test_name.lower(), existing_name.lower())
            if s > similarity_threshold:
                matches.append('{} ({:.2f})'.format(existing_name, s))
        # were matches found
        if matches:
            print('{} maybe included in {}'.format(test_name, ', '.join(matches)))
        else:
            print('{} not included'.format(test_name))
