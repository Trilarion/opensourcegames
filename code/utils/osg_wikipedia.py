"""
Everything specific to search in Wikipedia.
Using https://github.com/goldsmith/Wikipedia
"""

import wikipedia
from typing import Any

wikipedia.set_lang('en')  # just in case that isn't so already


def search(search_term: str, results: int = 3) -> list[str]:
    """
    Performs a search on Wikipedia and delivers an amount of results
    """
    return wikipedia.search(search_term, results=results)


def pages(titles: list[str]) -> list[Any]:
    """
    Retrieves pages from wikipedia (only exact matches to titles?)
    """
    pages_list: list[Any] = []
    for title in titles:
        try:
            page = wikipedia.page(title, auto_suggest=False)
        except wikipedia.exceptions.DisambiguationError:
            continue  # here we silently eat the exception
        pages_list.append(page)
    return pages_list
