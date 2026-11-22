"""
Tests for helper functions in osgl.osg that do not need the database.
"""

import pytest

from osgl import osg, parse


@pytest.mark.parametrize('name, expected', [
    ('0 A.D.', '0_ad'),
    ('1255 Burgomaster', '1255_burgomaster'),
    ('Master of Orion', 'master_of_orion'),
    ('Jörmungandr', 'jormungandr'),
])
def test_canonical_name(name, expected):
    """
    Canonical names are lower case, without special characters and with underscores instead of spaces.
    """
    assert osg.canonical_name(name) == expected


@pytest.mark.parametrize('text, expected', [
    ('https://example.org', True),
    ('git://example.org/repo.git', True),
    ('https://example.org with space', False),
    ('example.org', False),
])
def test_is_url(text, expected):
    """
    Only strings with a known prefix and without spaces are URLs.
    """
    assert osg.is_url(text) == expected


def test_repository_type_detection():
    """
    Git, svn and hg repositories are recognized by their URLs.
    """
    assert osg.get_git_repo('https://github.com/example/sample.git') is not None
    assert osg.get_git_repo('https://example.org/') is None
    assert osg.get_svn_repo('svn://example.org/trunk') is not None
    assert osg.get_hg_repo('http://hg.example.org/repo') is not None
    assert osg.get_hg_repo('https://bitbucket.org/example/repo.git') is None


def test_inactive_year():
    """
    The year of inactivity is extracted from the state field.
    """
    assert osg.is_inactive({'State': ['mature', 'inactive since 2024']})
    assert osg.extract_inactive_year({'State': ['mature', 'inactive since 2024']}) == 2024
    assert osg.extract_inactive_year({'State': ['beta']}) is None


def test_render_value():
    """
    Values with commas are quoted and comments are added in parentheses.
    """
    assert osg.render_value('C') == 'C'
    assert osg.render_value('Some, Language') == '"Some, Language"'
    assert osg.render_value(parse.Value('https://example.org', '@stars 3')) == 'https://example.org (@stars 3)'
