"""
Tests for the validation of entries in osg._check_and_process_entry.

Each test starts from the valid sample entry (see conftest.py), breaks exactly one rule and expects a RuntimeError
with a message naming the problem.
"""

import pathlib

import pytest

from osgl import constants as c, osg, parse


def set_field(entry, field, values):
    """
    Replaces the values of a field in a raw entry (list of (field, values) pairs), or inserts the field at the
    position given by the order of valid fields if it does not exist yet.
    """
    fields = [name for name, _ in entry]
    if field in fields:
        entry[fields.index(field)] = (field, values)
        return entry
    order = list(c.valid_fields)
    position = next((index for index, name in enumerate(fields)
                     if name in order and order.index(name) > order.index(field)), len(entry))
    entry.insert(position, (field, values))
    return entry


def remove_field(entry, field):
    """
    Removes a field from a raw entry.
    """
    return [(name, values) for name, values in entry if name != field]


def set_building_field(entry, field, values):
    """
    Sets a field in the building section of a raw entry.
    """
    building = dict(entry)['Building']
    building.append((field, values))
    return entry


def check(entry):
    """
    Runs the validation on a raw entry.
    """
    return osg._check_and_process_entry(entry)


def test_valid_sample_entry(raw_sample_entry):
    """
    The unchanged sample entry passes and is converted into a dictionary.
    """
    entry = check(raw_sample_entry)
    assert entry['Title'] == 'Sample Game'
    assert entry['Building'] == {'Build system': ['CMake']}


def test_file_name_with_number_suffix_is_allowed(raw_sample_entry):
    """
    Duplicate canonical names may be resolved with a -X suffix in the file name.
    """
    entry = set_field(raw_sample_entry, 'File', pathlib.Path('sample_game-2.md'))
    check(entry)


# Field structure


def test_field_in_wrong_order(raw_sample_entry):
    """
    Fields must appear in the order of the valid fields.
    """
    entry = remove_field(raw_sample_entry, 'State')
    entry.insert(2, ('State', ['beta']))  # before Home
    with pytest.raises(RuntimeError, match='either misspelled or in wrong order'):
        check(entry)


def test_misspelled_field(raw_sample_entry):
    """
    Unknown field names are rejected.
    """
    entry = [('Homepage', values) if name == 'Home' else (name, values) for name, values in raw_sample_entry]
    with pytest.raises(RuntimeError, match='Field "Homepage" either misspelled or in wrong order'):
        check(entry)


def test_duplicate_field(raw_sample_entry):
    """
    A field must not appear twice.
    """
    index = [name for name, _ in raw_sample_entry].index('Home')
    raw_sample_entry.insert(index + 1, ('Home', ['https://example.com/']))
    with pytest.raises(RuntimeError, match='Field "Home" appears twice'):
        check(raw_sample_entry)


def test_missing_essential_field(raw_sample_entry):
    """
    Essential fields must be present.
    """
    entry = remove_field(raw_sample_entry, 'Home')
    with pytest.raises(RuntimeError, match='Essential property "Home" missing'):
        check(entry)


def test_invalid_building_field(raw_sample_entry):
    """
    Only valid building fields may be used in the building section.
    """
    entry = set_building_field(raw_sample_entry, 'Build tool', ['Make'])
    with pytest.raises(RuntimeError, match='Building field "Build tool" invalid'):
        check(entry)


def test_duplicate_building_field(raw_sample_entry):
    """
    A field must not appear twice in the building section.
    """
    entry = set_building_field(raw_sample_entry, 'Build system', ['Make'])
    with pytest.raises(RuntimeError, match='Field "Build system" appears twice'):
        check(entry)


def test_file_name_not_canonical(raw_sample_entry):
    """
    The file name must be derived from the title.
    """
    entry = set_field(raw_sample_entry, 'File', pathlib.Path('other_name.md'))
    with pytest.raises(RuntimeError, match='File name should be sample_game.md'):
        check(entry)


# Field contents


@pytest.mark.parametrize('field, value', [
    ('Inspiration', 'Master of Orion'),
    ('Play', 'https://example.org/play'),
    ('Platform', 'Windows'),
    ('Code dependency', 'SDL2'),
])
def test_comment_in_field_without_comments(raw_sample_entry, field, value):
    """
    Some fields must not have comments.
    """
    entry = set_field(raw_sample_entry, field, [parse.Value(value, 'some comment')])
    with pytest.raises(RuntimeError, match=f'field without comments {field} has comment'):
        check(entry)


def test_unknown_state(raw_sample_entry):
    """
    Only beta, mature and inactive since are valid states.
    """
    entry = set_field(raw_sample_entry, 'State', ['alpha'])
    with pytest.raises(RuntimeError, match='Unknown state "alpha"'):
        check(entry)


