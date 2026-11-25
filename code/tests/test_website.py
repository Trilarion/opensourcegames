"""
Tests for the static website generator (osgl.website.generate): helper functions and a complete generation run
into a temporary folder.
"""

import json

import pytest

from osgl import constants as c, osg, parse, statistics as stat
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


def test_count_text():
    """
    The number is followed by the singular for one and the plural otherwise.
    """
    assert g.count_text(1, 'game') == '1 game'
    assert g.count_text(0, 'game') == '0 games'
    assert g.count_text(3, 'entry') == '3 entries'


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


@pytest.mark.parametrize('path, expected', [
    (['index.html'], ''),
    (['games', 'index.html'], 'games/'),
    (['games', 'A.html'], 'games/A.html'),
    (['table.html'], 'table.html'),
])
def test_page_url(path, expected):
    """
    Public page URLs are absolute, index pages are addressed by their folder.
    """
    assert g.page_url(path) == c.web_url + expected


def test_set_page_metadata():
    """
    Title gets the site name, canonical URL and relative links follow the page path.
    """
    base = {}
    g.set_page_metadata(base, ['games', 'A.html'], 'Some title', 'Some description')
    assert base['title'] == f'Some title | {g.SITE_SHORT_NAME}'
    assert base['description'] == 'Some description'
    assert base['canonical-url'] == c.web_url + 'games/A.html'
    assert base['url_to'](['contribute.html']) == '../contribute.html'


def test_create_sitemap():
    """
    The sitemap lists the sorted absolute URLs of all pages.
    """
    text = g.create_sitemap([['table.html'], ['games', 'index.html'], ['index.html']])
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<urlset ')
    locs = [line.strip()[len('<url><loc>'):-len('</loc></url>')] for line in text.splitlines() if '<loc>' in line]
    assert locs == [c.web_url, c.web_url + 'games/', c.web_url + 'table.html']


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


def test_make_text_with_links_plain_text():
    """
    A text without links is a single text node.
    """
    assert g.make_text_with_links('Simple puzzle game.', {}) == [g.make_text('Simple puzzle game.')]


def test_make_text_with_links_bare_url():
    """
    Bare URLs become shortened links, trailing punctuation stays text.
    """
    nodes = g.make_text_with_links('See https://example.org/page.', {})
    assert nodes[0] == g.make_text('See ')
    assert nodes[1]['href'] == 'https://example.org/page'
    assert nodes[1]['content'] == g.make_text('example.org/page')
    assert nodes[2] == g.make_text('.')


def test_make_text_with_links_known_service():
    """
    Bare URLs of known services are shown with their icon, Wikipedia links with the article name.
    """
    nodes = g.make_text_with_links('https://github.com/example/sample', {})
    assert nodes[0]['content'][0]['id'] == 'github'
    nodes = g.make_text_with_links('https://en.wikipedia.org/wiki/Sample_game_%28video%29', {})
    assert nodes[0]['content'][1] == g.make_text('Sample game (video)')


def test_make_text_with_links_markdown():
    """
    Markdown links become links with their label, links to entries point to the entry on the website, unknown
    entries are only text.
    """
    references = {'other.md': ['games', 'O.html#other']}
    nodes = g.make_text_with_links('See [Other](other.md), [Site](https://example.org) and [Gone](gone.md)', references)
    assert nodes[1] == g.make_url(['games', 'O.html#other'], 'Other')
    assert nodes[3] == g.make_url('https://example.org', 'Site')
    assert nodes[5] == g.make_text('Gone')
    assert [node['text'] for node in nodes[0::2]] == ['See ', ', ', ' and ']


def test_make_text_with_links_line_breaks():
    """
    Line breaks are kept.
    """
    nodes = g.make_text_with_links('First line.\nSecond line.', {})
    assert nodes == [g.make_text('First line.'), g.make_line_break(), g.make_text('Second line.')]


def test_make_icon_without_css():
    """
    Icons without CSS classes have no default color (they take the color of the surrounding text).
    """
    assert g.make_icon('sun') == {'type': 'icon', 'id': 'sun'}
    assert g.make_icon('sun', 'Active', 'has-text-link')['css'] == 'has-text-link'


def test_platform_colors_are_text_colors():
    """
    Platform icons are colored with text color helpers, color modifiers like is-danger have no effect on icons.
    """
    assert all(color.startswith('has-text-') for color in g.platform_color.values())


@pytest.fixture
def macros():
    """
    The macros of the website templates, rendered with the generator's Jinja environment.
    """
    base = {'url_to': lambda target, info=None: target if isinstance(target, str) else '/'.join(target)}
    return g.create_environment(base).get_template('macros.jinja').module


def test_render_icons(macros):
    """
    Icons within the content are a single element, icons rendered directly by the templates keep the Bulma container.
    """
    icon = g.make_icon('sun', 'Active', 'has-text-link')
    assert str(macros.render_element(icon)) == '<i class="icon-sun inline-icon has-text-link" title="Active"></i>'
    assert str(macros.render_element(g.make_icon('sun'))) == '<i class="icon-sun inline-icon"></i>'
    assert str(macros.render_icon({'id': 'home'})) == '<span class="icon"><i class="icon-home"></i></span>'


