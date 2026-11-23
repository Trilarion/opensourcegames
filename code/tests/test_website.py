"""
Tests for the static website generator (osgl.website.generate): helper functions and a complete generation run
into a temporary folder.
"""

import json

import pytest

from osgl import constants as c, osg, parse
from osgl.website import generate as g


# Helpers


def test_get_plural_or_singular():
    """
    Singular for one, configured plural otherwise, unknown names are an error.
    """
    assert g.get_plural_or_singular('Developer', 1) == 'Developer'
    assert g.get_plural_or_singular('Developer', 2) == 'Developers'
    assert g.get_plural_or_singular('Code repository', 3) == 'Code repositories'
    assert g.get_plural_or_singular('Media', 0) == 'Media'
    with pytest.raises(RuntimeError, match='not a known singular'):
        g.get_plural_or_singular('Spaceship', 2)


def test_file_hash_ignores_build_date():
    """
    Lines with the build date do not change the hash, other changes do.
    """
    text = '<p>\n  This website is built {}\n</p>'
    assert g.file_hash(text.format('today')) == g.file_hash(text.format('yesterday'))
    assert g.file_hash('<p>a</p>') != g.file_hash('<p>b</p>')


@pytest.mark.parametrize('current, target, expected', [
    ([], ['games', 'A.html'], 'games/A.html'),
    (['games'], ['games', 'A.html'], 'A.html'),
    (['games'], ['index.html'], '../index.html'),
    (['games'], ['developers', 'B.html#x'], '../developers/B.html#x'),
    (['games'], 'https://example.org', 'https://example.org'),
    ([], 'index.html', 'index.html'),
])
def test_url_to(current, target, expected):
    """
    Relative links are created from the folder of the current page, absolute links stay unchanged.
    """
    assert g.url_to(current, target) == expected


def test_sort_into_categories():
    """
    Items can be in several categories, items in no category go into the unknown category.
    """
    result = g.sort_into_categories([1, 2, 3, 4], ['even', 'small'],
                                    lambda item, category: item % 2 == 0 if category == 'even' else item < 3,
                                    'other')
    assert result == {'even': [2, 4], 'small': [1, 2], 'other': [3]}


def test_divide_in_three_columns_and_transform():
    """
    Each category is transformed and split into three nearly equal columns.
    """
    result = g.divide_in_three_columns_and_transform({'A': [1, 2, 3, 4], 'B': []}, lambda x: x * 10)
    assert result['number_entries'] == {'A': 4, 'B': 0}
    assert result['entries'] == {'A': [[10, 20], [30], [40]], 'B': [[], [], []]}


def test_preprocess():
    """
    Items get unique anchors, an alphabetical letter (with replacements) and a link.
    """
    items = [{'Name': 'Alpha'}, {'Name': 'alpha'}, {'Name': 'Ølfred'}, {'Name': '2048'}, {'Name': 'Ätsch'}]
    g.preprocess(items, 'Name', ['developers'])
    assert [item['anchor-id'] for item in items] == ['alpha', 'alphax', 'olfred', '2048', 'atsch']
    assert [item['letter'] for item in items] == ['A', 'A', '0', '0', 'A']
    assert items[0]['href'] == ['developers', 'A.html#alpha']


@pytest.mark.parametrize('url, expected_icon, expected_text', [
    ('https://github.com/example/sample/', 'github', 'example/sample'),
    ('https://gitlab.com/example/sample', 'gitlab', 'example/sample'),
    ('https://sourceforge.net/projects/sample', 'sourceforge', 'sample'),
    ('https://web.archive.org/web/2020/https://example.org', 'library', '2020/https://example.org'),
    ('https://en.wikipedia.org/wiki/Sample', 'wikipedia', 'Sample Game'),
])
def test_shortcut_url_known_services(url, expected_icon, expected_text):
    """
    Known services are shown with an icon and a shortened text.
    """
    icon, text = g.shortcut_url(url, 'Sample Game')
    assert icon['id'] == expected_icon
    assert text['text'] == expected_text


def test_shortcut_url_other():
    """
    Other URLs only lose their scheme.
    """
    assert g.shortcut_url('https://example.org/', 'x') == 'example.org'
    assert g.shortcut_url('ftp://example.org', 'x') == 'ftp://example.org'


@pytest.mark.parametrize('stars, icon', [(500, 'star'), (100, 'star-half-full'), (5, 'star-o')])
def test_make_repo_url_with_comments(stars, icon):
    """
    Repository comments are shown as creation year and a star rating icon.
    """
    repo = parse.Value('https://github.com/example/sample.git', f'@created 2018, @stars {stars}, @archived')
    node = g.make_repo_url(repo, 'Sample')
    url, enclosed = node['entries']
    assert url['href'] == repo
    comments = enclosed['entry']['entries']
    assert comments[0] == g.make_text('since 2018')
    assert comments[1]['id'] == icon
    assert comments[2] == g.make_text('archived')


def test_make_repo_url_without_comments():
    """
    Without comments only the link is returned.
    """
    node = g.make_repo_url('https://example.org/repo.git', 'Sample')
    assert node['type'] == 'url'


@pytest.mark.parametrize('link, href', [
    ('someone@GH', 'https://github.com/someone'),
    ('someone@GL', 'https://gitlab.com/someone'),
    ('someone@SF', 'https://sourceforge.net/u/someone/profile/'),
    ('someone@BB', 'https://bitbucket.org/someone/'),
])
def test_developer_profile_link(link, href):
    """
    Contact shortcuts are converted into profile links.
    """
    assert g.developer_profile_link(link)['href'] == href


