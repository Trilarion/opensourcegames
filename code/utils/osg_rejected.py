"""
Handling of rejected file information.
"""

import re
from utils import constants as c, utils as u

matcher = re.compile(r'(.*)? \((.*)?\): (.*)')  # general structure: name (link, link): description


def read_rejected_file() -> list[dict[str, str | list[str]]]:
    """
    Read list of rejected games information.
    Uses very simple parsing.
    :return: List of dictionaries with keys: Title, URLs, Description
    """
    text = u.read_text(c.rejected_file)
    rejected: list[dict[str, str | list[str]]] = []
    for line in text.split('\n'):
        # print(line)
        matches = matcher.findall(line)[0]  # we know there will be exactly one match on every line
        name = matches[0].strip()
        links = matches[1].split(',')
        links = [link.strip() for link in links]
        description = matches[2].strip()
        rejected.append({'Title': name, 'URLs': links, 'Description': description})
    return rejected


def write_rejected_file(rejected: list[dict[str, str | list[str]]]) -> None:
    """
    Write list of rejected entries to file.
    Sorts by title.
    :param rejected: List of dictionaries with keys: Title, URLs, Description
    """
    # sort by name
    rejected.sort(key=lambda x: str.casefold(x['Title']))
    # expand single items
    rejected_text = [f"{item['Title']} ({', '.join(item['URLs'])}): {item['Description']}" for item in rejected]
    # join with newlines
    rejected_str = '\n'.join(rejected_text)
    # write to file
    u.write_text(c.rejected_file, rejected_str)