def test_render_text_with_links_escapes(macros):
    """
    Free text with links is escaped, only the links are HTML.
    """
    nodes = g.make_text_with_links('A <b> & [C](https://example.org)', {})
    assert str(macros.render_element(nodes)) == 'A &lt;b&gt; &amp; <a href="https://example.org">C</a>'


def test_inline_icon_class_in_css():
    """
    The class used for inline icons and the class of the notes are defined in the website stylesheet.
    """
    css = (c.web_static_path / 'css' / 'osgl.min.css').read_text(encoding='utf-8')
    assert '.inline-icon {' in css
    assert '.entry-note {' in css


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
    node = g.developer_profile_link(link)
    assert node['href'] == href
    assert 'css' not in node['content']  # icon in the link color


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
    The index node of an entry marks mature entries bold (as class of the link) and shows beta and inactivity as
    tags.
    """
    entry = {'Title': 'Sample', 'href': ['games', 'S.html#sample'], 'anchor-id': 'sample',
             'State': ['beta', 'inactive since 2020']}
    node = g.entry_index(entry)
    assert 'class' not in node['url']
    assert node['tags']['text'] == '(beta, inactive since 2020)'
    entry['State'] = ['mature']
    node = g.entry_index(entry)
    assert node['url']['class'] == g.BOLD_CLASS and 'tags' not in node


def test_make_alphabetical_index():
    """
    The alphabetical index of a selection of entries is sorted, contains only letters with entries and their number.
    """
    entries = [{'Title': title, 'href': ['games', f'{title[0]}.html#{title}'], 'anchor-id': title, 'letter': title[0],
                'State': ['mature']} for title in ('Cb', 'Aa', 'Ca')]
    index = g.make_alphabetical_index(entries, 'Title', 'Subtitle', 'game')
    assert index['categories'] == ['A', 'C']
    assert index['number_entries'] == {'A': 1, 'C': 2}
    assert [node['url']['content']['text'] for column in index['entries']['C'] for node in column] == ['Ca', 'Cb']
    assert index['category-infos']['A'] == g.make_text('1 game')
    assert index['category-infos']['C'] == g.make_text('2 games')


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
    assert 'class' not in node['url'] and 'tags' not in node
    item[key] = ['a'] * threshold
    node = function(item)
    assert node['url']['class'] == g.BOLD_CLASS and node['tags']['text'] == f'({threshold})'


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


def test_create_chart_section(website_folder):
    """
    The chart is written to the statistics folder, N/A items are listed but not passed to the chart.
    """
    charted = []
    chartmaker = lambda statistics: charted.extend(statistics) or '<svg></svg>'
    section = g.create_chart_section([('beta, active', 3), ('N/A', 1)], 'State', 'state.svg', chartmaker)
    assert section == {'title': 'State', 'id': 'state',
                       'items': [[g.make_text('beta, active'), g.make_text(' (3)')], [g.make_text('N/A'), g.make_text(' (1)')]],
                       'chart': g.statistics_path + ['state.svg']}
    assert charted == [('beta, active', 3)]
    assert (website_folder / 'statistics' / 'state.svg').read_text(encoding='utf-8') == '<svg></svg>'


def test_create_chart_section_links(website_folder):
    """
    Items are linked if the link function returns a target, 'Other' and 'N/A' are never linked.
    """
    link = lambda name: ['games', 'x.html'] if name != 'C' else None
    section = g.create_chart_section([('Lua', 3), ('C', 2), ('Other', 1), ('N/A', 1)], 'Languages', 'l.svg',
                                     lambda statistics: '<svg></svg>', link)
    names = [item[0] for item in section['items']]
    assert names[0] == g.make_url(['games', 'x.html'], 'Lua')
    assert names[1:] == [g.make_text('C'), g.make_text('Other'), g.make_text('N/A')]


def test_create_statistics_section_keep_and_normalize(website_folder):
    """
    Values are normalized before counting, filtered and rare values are combined.
    """
    entries = [{'Keyword': ['action', 'multiplayer online', '2D']}, {'Keyword': ['action', 'multiplayer LAN']}]
    section = g.create_statistics_section(entries, 'Keyword', 'Other keywords', 'k.svg', lambda statistics: '<svg></svg>',
                                          threshold=2, normalize=stat.normalize_keyword,
                                          keep=lambda keyword: keyword != 'action')
    assert section['items'] == [[g.make_text('multiplayer'), g.make_text(' (2)')], [g.make_text('Other'), g.make_text(' (1)')]]


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
    assert len(charts) >= 8
    for chart in ('state.svg', 'genres.svg', 'other_keywords.svg'):
        assert (website_folder / 'statistics' / chart).is_file(), chart
    # statistics page starts with the state section and links to the contribution guidelines (warning box and footer)
    statistics_page = (website_folder / 'statistics' / 'index.html').read_text(encoding='utf-8')
    assert statistics_page.count('<a href="../contribute.html">contribution guidelines</a>') == 2
    state_id, platforms_id = (osg.canonical_name(title) for title in ('State', 'Supported platforms'))
    assert statistics_page.index(f'id="{state_id}"') < statistics_page.index(f'id="{platforms_id}"')
    # contribute page with tasks for volunteers, the internal platform link points to an existing section
    contribute = (website_folder / 'contribute.html').read_text(encoding='utf-8')
    assert '<a href="games/platforms.html#unknown%20platform%20support">' in contribute
    assert 'blob/master/code/backlog.txt' in contribute
    platforms = (website_folder / 'games' / 'platforms.html').read_text(encoding='utf-8')
    assert f'id="{g.UNKNOWN_PLATFORM.lower()}"' in platforms
    # linked items in the lists
    assert '<a href="../games/platforms.html#windows">Windows</a>' in statistics_page
    assert '<a href="../games/languages.html#c++">C++</a>' in statistics_page
    assert '<a href="../games/genres.html#action">action</a>' in statistics_page
    assert '<a href="../games/remakes.html">remake or clone</a>' in statistics_page
    assert not (website_folder / 'invalid.html').exists()

    # sitemap with all pages, but not the search console token
    sitemap = (website_folder / 'sitemap.xml').read_text(encoding='utf-8')
    assert f'<loc>{c.web_url}</loc>' in sitemap and f'<loc>{c.web_url}games/A.html</loc>' in sitemap
    assert 'google' not in sitemap
    assert sitemap.count('<loc>') == sum(1 for _ in website_folder.rglob('*.html')) - 1

    # canonical link and link previews of a sub page, the footer link is relative to the page
    page = (website_folder / 'games' / 'A.html').read_text(encoding='utf-8')
    assert f'<link rel="canonical" href="{c.web_url}games/A.html">' in page
    assert f'<meta property="og:image" content="{c.web_url}{g.SOCIAL_IMAGE}">' in page
    assert '<title>Open source games starting with A | OSGL</title>' in page
    assert '<a href="../contribute.html">contribution guidelines</a>' in page

    # main page with search form, statistics link and the tiles
    index = (website_folder / 'index.html').read_text(encoding='utf-8')
    assert '<form action="table.html" method="get"' in index
    assert 'href="statistics/index.html" class="is-underlined"' in index
    assert index.count('class="box has-text-centered') == len(g.index_genres) + 5
    for target in ('games/genres.html#action', 'games/web.html', 'games/libre.html', 'games/remakes.html',
                   'games/top.html', 'games/kids.html'):
        assert f'href="{target}"' in index, target

    # remakes and libre games are compact indices linking to the entries on the alphabetical pages
    for page in ('remakes.html', 'libre.html'):
        text = (website_folder / 'games' / page).read_text(encoding='utf-8')
        assert '<div class="columns">' in text, page
        assert 'Raw entry' not in text, page
        assert 'href="A.html#' in text, page

    # developers with name and contacts in one line, improve link once per page
    developers = (website_folder / 'developers' / 'A.html').read_text(encoding='utf-8')
    assert developers.count('title="Contribution guide"') == 1
    assert 'class="level' not in developers


def _index_game(keywords, states):
    """
    Create a minimal game entry for the main page data.
    """
    return {'Keyword': keywords, 'State': states, 'Code language': ['C++']}


def test_create_index_data():
    """
    The main page data contains the key numbers and one tile per selected genre and sub list.
    """
    games = [_index_game(['action'], ['mature']), _index_game(['puzzle'], ['beta', 'inactive since 2010'])]
    non_games = [{'Keyword': ['library'], 'State': ['mature'], 'Code language': ['Python']}]
    games_by_genre = {genre: [] for genre in g.index_genres}
    games_by_genre['Action'] = games[:1]
    index_lists = ((g.games_web_path, 'earth', 'Playable in the browser', 1234, 'games'),)
    data = g.create_index_data(games, non_games, [{}] * 3, [{}] * 4, games_by_genre, index_lists)

    assert (data['number-games'], data['number-non-games']) == ('2', '1')
    assert (data['number-mature'], data['number-active']) == ('1', '1')
    assert (data['number-languages'], data['number-developers'], data['number-inspirations']) == ('2', '3', '4')
    assert [tile['title'] for tile in data['genre-tiles']] == list(g.index_genres)
    assert data['genre-tiles'][0]['href'] == ['games', 'genres.html#action']
    assert data['genre-tiles'][0]['number'] == '1 games'
    assert data['list-tiles'] == [g.make_index_tile(g.games_web_path, 'earth', 'Playable in the browser', 1234)]
    assert data['list-tiles'][0]['number'] == '1,234 games'


def test_create_index_data_unknown_genre():
    """
    A configured main page genre that is not a known genre is an error.
    """
    with pytest.raises(RuntimeError, match='Unknown main page genres'):
        g.create_index_data([], [], [], [], {}, ())