def test_developer_profile_link_unknown():
    """
    Unknown contact shortcuts are an error.
    """
    with pytest.raises(RuntimeError, match='Unknown profile link'):
        g.developer_profile_link('someone@XX')


@pytest.mark.parametrize('keyword, icons, title', [
    ('content open', ['lock_open'], c.keyword_genre_descriptions['content open']),
    ('content free', ['lock_open'], c.keyword_genre_descriptions['content free']),
    ('content commercial', ['attach_money'], c.keyword_genre_descriptions['content commercial']),
    ('content commercial + original required', ['attach_money', 'attach_money'], None),
    ('content open (?)', ['lock_open'], f"{c.keyword_genre_descriptions['content open']} (uncertain)"),
    ('content commercial (?)', ['attach_money'], f"{c.keyword_genre_descriptions['content commercial']} (uncertain)"),
    ('multiplayer', ['users'], 'Multiplayer'),
    ('multiplayer online + LAN', ['users'], 'Multiplayer: online, LAN'),
])
def test_create_keyword_tag_icons(keyword, icons, title):
    """
    Content and multiplayer keywords are shown as icon tags with a tooltip and the keyword as hidden text.
    """
    tag = g.create_keyword_tag(keyword)
    assert tag['type'] == 'icon-tag'
    assert tag['icons'] == icons
    assert tag['text'] == keyword
    if title:
        assert tag['title'] == title


@pytest.mark.parametrize('keyword', ['content swappable', 'content none', 'content open + non-commercial', 'multiplayers'])
def test_create_keyword_tag_icon_fallback(keyword):
    """
    Rare content variants (and keywords only starting like multiplayer) stay text tags.
    """
    assert g.create_keyword_tag(keyword)['type'] == 'text'


def test_keyword_icons_exist_in_css():
    """
    All icons used for keyword tags have a rule in the icon font stylesheet.
    """
    css = (c.web_static_path / 'css' / 'osgl.min.css').read_text(encoding='utf-8')
    icons = {g.multiplayer_icon} | {icon for icon_ids, _ in g.content_keyword_icon_map.values() for icon in icon_ids}
    for icon in icons:
        assert f'.icon-{icon}:before' in css


def test_entry_index():
    """
    The index node of an entry marks mature entries bold and shows beta and inactivity as tags.
    """
    entry = {'Title': 'Sample', 'href': ['games', 'S.html#sample'], 'anchor-id': 'sample',
             'State': ['beta', 'inactive since 2020']}
    node = g.entry_index(entry)
    assert node['bold'] is False
    assert node['tags']['text'] == '(beta, inactive since 2020)'
    entry['State'] = ['mature']
    node = g.entry_index(entry)
    assert node['bold'] is True and 'tags' not in node


@pytest.mark.parametrize('function, key, threshold', [
    (g.inspiration_index, 'Inspired entries', g.TOP_INSPIRATION_THRESHOLD),
    (g.developer_index, 'Games', g.TOP_DEVELOPER_THRESHOLD),
])
def test_inspiration_and_developer_index(function, key, threshold):
    """
    Inspirations and developers are bold from a threshold on and show their count if larger than one.
    """
    item = {'Name': 'Someone', 'href': ['x', 'S.html#someone'], 'anchor-id': 'someone', key: ['a']}
    node = function(item)
    assert node['bold'] is False and 'tags' not in node
    item[key] = ['a'] * threshold
    node = function(item)
    assert node['bold'] is True and node['tags']['text'] == f'({threshold})'


# Complete generation


@pytest.fixture
def website_folder(tmp_path, monkeypatch):
    """
    Redirects all output paths of the website generator to a temporary folder and returns it.
    """
    web_path = tmp_path / 'docs'
    monkeypatch.setattr(c, 'web_path', web_path)
    monkeypatch.setattr(c, 'web_css_path', web_path / 'css')
    monkeypatch.setattr(c, 'web_js_path', web_path / 'js')
    monkeypatch.setattr(c, 'web_screenshots_path', web_path / 'screenshots')
    monkeypatch.setattr(c, 'web_data_path', web_path / 'data')
    monkeypatch.setattr(c, 'json_db_file', web_path / 'data' / 'entries.json')
    monkeypatch.setattr(g, 'previous_files', {})
    return web_path


@pytest.mark.slow
def test_generate_website(website_folder):
    """
    The complete website is generated from the real database without errors and contains the main pages,
    one table row per entry and the statistics charts.
    """
    g.main()

    for page in ('index.html', 'table.html', 'contribute.html', 'favicon.svg',
                 'games/index.html', 'games/A.html', 'games/languages.html', 'games/genres.html',
                 'games/platforms.html', 'frameworks/index.html', 'inspirations/index.html',
                 'developers/index.html', 'statistics/index.html', 'css/osgl.min.css', 'js/osgl.js'):
        assert (website_folder / page).is_file(), page

    number_entries = sum(1 for file in c.entries_path.iterdir() if file.is_file())
    table = json.loads((website_folder / 'data' / 'entries.json').read_text(encoding='utf-8'))
    assert len(table['data']) == number_entries

    charts = list((website_folder / 'statistics').glob('*.svg'))
    assert len(charts) >= 5
    assert not (website_folder / 'invalid.html').exists()
