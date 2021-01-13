"""
Everything specific to search in Wikipedia.
Using https://github.com/goldsmith/Wikipedia
"""

import wikipedia
wikipedia.set_lang('en') # just in case that isn't so already


def search(search_term, results=3):
    """

    :param search_term:
    :param max_results:
    :return:
    """
    return wikipedia.search(search_term, results=results)


def pages(titles):
    pages = []
    for title in titles:
        page = wikipedia.page(title, auto_suggest=False)
        pages.append(page)
    return pages
