"""
Everything specific to search in Wikipedia.
Using https://github.com/goldsmith/Wikipedia
"""

import wikipedia


def search(search_term, results=3):
    """

    :param search_term:
    :param max_results:
    :return:
    """
    return wikipedia.search(search_term, results=results)