@pytest.mark.parametrize('state', [['beta', 'mature'], ['inactive since 2020']])
def test_state_must_be_either_beta_or_mature(raw_sample_entry, state):
    """
    The state must contain exactly one of beta and mature.
    """
    entry = set_field(raw_sample_entry, 'State', state)
    with pytest.raises(RuntimeError, match='State must be one of'):
        check(entry)


def test_url_without_valid_prefix(raw_sample_entry):
    """
    URLs must start with a known prefix.
    """
    entry = set_field(raw_sample_entry, 'Home', ['www.example.org'])
    with pytest.raises(RuntimeError, match='URL "www.example.org" in field "Home" is not a valid URL'):
        check(entry)


def test_url_in_angle_brackets_is_allowed(raw_sample_entry):
    """
    URLs may be enclosed in angle brackets.
    """
    entry = set_field(raw_sample_entry, 'Home', ['<https://example.org/>'])
    check(entry)


def test_repository_without_https(raw_sample_entry):
    """
    GitHub, GitLab, ... repositories must use https.
    """
    entry = set_field(raw_sample_entry, 'Code repository', ['http://github.com/example/sample.git'])
    with pytest.raises(RuntimeError, match='should start with https://'):
        check(entry)


def test_repository_without_git_suffix(raw_sample_entry):
    """
    GitHub, GitLab, ... repositories must end on .git.
    """
    entry = set_field(raw_sample_entry, 'Code repository', ['https://github.com/example/sample'])
    with pytest.raises(RuntimeError, match='should end on .git'):
        check(entry)


@pytest.mark.parametrize('platforms', [['Linux', 'Windows'], ['Amiga']])
def test_invalid_platforms(raw_sample_entry, platforms):
    """
    Platforms must be known and given in the order of the valid platforms.
    """
    entry = set_field(raw_sample_entry, 'Platform', platforms)
    with pytest.raises(RuntimeError, match='either misspelled or in wrong order'):
        check(entry)


def test_valid_platforms(raw_sample_entry):
    """
    Known platforms in the right order are accepted.
    """
    entry = set_field(raw_sample_entry, 'Platform', ['Windows', 'Linux', 'Web'])
    check(entry)


def test_no_keyword(raw_sample_entry):
    """
    At least one keyword is required.
    """
    entry = set_field(raw_sample_entry, 'Keyword', [])
    with pytest.raises(RuntimeError, match='Need at least one keyword'):
        check(entry)


def test_no_recommended_keyword(raw_sample_entry):
    """
    At least one of the recommended keywords is required.
    """
    entry = set_field(raw_sample_entry, 'Keyword', ['2D'])
    with pytest.raises(RuntimeError, match='Entry contains no recommended keywords'):
        check(entry)


def test_remake_or_clone_is_not_recommended(raw_sample_entry):
    """
    The keyword for remakes and clones alone is not enough, a genre (recommended keyword) is still needed.
    """
    entry = set_field(raw_sample_entry, 'Keyword', ['remake or clone'])
    with pytest.raises(RuntimeError, match='Entry contains no recommended keywords'):
        check(entry)


@pytest.mark.parametrize('keyword', ['remake', 'clone'])
def test_obsolete_keyword(raw_sample_entry, keyword):
    """
    The former keywords remake and clone are rejected in favor of the merged keyword.
    """
    entry = set_field(raw_sample_entry, 'Keyword', ['strategy', keyword])
    with pytest.raises(RuntimeError, match=f'Obsolete keyword\\(s\\) {keyword}'):
        check(entry)


def test_unknown_language(raw_sample_entry):
    """
    Code languages must be known.
    """
    entry = set_field(raw_sample_entry, 'Code language', ['Klingon'])
    with pytest.raises(RuntimeError, match='Language "Klingon" is not a known code language'):
        check(entry)


def test_unknown_license(raw_sample_entry):
    """
    Code licenses must be known.
    """
    entry = set_field(raw_sample_entry, 'Code license', ['Klingon License'])
    with pytest.raises(RuntimeError, match='License "Klingon License" is not a known license'):
        check(entry)


@pytest.mark.parametrize('name, problem', [('\u202e', 'has no visible character'),
                                           ('Jane\xa0Doe', 'invisible or special space characters')])
def test_invalid_developer_name(raw_sample_entry, name, problem):
    """
    Developer names must have a visible character and must not contain invisible or special space characters.
    """
    entry = set_field(raw_sample_entry, 'Developer', ['Jane Doe', name])
    with pytest.raises(RuntimeError, match=problem):
        check(entry)
