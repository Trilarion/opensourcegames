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
    ('LÖVE', 'love'),
    ('Straße', 'strasse'),
    ('Dragon History - Dračí Historie', 'dragon_history-draci_historie'),
    ('Adrián López', 'adrian_lopez'),
    ('Łukasz Jørgensen', 'lukasz_jorgensen'),
    ('Jazz² Resurrection', 'jazz_resurrection'),
    ('Just another Tetris™ clone', 'just_another_tetris_clone'),
    ('Pacman 吃豆游戏', 'pacman_'),
])
def test_canonical_name(name, expected):
    """
    Canonical names are lower case, without special characters and with underscores instead of spaces.
    """
    assert osg.canonical_name(name) == expected



@pytest.mark.parametrize('name, expected', [
    ('Jane Doe', 'Jane Doe'),
    ('\u202e', ''),
    ('\u202ePhilihp Busby', 'Philihp Busby'),
    ('yui\u200b', 'yui'),
    ('Paweł\xa0Fertyk', 'Paweł Fertyk'),
    ('Erin\u2004Yuki\u2009Schlarb', 'Erin Yuki Schlarb'),
    ('  Dale  Harvey ', 'Dale Harvey'),
    ('Tab\tName', 'Tab Name'),
    ('Soft\xadhyphen', 'Softhyphen'),
    ('Cafe\u0301', 'Café'),
    ('Алексей', 'Алексей'),
    ('南门阳德', '南门阳德'),
    ('\u3000刘敏\u3000', '刘敏'),
])
def test_normalize_developer_name(name, expected):
    """
    Invisible characters are removed, spaces normalized and the name NFC normalized, other characters are kept.
    """
    assert osg.normalize_developer_name(name) == expected


@pytest.mark.parametrize('name, valid', [
    ('Jane Doe', True),
    ('Алексей', True),
    ('k\u0337e\u0336rnel', True),
    ('\u202e', False),
    ('', False),
    (' ', False),
    ('yui\u200b', False),
    ('Paweł\xa0Fertyk', False),
    ('Dale  Harvey', False),
    ('Cafe\u0301', False),
])
def test_check_developer_name(name, valid):
    """
    Only names that are already normalized and have a visible character are valid.
    """
    assert (osg.check_developer_name(name) is None) == valid

@pytest.mark.parametrize('text, expected', [
    ('https://example.org', True),
    ('git://example.org/repo.git', True),
    ('svn://svn.example.org/trunk', True),
    ('http://cvs.savannah.nongnu.org:/sources/example', True),
    ('https://en.wikipedia.org/wiki/Example_(game)', True),
    ('https://example.org with space', False),
    ('example.org', False),
    ('https://', False),
    ('https://)', False),
    ('http:/example.org', False),
    ('https://example.org/<path>', False),
    ('mailto://example.org', False),
])
def test_is_url(text, expected):
    """
    Only strings with a known prefix, a plausible host and without whitespace or <>" are URLs.
    """
    assert osg.is_url(text) == expected


@pytest.mark.parametrize('text, expected', [
    ('https://example.org', ['https://example.org']),
    ('see https://example.org, and more', ['https://example.org']),
    ('https://example.org (https://github.com/example, @stars 3)', ['https://example.org', 'https://github.com/example']),
    ('(see also https://example.org/page.html)', ['https://example.org/page.html']),
    ('a link <https://example.org/a> here', ['https://example.org/a']),
    ('[Notes](https://example.org/readme#notes).', ['https://example.org/readme#notes']),
    ('https://en.wikipedia.org/wiki/Example_(game)', ['https://en.wikipedia.org/wiki/Example_(game)']),
    ('[Game](https://en.wikipedia.org/wiki/Example_(game))', ['https://en.wikipedia.org/wiki/Example_(game)']),
    ('git://example.org/a.git svn://example.org/b', ['git://example.org/a.git', 'svn://example.org/b']),
    ('https://web.archive.org/web/2018/http://example.org/', ['https://web.archive.org/web/2018/http://example.org/']),
    ('https://a.org\nhttps://b.org\nhttps://a.org', ['https://a.org', 'https://b.org', 'https://a.org']),
    ('Port: https://example.org.', ['https://example.org']),
    ('https://en.wikipedia.org/wiki/Yo_Frankie!', ['https://en.wikipedia.org/wiki/Yo_Frankie!']),
    ('https://web.archive.org/web/*/https://example.org/files/*', ['https://web.archive.org/web/*/https://example.org/files/*']),
    ('no url here, only http:// and example.org', []),
])
def test_extract_urls(text, expected):
    """
    URLs are found anywhere in a text, without trailing punctuation or unbalanced closing parentheses.
    """
    assert osg.extract_urls(text) == expected


def test_all_urls_ignores_notes():
    """
    Only the URL fields (with the comments of their values) count, not the notes or other fields.
    """
    entry = {
        'File': 'example.md',
        'Home': [parse.Value('https://example.org', 'https://web.archive.org/web/2018/https://example.org')],
        'Media': ['https://en.wikipedia.org/wiki/Chromium_B.S.U.'],
        'Code repository': ['https://github.com/example/example.git', 'https://github.com/example/example.git',
                            'https://gitlab.com/example/old.git @archive'],
        'Code license': [parse.Value('GPL-3.0', 'https://example.org/license')],
        'Note': 'Port to Android: https://github.com/other/port\n',
    }
    assert osg.all_urls([entry]) == {
        'https://example.org': ['example.md'],
        'https://web.archive.org/web/2018/https://example.org': ['example.md'],
        'https://en.wikipedia.org/wiki/Chromium_B.S.U.': ['example.md'],
        'https://github.com/example/example.git': ['example.md'],
        'https://gitlab.com/example/old.git': ['example.md'],
    }


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


@pytest.mark.parametrize('name, inspired_entries, expected', [
    ('Original', ['Clone'], True),  # an entry has the name of the inspiration
    ('Original', ['Original', 'Clone'], False),  # the entry of the same name is inspired by it (open source release)
    ('Unknown', ['Clone'], False),  # no entry has the name of the inspiration
])
def test_is_included_inspiration(name, inspired_entries, expected):
    """
    An inspiration is included if an entry has its name and that entry is not inspired by it.
    """
    inspiration = {'Name': name, 'Inspired entries': inspired_entries}
    assert osg.is_included_inspiration(inspiration, {'Original', 'Clone'}) is expected
