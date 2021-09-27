"""
Handling of rejected file information.
"""

import os
import re
from utils import constants as c, utils as u

matcher = re.compile(r'(.*)? \((.*)?\): (.*)')  # general structure: name (link, link): description


def read_rejected_file():
    """

    :return:
    """
    rejected_file = os.path.join(c.root_path, 'code', 'rejected.txt')
    text = u.read_text(rejected_file)
    rejected = []
    for line in text.split('\n'):
        print(line)
        matches = matcher.findall(line)[0]  # we know there will be exactly one match on every line
        name = matches[0].strip()
        links = matches[1].split(',')
        links = [link.strip() for link in links]
        description = matches[2].strip()
        rejected.append({'Title': name, 'URLs': links, 'Description': description})
    return rejected


def write_rejected_file(rejected):
    """

    :param rejected:
    """
    # sort by name
    rejected.sort(key=lambda x: str.casefold(x[0]))
    # expand single items
    rejected = ['{} ({}): {}'.format(item[0], ', '.join(item[1]), item[2]) for item in rejected]
    # join with newlines
    rejected = '\n'.join(rejected)
    # write to file
    rejected_file = os.path.join(c.root_path, 'code', 'rejected.txt')
    u.write_text(rejected_file, rejected)