"""
Consistency checks of the definitions in osgl.constants and tests of the local configuration access.
"""

import collections
import configparser

import pytest

from osgl import constants as c


# licenses that intentionally (or for now) have no link
LICENSES_WITHOUT_URL = {'Custom', 'None', 'NPOSL-3.0', 'Proprietary', 'SWIG license', '?'}


def duplicates(values):
    """
    Returns the values that occur more than once.
    """
    return [value for value, count in collections.Counter(values).items() if count > 1]


@pytest.mark.parametrize('name', [
    'essential_fields', 'valid_properties', 'valid_fields', 'valid_platforms', 'recommended_keywords',
    'interesting_keywords', 'known_languages', 'known_licenses', 'valid_multiplayer_modes', 'valid_annotation',
    'ignored_code_dependencies', 'entries_without_developers',
])
def test_no_duplicates(name):
    """
    The tuples of valid or known values do not contain duplicates.
    """
    assert duplicates(getattr(c, name)) == []


def test_essential_fields_are_valid_and_ordered():
    """
    Essential fields are valid fields and given in the order of the valid fields.
    """
    positions = [c.valid_fields.index(field) for field in c.essential_fields]
    assert positions == sorted(positions)


def test_licenses_have_urls():
    """
    Every known license has a link, except a few known ones.
    """
    missing = {license for license in c.known_licenses if license not in c.license_urls}
    assert missing == LICENSES_WITHOUT_URL


def test_get_license_url_unknown_license():
    """
    Asking for the link of an unknown license is an error.
    """
    with pytest.raises(RuntimeError, match='Unknown license'):
        c.get_license_url('Klingon License')


def test_languages_have_urls():
    """
    Every known language (except the placeholders) has a link.
    """
    assert set(c.known_languages) - set(c.language_urls) == {'None', '?'}


def test_non_game_keywords_are_recommended():
    """
    The non-game keywords are part of the recommended keywords.
    """
    assert set(c.non_game_keywords) <= set(c.recommended_keywords)


def test_recommended_keywords_have_descriptions():
    """
    Every recommended keyword except library has a description for the website.
    """
    assert set(c.recommended_keywords) - set(c.keyword_genre_descriptions) == {'library'}


def test_remake_or_clone_keyword():
    """
    The merged keyword for remakes and clones is an interesting but not a recommended keyword, has a description and
    replaces the obsolete keywords.
    """
    assert c.remake_or_clone_keyword not in c.recommended_keywords
    assert c.remake_or_clone_keyword in c.interesting_keywords
    assert c.remake_or_clone_keyword in c.keyword_genre_descriptions
    for keyword in c.obsolete_keywords:
        assert keyword not in c.recommended_keywords
        assert keyword not in c.interesting_keywords
        assert keyword not in c.keyword_genre_descriptions


# Local configuration


@pytest.fixture
def local_config(tmp_path, monkeypatch):
    """
    Redirects the local config to a temporary file and returns a function that writes and loads its content.
    """
    file = tmp_path / 'local-config.ini'
    monkeypatch.setattr(c, 'local_config_file', file)
    config = configparser.ConfigParser()
    monkeypatch.setattr(c, 'config', config)

    def write(content):
        """
        Writes the config file and reads it into the redirected config parser.
        """
        file.write_text(content, encoding='utf-8')
        config.read(file)

    return write


def test_get_config(local_config):
    """
    Values are read from the [general] section.
    """
    local_config('[general]\narchive-folder = D:\\archive\n')
    assert c.get_config('archive-folder') == 'D:\\archive'


def test_get_config_missing_file(local_config):
    """
    A missing config file is reported.
    """
    with pytest.raises(RuntimeError, match='not found'):
        c.get_config('archive-folder')


@pytest.mark.parametrize('content, message', [
    ('[other]\nkey = value\n', 'has no \\[general\\] section'),
    ('[general]\nother = value\n', 'is missing or empty'),
    ('[general]\narchive-folder =\n', 'is missing or empty'),
])
def test_get_config_invalid(local_config, content, message):
    """
    A missing section, a missing key or an empty value is reported.
    """
    local_config(content)
    with pytest.raises(RuntimeError, match=message):
        c.get_config('archive-folder')
