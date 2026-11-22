"""
Tests for the Lark based parsing of entries (grammars/entries.lark and osgl.parse).
"""

import lark
import pytest

from osgl import parse


def test_sample_entry_fields(parse_entry, sample_entry_text):
    """
    The sample entry is parsed into (field, values) pairs in the order of the file.
    """
    entry = dict(parse_entry(sample_entry_text))
    assert entry['Title'] == 'Sample Game'
    assert entry['Home'] == ['https://example.org/']
    assert entry['State'] == ['beta', 'inactive since 2020']
    assert entry['Keyword'] == ['strategy', 'remake or clone']
    assert entry['Note'] == 'A short note about the game.'


def test_comment_becomes_value_with_comment(parse_entry, sample_entry_text):
    """
    A value followed by a comment in parentheses is returned as parse.Value carrying the comment.
    """
    entry = dict(parse_entry(sample_entry_text))
    repository = entry['Code repository'][0]
    assert isinstance(repository, parse.Value)
    assert repository == 'https://github.com/example/sample.git'
    assert repository.comment == '@created 2018, @stars 27'


def test_quoted_value_may_contain_comma(parse_entry, sample_entry_text):
    """
    Quoted values may contain commas, the quotes are removed.
    """
    entry = dict(parse_entry(sample_entry_text))
    assert entry['Developer'] == ['Jane Doe', 'Studio, Inc.']


def test_building_section(parse_entry, sample_entry_text):
    """
    The building section is returned as nested list of properties.
    """
    entry = dict(parse_entry(sample_entry_text))
    assert dict(entry['Building']) == {'Build system': ['CMake']}


def test_missing_title_is_rejected(parse_entry, sample_entry_text):
    """
    An entry without the leading title line does not conform to the grammar.
    """
    text = sample_entry_text.split('\n', 2)[2]  # remove title and empty line
    with pytest.raises(lark.exceptions.LarkError):
        parse_entry(text)
