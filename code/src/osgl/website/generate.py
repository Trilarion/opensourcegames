"""
Generates the static website.

Uses

- Jinja2 (https://jinja.palletsprojects.com/en/2.11.x/)
- Simple-DataTables (https://github.com/fiduswriter/Simple-DataTables)
- Bulma for css styling (unfortunately bulma become very bloated after 0.9.4)

Sitemap is not needed, only for large projects with lots of JavaScript und many pages that aren't discoverable.
"""

# TODO tab: new filter tab (playable in a browser) with tiles (https://bulma.io/documentation/layout/tiles/) sorted by genre (just as normal list so far, no tiles yet)
# TODO tab: new filter tab (my top 100) with games I really like (mature and I tried them and there is a download for each of them) and some categories with explanation why and possible link to a review on the blog (like evil cult), still need to to that


# TODO general: replace or remove @notices like @add in entries (these notices should go to () comments anyway
# TODO general: check singular, plural (game, entries, items) although support is already quite good for that (Code Languages, ...)
# TODO general: better link replacements for showing the urls of links (see shortcut_url, also used for links in notes)
# TODO general: style URLs (Github, Wikipedia, Internet archive, SourceForge, ...)

# TODO general: meta/title+description tag
# TODO general: meta description of the pages, fill them

# TODO general: optimize layout for mobile view (quite good already)
# TODO general: meta titles for all pages, make them nice because they appear in search results! (https://www.contentpowered.com/blog/good-ctr-search-console/)

# TODO idea: text description automatically generate from keywords, state, and technical information for example: First-person action shooter written in C++, inspired by ... but inactive for 7 years.

# TODO statistics: should have disclaimer (warning or info box) about accuracy with link to contribute guidelines at the top
# TODO statistics: better and more statistics with links where possible
# TODO statistics: get it from common statistics generator
# TODO statistics: normalization, what if there are multiple entries per field (pie chart would be wrong, better to show bar chart instead)
# TODO statistics: state (beta, mature x active, inactive)
# TODO statistics: non essential keywords

# TODO games: developer details is too small to click on some devices, maybe details is-size6 instead (make technical details size 6 but with more)
# TODO games: keyword tags underlined to indicate links
# TODO games: @see-home/@see-download/@add (ignore or replace?)
# TODO games: top 100 list from Github via their stars with download links (add to entries)
# TODO games: order: homepage, inspiration, download, developer
# TODO games: link to dependencies (either if existing or if url)
# TODO games: repositories comments have too much space after( and before ) (use icons without span and with pr-0 on the icon
# TODO games: only the first paragraph of the note is shown, it often mixes the short description with "See also" lines and maintainer notes (TODO: ...), maybe make the short description a field
# TODO games: cross-references for code dependencies if included
# TODO games: "for adults" tagged need a special icon warning (not safe for work or something)
# TODO games: use genre icon after the game title (or before)
# TODO games: use moon or sun icon before inactive, not afterwards

# TODO contribute: contribute.html add content (especially what volunteers can be done)

# TODO developers: anchors to non-latin written developers do not work (chinese names have simply xxxxx)
# TODO developers: developers without a name (or with a zero width name)
# TODO developers: level with github, sourceforge links in one item (on mobile on one line)
# TODO developers: gitlab and bitbucket user profiles

# TODO inspirations: icon full lamp (not contained in icomoon.io)
# TODO inspirations: if included in the database, link instead to game (cross-reference)
# TODO inspirations: add media links and genres, maybe also years and original developer

import shutil
import math
import datetime
import time
import json
import re
import string
import urllib.parse
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from typing import Any, NoReturn, TypeAlias, TypeVar

from jinja2 import Environment, FileSystemLoader
import html5lib

from osgl import osg, constants as c, utils, statistics as stat, parse

Entry: TypeAlias = dict[str, Any]
"""
A parsed entry, developer, or inspiration augmented for template rendering.
"""

TemplateNode: TypeAlias = dict[str, Any]
"""
A structured value consumed by the Jinja templates.
"""

Item = TypeVar('Item')
Category = TypeVar('Category')

# the categories for the alphabetical indices, letters A-Z, used for identification and as link names internally
alphabet = string.ascii_uppercase
# the internal category name for all names not starting with a letter
extra = '0'
extended_alphabet = alphabet + extra
# and how they are displayed
extended_alphabet_names = {k: k for k in alphabet}
extended_alphabet_names[extra] = '0-9'
# especially for developers, replacements from other alphabets
alphabet_replacements = {'Á': 'A', 'Å': 'A', 'Ä': 'A', 'É': 'E', 'ⴹ': 'E', 'Ł': 'L', 'Ľ': 'L', 'А': 'A', 'Б': 'B', 'Д': 'D', 'И': 'I', 'К': 'K', 'П': 'P', 'Ö': 'O', 'Ü': 'U', 'ζ': 'Z'}

TOP_INSPIRATION_THRESHOLD = 4  # at least that many inspired games
TOP_DEVELOPER_THRESHOLD = 4    # at least that many developed games
BOLD_CLASS = 'has-text-weight-semibold'  # highlighted (mature or prolific) items in the indices

UNKNOWN_PLATFORM = 'Unknown platform support'

# the subfolder structure
games_path = ['games']
non_games_path = ['frameworks']
inspirations_path = ['inspirations']
developers_path = ['developers']
statistics_path = ['statistics']

# derived paths
games_index_path = games_path + ['index.html']
non_games_index_path = non_games_path + ['index.html']
inspirations_index_path = inspirations_path + ['index.html']
developers_index_path = developers_path + ['index.html']
statistics_index_path = statistics_path + ['index.html']

games_by_language_path = games_path + ['languages.html']
games_by_genres_path = games_path + ['genres.html']
games_by_platform_path = games_path + ['platforms.html']
games_top_path = games_path + ['top.html']
games_kids_path = games_path + ['kids.html']
games_web_path = games_path + ['web.html']
games_libre_path = games_path + ['libre.html']
games_remakes_path = games_path + ['remakes.html']

# those either are repos with many projects in it or are projects that have commercial content and there is no binary
# release or there is only a commercial binary release, so you cannot play them right away for free
github_top_ignored_repos = ('https://github.com/Hopson97/MineCraft-One-Week-Challenge.git', 'https://github.com/jdah/minecraft-weekend.git', 'https://github.com/TerryCavanagh/vvvvvv.git',
                              'https://github.com/nicholas-ochoa/OpenSC2K.git', 'https://github.com/BlindMindStudios/StarRuler2-Source.git', 'https://github.com/TheMozg/awk-raycaster.git',
                              'https://github.com/PistonDevelopers/hematite.git', 'https://github.com/keendreams/keen.git', 'https://github.com/ddevault/TrueCraft.git')

platform_color = {
    'Windows': 'has-text-danger',
    'Linux': 'has-text-link',
    'macOS': 'has-text-success',
    'Android': 'has-text-black',
    'iOS': 'has-text-primary',
    'Web': 'has-text-warning',
}

# map from supported OS name to icon name
platform_icon_map = {
    'Windows': 'windows',
    'Linux': 'tux',
    'macOS': 'appleinc',
    'Android': 'android',
    'iOS': 'ios',
    'Web': 'earth',
    UNKNOWN_PLATFORM: 'device_unknown'
}

# map from genre name to icon name
genre_icon_map = {
    'Action': 'target',
    'Arcade': 'pacman',
    'Adventure': 'dice',
    'Educational': 'graduation-cap',
    'Game engine': 'car',
    'Puzzle': 'puzzle-piece',
    'Role playing': 'user-secret',
    'Simulation': 'rocket1',
    'Strategy': 'fort-awesome',
    'Cards': 'spades',
    'Board': 'chess',
    'Music': 'music',
    'Visual novel': 'book',
    'Platform': 'directions_run',
    'Sports': 'soccer-court',
    'Framework': 'stack',
    'Library': 'library'
}

# map from content keyword to the icon names (repetitions allowed) and the tooltip of the shown icon tag,
# variants with a trailing " (?)" use the same icons with an uncertainty note (see create_icon_keyword_tag)
content_keyword_icon_map = {
    'content open': (('lock_open',), c.keyword_genre_descriptions['content open']),
    'content free': (('lock_open',), c.keyword_genre_descriptions['content free']),
    'content commercial': (('attach_money',), c.keyword_genre_descriptions['content commercial']),
    'content commercial + original required': (
        ('attach_money', 'attach_money'),
        f"{c.keyword_genre_descriptions['content commercial']} The original game is required."),
}
multiplayer_icon = 'users'

# genres shown as tiles on the main page (subset of the genres, all must exist)
index_genres = ('Action', 'Strategy', 'Role playing', 'Puzzle')

# cross-references to the language pages
code_language_references = {language: games_by_language_path[:-1] + [f'{games_by_language_path[-1]}#{language.lower()}'] for language in c.known_languages}

# map of internal non game names to display names (which are in plural)
non_game_category_names = {
    'tool': 'Tools',
    'framework': 'Frameworks',
    'library': 'Libraries',
    'game engine': 'Game Engines'
}

# we check the output html structure every time
html5parser = html5lib.HTMLParser(strict=True)

# file hashes for detecting changes
previous_files = {}

# pluralization (mostly with s, but there are a few exceptions)
plurals = {k: k+'s' for k in ('Assets license', 'Contact', 'Code language', 'Code license', 'Developer', 'Download', 'Inspiration', 'Game', 'Keyword', 'Home', 'Homepage', 'Organization', 'Platform', 'Tag')}
for k in ('Media', 'Play', 'Play online', 'State'):
    plurals[k] = k
for k in ('Code repository', 'Code dependency'):
    plurals[k] = k[:-1] + 'ies'


def get_plural_or_singular(name: str, amount: int) -> str:
    """
    Return the singular or configured plural form of ``name`` for ``amount``.

    Raises:
        RuntimeError: If ``name`` is not present in the pluralization table.
    """
    if not name in plurals.keys():
        raise RuntimeError(f'"{name}" not a known singular!')
    if amount == 1:
        return name
    return plurals[name]


def file_hash(text: str) -> int:
    """
    Hash generated markup while ignoring timestamps that change on every build.
    """
    lines = [line for line in text.split('\n') if not line.startswith('  This website is built ')]
    return hash(''.join(lines))


def raise_helper(msg: str) -> NoReturn:
    """
    Raise an exception from a Jinja expression where ``raise`` is unavailable.
    """
    raise Exception(msg)


def create_environment(base: dict[str, Any]) -> Environment:
    """
    Create the Jinja environment for the website templates, with autoescaping and the helper globals.

    Args:
        base: Page data shared by all templates (available as ``base`` in the templates).
    """
    environment = Environment(loader=FileSystemLoader(c.web_template_path), autoescape=True)
    environment.globals['base'] = base
    environment.globals['raise'] = raise_helper
    environment.globals['is_list'] = lambda obj: isinstance(obj, list)
    return environment


def write(text: str, path: str | Sequence[str]) -> None:
    """
    Validate and write a generated HTML page below the website output directory.

    If the normalized content matches a previous file, preserve that file's text so
    timestamp-only changes do not cause an unnecessary rewrite.
    """
    # output file
    if isinstance(path, str):
        path = [path]
    file = c.web_path
    for part in path:
        file /= part

    # check file hash and use previous version
    if file in previous_files and previous_files[file]['hash'] == file_hash(text):
        # no significant change, use previous version instead
        text = previous_files[file]['text']
    else:
        # validate text
        try:
            html5parser.parse(text)
        except Exception as e:
            utils.write_text(c.web_path / 'invalid.html', text)  # for further checking with https://validator.w3.org/
            print(f'problem with file {file}, see invalid.html')
            raise RuntimeError(e)

    # create output directory if necessary
    file.parent.mkdir(parents=True, exist_ok=True)

    # write text
    utils.write_text(file, text)


def sort_into_categories(
    items: Sequence[Item], categories: Sequence[Category],
    fit: Callable[[Item, Category], bool], unknown_category_name: str | None = None,
) -> dict[Category | str, list[Item]]:
    """
    Group items into every matching category and optionally an uncategorized group.

    Items may occur in more than one category.  The optional fallback contains only
    items that do not match any supplied category.
    """
    categorized_sublists = {}
    for category in categories:
        sublist = [item for item in items if fit(item, category)]
        categorized_sublists[category] = sublist
    if unknown_category_name:
        # now those that do not fit
        sublist = [item for item in items if not any(fit(item, category) for category in categories)]
        categorized_sublists[unknown_category_name] = sublist
    return categorized_sublists


def divide_in_three_columns_and_transform(
    categorized_lists: dict[Category, Sequence[Item]],
    transform: Callable[[Item], TemplateNode],
) -> dict[str, dict[Category, int] | dict[Category, list[list[TemplateNode]]]]:
    """
    Transform categorized items and split each category into three columns
    for creating a tabular layout of entries.
    """
    number_entries = {category: len(categorized_lists[category]) for category in categorized_lists.keys()}
    entries = {}
    for category in categorized_lists.keys():
        e = categorized_lists[category]
        # transform entry
        e = [transform(e) for e in e]
        # divide in three equal lists
        n = len(e)
        n1 = math.ceil(n/3)
        n2 = math.ceil(2*n/3)
        e = [e[:n1], e[n1:n2], e[n2:]]
        entries[category] = e
    return {'number_entries': number_entries, 'entries': entries}


def make_alphabetical_index(entries: Sequence[Entry], title: str, subtitle: str, unit: str) -> dict[str, Any]:
    """
    Create a compact alphabetical index (for the categorical index template) of a selection of entries.

    The index links to the entries on their alphabetical pages instead of repeating them. Only letters with entries
    are shown.

    Args:
        entries: The selected entries (games and non-games), must already have their links (see :func:`preprocess`).
        title: Title of the index page.
        subtitle: Subtitle of the index page.
        unit: Name of the entries in the number of entries per letter (e.g. "games").
    """
    entries = sorted(entries, key=lambda entry: str.casefold(entry['Title']))
    letters = [letter for letter in extended_alphabet if any(entry['letter'] == letter for entry in entries)]
    by_letter = sort_into_categories(entries, letters, lambda entry, letter: entry['letter'] == letter)
    index = divide_in_three_columns_and_transform(by_letter, entry_index)
    index['title'] = make_text(title)
    index['subtitle'] = [make_text(subtitle)]
    index['categories'] = letters
    index['category-names'] = extended_alphabet_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 20
    index['category-infos'] = {letter: make_text(f'{len(by_letter[letter])} {unit}') for letter in letters}
    return index


def url_to(current: Sequence[str], target: str | Sequence[str], info: Any = None) -> str:
    """
    Return a relative URL from ``current`` to ``target``.

    Absolute HTTP(S) targets are returned unchanged.  ``info`` is accepted because
    Jinja may pass additional context when calling this helper.
    """
    # if it's an absolute url, just return
    if isinstance(target, str) and any(target.startswith(x) for x in ('http://', 'https://')):
        return target
    if isinstance(target, str):
        target = [target]
    # split by slash
    #if current:
    #    current = current.split('/')
    #target = target.split('/')
    # reduce by common elements
    while len(current) > 0 and len(target) > 1 and current[0] == target[0]:
        current = current[1:]
        target = target[1:]
    # add .. as often as length of current still left
    target = ['..'] * len(current) + target
    # join by slash again
    url = '/'.join(target)
    return url


def set_page_metadata(base: Entry, title: str, description: str) -> None:
    """
    Set the title and search-result description for the next rendered HTML page.
    """
    base['title'] = title
    base['description'] = description


def preprocess(
    items: Sequence[Entry], key: str,
    url: list[str] | Callable[[Entry], list[str]],
) -> None:
    """
    Add anchors, alphabetical groups, and output links to renderable records.

    ``url`` is either a shared base path or a function selecting a path per item.
    """
    _ = set() # this is just to avoid duplicating anchors
    for item in items:
        # add unique anchor ref
        anchor = osg.canonical_name(item[key])
        while anchor in _:
            anchor += 'x'
        _.add(anchor)
        item['anchor-id'] = anchor

        # for alphabetic sorting
        start = item[key][0].upper()
        # special treatment of some variables
        start = alphabet_replacements.get(start, start)
        if not start in alphabet:
            start = extra
        item['letter'] = start
        item_url = url(item) if callable(url) else url
        item['href'] = item_url + [f'{start}.html#{anchor}']


def entry_index(entry: Entry) -> TemplateNode:
    """
    Create the compact index representation of a game or framework entry.
    """
    e = {
        'url': make_url(entry['href'], entry['Title'], css_class=BOLD_CLASS if 'mature' in entry['State'] else None),
        'anchor-id': entry['anchor-id']
    }
    tags = []
    if 'beta' in entry['State']:
        tags.append('beta')
    if osg.is_inactive(entry):
        tags.append(f'inactive since {osg.extract_inactive_year(entry)}')
    if tags:
        e['tags'] = make_text(f"({', '.join(tags)})", 'is-size-7')
    return e


def inspiration_index(inspiration: Entry) -> TemplateNode:
    """
    Create the compact index representation of an inspiration.
    """
    n = len(inspiration['Inspired entries'])
    e = {
        'url': make_url(inspiration['href'], inspiration['Name'], css_class=BOLD_CLASS if n >= TOP_INSPIRATION_THRESHOLD else None),
        'anchor-id': inspiration['anchor-id']
    }
    if n > 1:
        e['tags'] = make_text(f'({n})')
    return e


def developer_index(developer: Entry) -> TemplateNode:
    """
    Create the compact index representation of a developer.
    """
    n = len(developer['Games'])
    e = {
        'url': make_url(developer['href'], developer['Name'], css_class=BOLD_CLASS if n >= TOP_DEVELOPER_THRESHOLD else None),
        'anchor-id': developer['anchor-id']
    }
    if n > 1:
        e['tags'] = make_text(f'({n})', 'is-size-7')
    return e


def shortcut_url(url: str, name: str) -> str | list[TemplateNode]:
    """
    Create a concise, optionally icon-based label for a known external URL.
    """
    # remove slash at the end
    if url.endswith('/'):
        url = url[:-1]

    # gitlab
    gl_prefix = 'https://gitlab.com/'
    if url.startswith(gl_prefix):
        return [make_icon('gitlab'), make_text(url[len(gl_prefix):])]

    # github
    gh_prefix = 'https://github.com/'
    if url.startswith(gh_prefix):
        return [make_icon('github'), make_text(url[len(gh_prefix):])]

    # sourceforge
    sf_prefix = 'https://sourceforge.net/projects/'
    if url.startswith(sf_prefix):
        return [make_icon('sourceforge'), make_text(url[len(sf_prefix):])]

    # archive link
    ia_prefix = 'https://web.archive.org/web/'
    if url.startswith(ia_prefix):
        # return 'Archive: ' + url[len(ia_prefix):]
        return [make_icon('library'), make_text(url[len(ia_prefix):])]

    # Wikipedia link
    wp_prefix = 'https://en.wikipedia.org/wiki/'
    if url.startswith(wp_prefix):
        # return 'WP: ' + url[len(wp_prefix):]
        return [make_icon('wikipedia'), make_text(name)]

    # cutoff common prefixes
    for prefix in ('http://', 'https://'):
        if url.startswith(prefix):
            return url[len(prefix):]
    # as is
    return url


def make_url(
    href: str | Sequence[str], content: str | TemplateNode | list[TemplateNode],
    title: str | None = None, css_class: str | None = None,
) -> TemplateNode:
    """
    Create a URL node for use by the Jinja templates.
    """
    if isinstance(content, str):
        content = make_text(content)
    url = {
        'type': 'url',
        'href': href,
        'content': content
    }
    if title:
        url['title'] = title
    if css_class:
        url['class'] = css_class
    # we don't need a rel tag, we open links in the same tab anway and don't about referrer information being transmitted
    return url


def make_repo_url(x: str, name: str) -> TemplateNode:
    """
    Create a repository link and display metadata encoded in its comments.
    """
    # parse comments
    comments = []
    if isinstance(x, parse.Value):
        for c in x.comment.split(','):
            c = c.strip()
            if not c.startswith('@'):
                continue
            c = c.split(' ')
            key = c[0][1:] # without the @
            if len(c) > 1:
                value = c[1]
            if key == 'archived':
                comments.append(make_text('archived'))
            if key == 'created':
                comments.append(make_text(f'since {value}'))
            if key == 'stars':
                value = int(value)
                if value > 200:
                    comments.append(make_icon('star', 'top rated'))
                elif value > 30:
                    comments.append(make_icon('star-half-full', 'medium rated'))
                else:
                    comments.append(make_icon('star-o', 'low rated'))
    # this is the default element
    url = make_url(x, shortcut_url(x, name))
    if comments:
        return make_enumeration([url, make_enclose(make_enumeration(comments), '(', ')')], '')
    else:
        return url


def make_icon(id: str, title: str | None = None, css: str | None = None) -> TemplateNode:
    """
    Create an icon node, optionally with CSS classes (e.g. a text color) and a tooltip.

    Without CSS classes, the icon takes the color of the surrounding text.
    """
    icon = {
        'type': 'icon',
        'id': id
    }
    if css:
        icon['css'] = css
    if title:
        icon['title'] = title
    return icon


def make_text(content: str, css_class: str | None = None, title: str | None = None) -> TemplateNode:
    """
    Create a text node with optional CSS class and tooltip text.
    """
    text = {
        'type': 'text',
        'text': content
    }
    if css_class:
        text['class'] = css_class
    if title:
        text['title'] = title
    return text


def make_line_break() -> TemplateNode:
    """
    Create a line-break node for rendering a literal HTML break element.
    """
    return {'type': 'line-break'}


# Markdown links "[label](target)" or bare URLs in the free text of the entries
text_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)|(https?://[^\s<>()\[\]]+)')


def make_text_with_links(text: str, entry_references: Mapping[str, Sequence[str]]) -> list[TemplateNode]:
    """
    Create nodes for a free text (e.g. a note), with its Markdown links and bare URLs as links.

    Line breaks are kept. Markdown links to other entries ("[label](name.md)") link to their entry on the website,
    if that entry is unknown only the label is shown. Bare URLs are shortened like other URLs (see
    :func:`shortcut_url`), trailing punctuation is not part of the URL.

    Args:
        text: The free text.
        entry_references: Links of the entries by their file name.
    """
    nodes = []
    for index, line in enumerate(text.splitlines()):
        if index > 0:
            nodes.append(make_line_break())
        position = 0
        for match in text_link_pattern.finditer(line):
            if match.start() > position:
                nodes.append(make_text(line[position:match.start()]))
            position = match.end()
            label, target, url = match.groups()
            if url:
                stripped = url.rstrip('.,;:!?')
                # for Wikipedia links, the article name is shown
                article = urllib.parse.unquote(stripped.rsplit('/', 1)[-1]).replace('_', ' ')
                nodes.append(make_url(stripped, shortcut_url(stripped, article)))
                if len(stripped) < len(url):
                    nodes.append(make_text(url[len(stripped):]))
            elif target.startswith(('http://', 'https://')):
                nodes.append(make_url(target, label))
            elif target.rsplit('/', 1)[-1] in entry_references:
                nodes.append(make_url(entry_references[target.rsplit('/', 1)[-1]], label))
            else:
                nodes.append(make_text(label))
        if position < len(line):
            nodes.append(make_text(line[position:]))
    return nodes


def make_enclose(entry: TemplateNode, left: str, right: str) -> TemplateNode:
    """
    Create a node that renders ``entry`` between literal delimiters.
    """
    enclose = {
        'type': 'enclose',
        'entry': entry,
        'left': left,
        'right': right
    }
    return enclose


def make_enumeration(entries: Sequence[TemplateNode], divider: str = ', ') -> TemplateNode:
    """
    Create a node that renders entries separated by ``divider``.
    """
    enumeration = {
        'type': 'enumeration',
        'entries': entries,
        'divider': divider
    }
    return enumeration


def make_tags(entries: Sequence[TemplateNode]) -> TemplateNode:
    """
    Create the tag-list node used for entry keywords.
    """
    return {
        'type': 'tags',
        'enumeration': make_enumeration(entries, divider='')
    }


def make_icon_tag(icon_ids: Sequence[str], title: str, text: str) -> TemplateNode:
    """
    Create a tag node that shows only icons, with a tooltip.

    Args:
        icon_ids: Names of the icons (without the "icon-" prefix) shown one after another.
        title: Tooltip of the tag.
        text: Text alternative for screen readers (visually hidden), typically the keyword itself.
    """
    return {
        'type': 'icon-tag',
        'icons': list(icon_ids),
        'title': title,
        'text': text
    }


def make_img(file: Sequence[str], width: int, height: int) -> TemplateNode:
    """
    Create an image node with source path and intrinsic dimensions.
    """
    return {
        'type': 'image',
        'file': file,
        'width': width,
        'height': height
    }


def developer_profile_link(link: str) -> TemplateNode:
    """
    Create a profile URL node from a contact shortcut such as ``user@GH``.

    Raises:
        RuntimeError: If the shortcut does not name a supported profile service.
    """
    if link.endswith('@SF'):
        return make_url(f'https://sourceforge.net/u/{link[:-3]}/profile/', make_icon('sourceforge'), f'User {link[:-3]} on Sourceforge')
    if link.endswith('@GH'):
        return make_url(f'https://github.com/{link[:-3]}', make_icon('github'), f'User {link[:-3]} on Github')
    if link.endswith('@GL'):
        return make_url(f'https://gitlab.com/{link[:-3]}', make_icon('gitlab'), f'User {link[:-3]} on Gitlab')
    if link.endswith('@BB'):
        return make_url(f'https://bitbucket.org/{link[:-3]}/', make_icon('bitbucket'), f'User {link[:-3]} on BitBucket')
    raise RuntimeError(f'Unknown profile link {link}')


def convert_inspirations(inspirations: Sequence[Entry], entries: Sequence[Entry]) -> None:
    """
    Add template-ready media and cross-references to inspiration records.

    Every referenced title is expected to exist in ``entries``.
    """
    entries_references = {entry['Title']: entry['href'] for entry in entries}
    for inspiration in inspirations:
        name = inspiration['Name']
        inspiration['name'] = name

        # media
        if 'Media' in inspiration:
            entries = inspiration['Media']
            entries = [make_url(url, shortcut_url(url, name)) for url in entries]
            inspiration['media'] = [make_text('Media: '), make_enumeration(entries)]

        # inspired entries (with links to them)
        inspired_entries = inspiration['Inspired entries']
        entries = [make_url(entries_references[entry], make_text(entry)) for entry in inspired_entries]
        name = make_text(f"Inspired {get_plural_or_singular('Game', len(entries)).lower()}: ", 'has-text-weight-semibold')
        inspiration['inspired'] = [name, make_enumeration(entries)]


def convert_developers(developers: Sequence[Entry], entries: Sequence[Entry]) -> None:
    """
    Add template-ready game, contact, and organization data to developers.

    Every game referenced by a developer is expected to exist in ``entries``.
    """
    entries_references = {entry['Title']:entry['href'] for entry in entries}
    # iterate over all developers
    for developer in developers:
        name = developer['Name']
        developer['name'] = name

        # games for each developer
        developed_entries = developer['Games']
        entries = [make_url(entries_references[entry], make_text(entry)) for entry in developed_entries]
        name = make_text(f"Developed {get_plural_or_singular('Game', len(entries)).lower()}: ", 'has-text-weight-semibold')
        developer['games'] = [name, make_enumeration(entries)]

        # contacts
        contacts = developer.get('Contact', [])
        entries = [developer_profile_link(entry) for entry in contacts]
        developer['contact'] = entries

        # other fields
        for field in ('Organization',):
            if field in developer:
                entries = developer[field]
                if field in c.url_developer_fields:
                    entries = [make_url(entry, shortcut_url(entry, name)) for entry in entries]
                else:
                    entries = [make_text(entry) for entry in entries]
                developer[field.lower()] = [make_text(get_plural_or_singular(field, len(entries))+': '), make_enumeration(entries)]


def create_icon_keyword_tag(keyword: str) -> TemplateNode | None:
    """
    Create an icon tag for the content and multiplayer keywords.

    Returns None for keywords without an icon representation (including rare content variants like
    "content swappable"), these are shown as text tags.
    """
    # multiplayer with optional modes ("multiplayer online + LAN")
    match = re.fullmatch(r'multiplayer(?: (.+))?', keyword)
    if match:
        if match.group(1):
            modes = [mode.strip() for mode in match.group(1).split('+')]
            title = f"Multiplayer: {', '.join(modes)}"
        else:
            title = 'Multiplayer'
        return make_icon_tag((multiplayer_icon,), title, keyword)

    # content, possibly marked as uncertain
    base_keyword, uncertain = keyword, False
    if keyword.endswith(' (?)'):
        base_keyword, uncertain = keyword[:-len(' (?)')], True
    if base_keyword in content_keyword_icon_map:
        icon_ids, title = content_keyword_icon_map[base_keyword]
        if uncertain:
            title = f'{title} (uncertain)'
        return make_icon_tag(icon_ids, title, keyword)

    return None


def create_keyword_tag(keyword: str) -> TemplateNode:
    """
    Create a keyword tag, linking recommended categories to their index.

    Content and multiplayer keywords are shown as icon tags (see :func:`create_icon_keyword_tag`).
    """
    icon_tag = create_icon_keyword_tag(keyword)
    if icon_tag:
        return icon_tag

    tooltip = c.keyword_genre_descriptions.get(keyword)
    if tooltip is None:
        for described_keyword in sorted(c.keyword_genre_descriptions, key=len, reverse=True):
            if keyword.startswith(f'{described_keyword} ') or keyword.startswith(f'{described_keyword} ('):
                tooltip = c.keyword_genre_descriptions[described_keyword]
                break

    if keyword in c.recommended_keywords:
        if keyword in c.non_game_keywords:
            url = non_games_index_path.copy()
        else:
            url = games_by_genres_path.copy()
        url[-1] += f'#{keyword}'
        # TODO are icons looking good in the keyword tags (I somehow doubt it), maybe put them separately somewhere?
        #if keyword.capitalize() in genre_icon_map:
        #    return make_url(url, [make_icon(genre_icon_map[keyword.capitalize()]), make_text(keyword)], '{} games'.format(keyword), 'tag is-light is-link')
        tooltip = tooltip or non_game_category_names.get(keyword, f'{keyword.capitalize()} games')
        return make_url(url, make_text(keyword), tooltip, 'tag is-light is-link') # TODO underline tag needs <u> and it should be generalized
    elif keyword == c.remake_or_clone_keyword:
        return make_url(games_remakes_path, make_text(keyword), tooltip, 'tag is-light is-link')
    else:
        return make_text(keyword, 'tag is-light', tooltip)


def create_state_texts(states: Sequence[str]) -> list[TemplateNode | list[TemplateNode]]:
    """
    Create status nodes for an entry's maturity and activity indicators.
    """
    if 'mature' in states:
        state = make_text('mature', 'has-text-weight-bold')
    else:
        state = make_text('beta')
    inactive = [x for x in states if x.startswith('inactive since')]
    if inactive:
        activity = make_icon('brightness_3', inactive[0]) # inactive since only as tooltip
    else:
        activity = [make_icon('sun'), make_text('active', 'has-text-weight-bold')]
    return [state, activity]


def convert_entries(
    entries: Sequence[Entry], inspirations: Sequence[Entry], developers: Sequence[Entry],
    entry_references: Mapping[str, Sequence[str]],
) -> None:
    """
    Augment game and framework entries with data consumed by entry templates.

    Inspiration and developer records must already have output links assigned by
    :func:`preprocess`.

    Args:
        entry_references: Links of all entries (games and non-games) by their file name, for the links to other
            entries in the notes.
    """
    inspirations_references = {inspiration['Name']: inspiration['href'] for inspiration in inspirations}
    developer_references = {developer['Name']: developer['href'] for developer in developers}
    for entry in entries:
        # name
        name = entry['Title']
        entry['name'] = name

        # state
        entry['state'] = create_state_texts(entry['State'])

        # note (only the first paragraph, which typically is a short description)
        if 'Note' in entry:
            paragraph = entry['Note'].strip().split('\n\n')[0]
            entry['note'] = make_text_with_links(paragraph, entry_references)

        # keywords as tags, icon tags (content, multiplayer) after the text tags
        e = [create_keyword_tag(x) for x in entry['Keyword']]
        e = [x for x in e if x['type'] != 'icon-tag'] + [x for x in e if x['type'] == 'icon-tag']
        entry['keyword'] = make_tags(e)

        # other normal fields (not technical info)
        for field in ('Home', 'Inspiration', 'Media', 'Download', 'Play', 'Developer'):
            if field in entry:
                e = entry[field]
                divider = ', '
                if field == 'Inspiration':
                    e = [make_url(inspirations_references[x], make_text(x)) for x in e]
                elif field == 'Developer':
                    e = [make_url(developer_references[x], make_text(x)) for x in e]
                elif field in c.url_fields:
                    e = [make_url(x, shortcut_url(x, name)) for x in e]
                else:
                    e = [make_text(x) for x in e]
                if field == 'Home':  # Home -> Homepage
                    field = 'Homepage'
                    # first entry bold
                    e[0]['class'] = 'has-text-weight-semibold'
                elif field == 'Play':  # Play -> Play online
                    field = 'Play online'
                namex = make_text(f'{get_plural_or_singular(field, len(e))}: ')
                entry[field.lower()] = [namex, make_enumeration(e, divider)]

        # platforms
        if 'Platform' in entry:
            e = entry['Platform']
        else:
            e = [UNKNOWN_PLATFORM]
        e = [make_url(
            games_by_platform_path[:-1] + [f'{games_by_platform_path[-1]}#{platform.lower()}'],
            make_icon(platform_icon_map[platform], css=f"{platform_color.get(platform, 'has-text-link')} is-size-6"),
            platform
        ) if platform in platform_icon_map else make_text(platform) for platform in e]
        # namex = make_text('{}: '.format(get_plural_or_singular('Platform', len(e))))
        # entry['state'].insert(0, [namex] + e)
        entry['state'].insert(0, e)

        # technical info fields
        for field in ('Code language', 'Code license', 'Code repository', 'Code dependency', 'Assets license'):
            if field in entry:
                e = entry[field]
                divider = ', '
                if not e:
                    continue
                if field == 'Code repository':
                    e = [make_repo_url(x, name) for x in e]
                elif field == 'Code language':
                    e = [make_url(code_language_references[x], make_text(x)) for x in e]
                elif field == 'Code license' or field == 'Assets license':
                    e = [make_url(c.license_urls[x], x) if x in c.license_urls else make_text(x) for x in e]
                elif field in c.url_fields:
                    e = [make_url(x, shortcut_url(x, name)) for x in e]
                else:
                    e = [make_text(x) for x in e]
                namex = make_text(f'{get_plural_or_singular(field.capitalize(), len(entries))}: ')
                entry[field.lower()] = [namex, make_enumeration(e, divider)]

        # build system
        field = 'Build system'
        if field in entry['Building']:
            e = entry['Building'][field]
            divider = ', '
            e = [make_url(c.build_system_urls[x], x) if x in c.build_system_urls else make_text(x) for x in e]
            namex = make_text(f'{field}: ')
            entry[field.lower()] = [namex, make_enumeration(e, divider)]

        entry['raw-path'] = 'https://raw.githubusercontent.com/Trilarion/opensourcegames/master/entries/' + entry['File'].name


def add_license_links_to_entries(entries: Sequence[Entry]) -> None:
    """
    Replace code-license names with ``(URL, name)`` tuples for final rendering.
    """
    for entry in entries:
        licenses = entry['Code license']
        licenses = [(c.license_urls.get(license, ''), license) for license in licenses]
        entry['Code license'] = licenses


def make_index_tile(target: Sequence[str], icon_id: str, title: str, number: int, unit: str = 'games') -> TemplateNode:
    """
    Create a tile of the main page linking to a sub list, showing the number of included items.

    Args:
        target: Path of the linked page (from the top level folder), may include an anchor.
        unit: Name of the counted items (plural), shown after the number.
    """
    return {
        'href': target,
        'icon': make_icon(icon_id, css='has-text-info'),
        'title': title,
        'number': f'{number:,} {unit}'
    }


def create_index_data(
    games: Sequence[Entry], non_games: Sequence[Entry], developers: Sequence[Entry], inspirations: Sequence[Entry],
    games_by_genre: Mapping[str, Sequence[Entry]], index_lists: Sequence[tuple[Sequence[str], str, str, int, str]],
) -> dict[str, Any]:
    """
    Create the data of the main page: key numbers, genre tiles and tiles of selected sub lists.

    Args:
        games_by_genre: Games sorted into the genres (capitalized genre names as keys).
        index_lists: Selected sub lists as (target path, icon name, title, number of items, unit) tuples.

    Raises:
        RuntimeError: If a genre in ``index_genres`` is not a known genre.
    """
    unknown_genres = [genre for genre in index_genres if genre not in games_by_genre]
    if unknown_genres:
        raise RuntimeError(f'Unknown main page genres {unknown_genres}')

    mature_games = [game for game in games if 'mature' in game['State']]
    active_games = [game for game in games if not any(state.startswith('inactive since') for state in game['State'])]
    languages = {str(language) for entry in [*games, *non_games] for language in entry.get('Code language', [])}

    genre_tiles = []
    for genre in index_genres:
        target = games_by_genres_path[:-1] + [f'{games_by_genres_path[-1]}#{genre.lower()}']
        genre_tiles.append(make_index_tile(target, genre_icon_map[genre], genre, len(games_by_genre[genre])))
    list_tiles = [make_index_tile(*index_list) for index_list in index_lists]

    return {
        'number-games': f'{len(games):,}',
        'number-non-games': f'{len(non_games):,}',
        'number-mature': f'{len(mature_games):,}',
        'number-active': f'{len(active_games):,}',
        'number-languages': f'{len(languages):,}',
        'number-developers': f'{len(developers):,}',
        'number-inspirations': f'{len(inspirations):,}',
        'genre-tiles': genre_tiles,
        'list-tiles': list_tiles
    }


def get_topN_games(games: Sequence[Entry], N: int = 100) -> list[Entry]:
    """
    Return at most ``N`` playable games ranked by repository star metadata.
    """
    top_games = []
    for game in games:
        # get stars of repositories
        stars = 0
        for repo in game.get('Code repository', [])[:1]:  # take only first one
            if repo in github_top_ignored_repos:
                continue
            if isinstance(repo, parse.Value):
                for c in repo.comment.split(','):
                    c = c.strip()
                    if not c.startswith('@'):
                        continue
                    c = c.split(' ')
                    key = c[0][1:]  # without the @
                    if len(c) > 1 and key == 'stars':
                        value = int(c[1])
                        if value > stars:
                            stars = value
        if stars > 0:
            top_games.append((game, stars))
    top_games.sort(key=lambda x:x[1], reverse=True)
    top_games = top_games[:N]  # get top N
    top_games =[game for game, stars in top_games]
    return top_games


def add_screenshot_information(entries: Sequence[Entry]) -> None:
    """
    Add image nodes for screenshots recorded in the screenshots overview.
    """
    # read screenshot information
    overview = osg.read_screenshots_overview()

    # iterate over entries
    for entry in entries:
        # get screenshots entry
        name = osg.canonical_name(entry['Title'])  # TODO should be stored upon loading I guess
        info = overview.get(name, {})
        screenshots = []
        for id, item in info.items():
            width = item[0]
            height = item[1]
            if item[2] and not item[2].startswith('!'):
                url = item[2]
            else:
                url = None
            file = ['screenshots', f'{name}_{id:02d}.jpg']
            img = make_img(file, width, height)
            if url:
                screenshot = make_url(url, img)
            else:
                screenshot = img
            screenshots.append(screenshot)
        if screenshots:
            entry['screenshots'] = screenshots


def create_table_json_data(entries: Sequence[Entry]) -> None:
    """
    Write the JSON data used by the interactive entries table.

    Entries must already contain generated internal links and a homepage.
    """
    # create json structure
    db = {'headings': ['Title', 'State', 'Tags', 'Platform', 'Language', 'License']}
    data = []
    for entry in entries:
        title = f"<a href=\"{url_to([], entry['href'])}\" class=\"has-text-weight-semibold\">{entry['Title']}</a> <a href=\"{entry['Home'][0]}\"><i class=\"icon-new-tab\"></i></a>"
        state = f'<span class="is-size-7">{", ".join(entry["State"])}</span>'
        tags = entry['Keyword']
        tags = [tag for tag in tags if tag in c.interesting_keywords]
        tags = ', '.join(tags)
        platform = entry.get('Platform', ['-'])
        platform = f'<span class="is-size-7">{", ".join(platform)}</span>'
        language = ', '.join(entry['Code language'])
        license = entry['Code license']
        license = f'<span class="is-size-7">{", ".join(license)}</span>'
        data.append([title, state, tags, platform, language, license])
    data.sort(key=lambda x: str.casefold(x[0]))
    db['data'] = data

    # write out
    text = json.dumps(db, indent=1)
    c.json_db_file.parent.mkdir(parents=True, exist_ok=True)
    utils.write_text(c.json_db_file, text)


def create_statistics_section(
    entries: Sequence[Entry], field: str, title: str, filename: str,
    chartmaker: Callable[[list[tuple[str, int]]], str], sub_field: str | None = None,
) -> Entry:
    """
    Generate a chart and return its template section for a statistics field.

    The chart maker returns reproducible SVG text, which is written below the statistics folder of the website.
    """
    statistics = stat.get_field_statistics(entries, field, sub_field)
    statistics = stat.truncate_stats(statistics, 10)
    text = chartmaker([item for item in statistics if item[0] != 'N/A'])
    file = c.web_path.joinpath(*statistics_path, filename)
    file.parent.mkdir(parents=True, exist_ok=True)
    utils.write_text(file, text)
    section = {
        'title': title,
        'id': osg.canonical_name(title),
        'items': ['{} ({})'.format(*item) for item in statistics],
        'chart': statistics_path + [filename]
    }
    return section


def generate(entries: list[Entry], inspirations: list[Entry], developers: list[Entry]) -> None:
    """
    Regenerate the complete static website from validated source records.

    Cross-references in entries must resolve to a corresponding inspiration or
    developer record.  This function augments its input dictionaries in place while
    preparing them for Jinja rendering.
    """

    # split entries in games and non-games
    games, non_games = [], []
    for entry in entries:
        (games, non_games)[any([keyword in entry['Keyword'] for keyword in c.non_game_keywords])].append(entry)

    # preprocess
    preprocess(games, 'Title', games_path)
    preprocess(
        non_games,
        'Title',
        lambda non_game: non_games_path + [[keyword for keyword in c.non_game_keywords if keyword in non_game['Keyword']][0]]
    )
    entries = games + non_games
    preprocess(inspirations, 'Name', inspirations_path)
    preprocess(developers, 'Name', developers_path)

    # set internal links up
    convert_inspirations(inspirations, entries)
    convert_developers(developers, entries)
    entry_references = {entry['File'].name: entry['href'] for entry in entries}
    convert_entries(games, inspirations, developers, entry_references)
    convert_entries(non_games, inspirations, developers, entry_references)

    # create entries.json for the table
    create_table_json_data(entries)

    # create statistics data
    statistics_data = {
        'title': 'Statistics',
        'sections': []
    }

    # supported platforms
    section = create_statistics_section(entries, 'Platform', 'Supported platforms', 'supported_platforms.svg', partial(stat.export_bar_chart, aspect_ratio=0.7, tick_label_rotation=45))
    statistics_data['sections'].append(section)

    # code languages
    section = create_statistics_section(entries, 'Code language', 'Code languages', 'code_languages.svg', partial(stat.export_bar_chart, aspect_ratio=1.5, tick_label_rotation=45))
    statistics_data['sections'].append(section)

    # code license
    section = create_statistics_section(entries, 'Code license', 'Code licenses', 'code_licenses.svg', partial(stat.export_bar_chart, aspect_ratio=1.5, tick_label_rotation=45))
    statistics_data['sections'].append(section)

    # code dependencies
    section = create_statistics_section(entries, 'Code dependency', 'Code dependencies', 'code_dependencies.svg', partial(stat.export_bar_chart, aspect_ratio=1.5, tick_label_rotation=45))
    statistics_data['sections'].append(section)

    # build-systems
    section = create_statistics_section(entries, 'Build system', 'Build systems', 'build_systems.svg', stat.export_pie_chart, sub_field='Building')
    statistics_data['sections'].append(section)

    # set external links up (statistics and entries.json doesn't work anymore beyond that point)
    add_license_links_to_entries(entries)

    # sort into categories
    sorter = lambda item, category: category == item['letter']
    games_by_alphabet = sort_into_categories(games, extended_alphabet, sorter)
    inspirations_by_alphabet = sort_into_categories(inspirations, extended_alphabet, sorter)
    developers_by_alphabet = sort_into_categories(developers, extended_alphabet, sorter)

    genres = [keyword.capitalize() for keyword in c.recommended_keywords if keyword not in c.non_game_keywords]
    genres.sort()
    games_by_genre = sort_into_categories(games, genres, lambda item, category: category.lower() in item['Keyword'])
    games_by_platform = sort_into_categories(entries, c.valid_platforms, lambda item, category: category in item.get('Platform', []), UNKNOWN_PLATFORM)
    games_by_language = sort_into_categories(entries, c.known_languages, lambda item, category: category in item['Code language'])
    non_games_by_type = sort_into_categories(non_games, c.non_game_keywords, lambda item, category: category in item['Keyword'])

    # extract top Github stars games
    N_top = 100
    top_games = get_topN_games(games, N=N_top)

    # base dictionary
    base = {
        'title': 'OSGL',
        'description': 'Browse open source games, game engines, frameworks, and tools with technical details.',
        'creation-date': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M'),
        'css': ['bulma.min.css', 'osgl.min.css'],
        'js': ['osgl.js']
    }

    # copy css and js
    utils.copy_tree(c.web_static_path / 'css', c.web_css_path)
    utils.copy_tree(c.web_static_path / 'js', c.web_js_path)

    # copy screenshots path
    filenames = [file.name for file in c.screenshots_path.iterdir() if file.suffix == '.jpg']
    c.web_screenshots_path.mkdir(parents=True, exist_ok=True)
    for filename in filenames:
        shutil.copyfile(c.screenshots_path / filename, c.web_screenshots_path / filename)

    # collage_image and google search console token and favicon.svg
    for filename in ('collage_games.jpg', 'google1f8a3863114cbcb3.html', 'favicon.svg'):
        shutil.copyfile(c.web_static_path / filename, c.web_path / filename)

    # create Jinja Environment
    environment = create_environment(base)

    # multiple times used templates
    template_categorical_index = environment.get_template('categorical_index.jinja')
    template_listing_entries = environment.get_template('listing_entries.jinja')

    # top level folder
    base['url_to'] = partial(url_to, [])

    # index.html is generated after the sub lists (see below), because it shows their sizes

    # contribute page
    set_page_metadata(
        base,
        'OSGL | Contributions',
        'Learn how to add or improve open source game entries and give feedback to the Open Source Games List.',
    )
    base['active_nav'] = 'contribute'
    template = environment.get_template('contribute.jinja')
    write(template.render(), ['contribute.html'])

    # statistics page in statistics folder
    set_page_metadata(
        base,
        'OSGL | Statistics',
        'Explore statistics about platforms, programming languages, licenses, dependencies, and build systems in the Open Source Games List.',
    )
    base['url_to'] = partial(url_to, statistics_path)
    base['active_nav'] = 'statistics'

    # statistics preparation
    template = environment.get_template('statistics.jinja')
    # render and write statistics page
    write(template.render(data=statistics_data), statistics_index_path)

    # non-games folder
    set_page_metadata(
        base,
        'OSGL | Game engines, frameworks, tools',
        f'Browse {len(non_games)} open source game engines, frameworks, libraries, and development tools.',
    )
    base['url_to'] = partial(url_to, non_games_path)
    base['active_nav'] = 'frameworks'

    # non-games by type
    index = divide_in_three_columns_and_transform(non_games_by_type, entry_index)
    index['title'] = make_text('Open source game engines/frameworks/tools')
    index['subtitle'] = make_text(f'Index of {len(non_games)} game engines/frameworks/tools')
    index['categories'] = c.non_game_keywords
    index['category-names'] = non_game_category_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 0
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), non_games_index_path)

    # generate non-games pages
    for keyword in c.non_game_keywords:
        set_page_metadata(
            base,
            f'OSGL | {non_game_category_names[keyword]}',
            f'Browse {len(non_games_by_type[keyword])} open source {non_game_category_names[keyword].lower()} for game development.',
        )
        listing = {
            'title': non_game_category_names[keyword],
            'subtitle': make_url(non_games_index_path, 'Index'),
            'items': non_games_by_type[keyword]
        }
        write(template_listing_entries.render(listing=listing), non_games_path + [f'{keyword}.html'])

    # games folder
    set_page_metadata(
        base,
        'OSGL | Games | Alphabetical',
        f'Browse an alphabetical index of {len(games)} open source games with technical details and download links.',
    )
    base['url_to'] = partial(url_to, games_path)
    base['active_nav'] = 'games'

    # generate games pages
    for letter in extended_alphabet:
        letter_description = 'non-alphabetical titles' if letter == extra else f'titles beginning with {letter}'
        set_page_metadata(
            base,
            f'OSGL | Games | {letter}',
            f'Browse {len(games_by_alphabet[letter])} open source games with {letter_description}.',
        )
        listing = {
            'title': f'Games starting with {letter.capitalize()}',
            'items': games_by_alphabet[letter]
        }
        write(template_listing_entries.render(listing=listing), games_path + [f'{letter.capitalize()}.html'])

    # generate games index
    set_page_metadata(
        base,
        'OSGL | Games | Alphabetical',
        f'Browse an alphabetical index of {len(games)} open source games with technical details and download links.',
    )
    index = divide_in_three_columns_and_transform(games_by_alphabet, entry_index)
    index['title'] = make_text('Open source games')
    index['subtitle'] = [make_text(f'Alphabetical index of {len(games)} games.')]
    index['categories'] = extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 20
    index['category-infos'] = {letter: make_text(f'{len(games_by_alphabet[letter])} games') for letter in extended_alphabet}
    write(template_categorical_index.render(index=index), games_index_path)

    # genres
    set_page_metadata(
        base,
        'OSGL | Games | Genres',
        'Browse open source games by genre, including action, adventure, puzzle, strategy, and role-playing games.',
    )
    base['active_nav'] = ['filter', 'genres']
    index = divide_in_three_columns_and_transform(games_by_genre, entry_index)
    index['title'] = make_text('Open source games')
    index['subtitle'] = [make_text('Index by game genre.')]
    index['categories'] = genres
    index['category-names'] = {k: make_text(k) for k in index['categories']}
    index['category-icons'] = {k: make_icon(genre_icon_map[k]) for k in index['categories'] if k in genre_icon_map}
    index['number_entries_per_category_threshold'] = 50
    index['category-infos'] = {
        genre: [
            make_text(c.keyword_genre_descriptions[genre.lower()]),
            make_line_break(),
            make_text(f'{len(games_by_genre[genre])} games'),
        ]
        for genre in genres
    }
    write(template_categorical_index.render(index=index), games_by_genres_path)

    # games by language
    set_page_metadata(
        base,
        'OSGL | Games | Programming language',
        'Browse open source games and frameworks by programming language.',
    )
    base['active_nav'] = ['filter', 'code language']
    index = divide_in_three_columns_and_transform(games_by_language, entry_index)
    index['title'] = 'Open source games and frameworks'
    index['subtitle'] = [make_text('Index by programming language.')]
    index['categories'] = c.known_languages
    index['category-names'] = {k:k for k in index['categories']}
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 15
    index['category-infos'] = {category: make_url(c.language_urls[category], 'Language information', css_class='is-size-7') for category in c.known_languages if category in c.language_urls}
    write(template_categorical_index.render(index=index), games_by_language_path)

    # games by platform
    set_page_metadata(
        base,
        'OSGL | Games | Supported Platform',
        'Browse open source games and frameworks by supported platform, including Windows, Linux, macOS, mobile, and web.',
    )
    base['active_nav'] = ['filter', 'platforms']
    index = divide_in_three_columns_and_transform(games_by_platform, entry_index)
    index['title'] = 'Open source games and frameworks'
    index['subtitle'] = [make_text('Index by supported platform.')]
    index['categories'] = c.valid_platforms + (UNKNOWN_PLATFORM,)
    index['category-names'] = {k: make_text(k) for k in index['categories']}
    index['category-icons'] = {k: make_icon(platform_icon_map[k]) for k in index['categories']}
    index['number_entries_per_category_threshold'] = 15
    index['category-infos'] = {}
    index['category-infos'] = {category: make_text(f'{len(games_by_platform[category])} entries') for category in index['categories']}
    write(template_categorical_index.render(index=index), games_by_platform_path)

    # for kids games
    kids_games = [game for game in games if 'for kids' in game['Keyword']]
    set_page_metadata(
        base,
        'OSGL | Games | For Kids',
        f'Browse {len(kids_games)} open source games tagged as suitable for children.',
    )
    base['active_nav'] = ['filter', 'kids']
    listing = {
        'title': 'Games for Kids',
        'subtitle': f'{len(kids_games)} games suitable for kids.',
        'items': kids_games
    }
    write(template_listing_entries.render(listing=listing), games_kids_path)

    # playable in browser
    web_games = [game for game in games if 'Play' in game and 'Web' in game['Platform']]
    set_page_metadata(
        base,
        'OSGL | Games | Web Play',
        f'Browse {len(web_games)} open source games that can be played directly in a web browser.',
    )
    base['active_nav'] = ['filter', 'web']
    listing = {
        'title': 'Playable browser games',
        'subtitle': f'{len(web_games)} games that can be played in your browser right away.',
        'items': web_games
    }
    write(template_listing_entries.render(listing=listing), games_web_path)

    # completely free games
    libre_games = [game for game in games if 'content open' in game['Keyword']]
    set_page_metadata(
        base,
        'OSGL | Games | Free code and artwork',
        f'Browse {len(libre_games)} open source games with open or libre code and artwork.',
    )
    base['active_nav'] = ['filter', 'libre']
    index = make_alphabetical_index(
        libre_games, 'Completely free games', f'Index of {len(libre_games)} games with open/libre code and artwork.',
        'games',
    )
    write(template_categorical_index.render(index=index), games_libre_path)

    # remakes and clones of existing games (including engine reimplementations, which are non-games)
    remake_entries = [entry for entry in entries if c.remake_or_clone_keyword in entry['Keyword']]
    set_page_metadata(
        base,
        'OSGL | Games | Remakes and clones',
        f'Browse {len(remake_entries)} open source remakes and clones of existing games.',
    )
    base['active_nav'] = ['filter', 'remakes']
    index = make_alphabetical_index(
        remake_entries, 'Remakes and clones',
        f'Index of {len(remake_entries)} games and engines that recreate, port or reimplement existing games.',
        'entries',
    )
    write(template_categorical_index.render(index=index), games_remakes_path)

    # top github/gitlab games
    set_page_metadata(
        base,
        f'OSGL | Games | Top stars {N_top}',
        f'Browse the {N_top} highest-starred immediately playable open source games in the Open Source Games List.',
    )
    base['active_nav'] = ['filter', f'top']
    # there are no other games coming afterward, can actually number them
    for index, game in enumerate(top_games):
        game['name'] = f'{index + 1}. ' + game['name']
    listing = {
        'title': f'Top stars {N_top}',
        'subtitle': f'{N_top} highest rated (by stars on Github or Gitlab) immediately downloadable and playable open source games in the database.', # that can be played online or downloaded
        'items': top_games
    }
    write(template_listing_entries.render(listing=listing), games_top_path)

    # index.html (main page, top level folder) with key numbers and tiles for selected genres and sub lists
    set_page_metadata(
        base,
        'OSGL | Open source games list',
        f'Browse technical information about {len(games)} open source games and {len(non_games)} game engines, frameworks, and tools.',
    )
    base['url_to'] = partial(url_to, [])
    base['active_nav'] = 'index'
    index_lists = (
        (games_web_path, 'earth', 'Playable in the browser', len(web_games), 'games'),
        (games_libre_path, 'heart', 'Open code + artwork', len(libre_games), 'games'),
        (games_remakes_path, 'undo', 'Remakes and clones', len(remake_entries), 'entries'),
        (games_top_path, 'star', 'Top by stars', len(top_games), 'games'),
        (games_kids_path, 'child', 'For kids', len(kids_games), 'games'),
    )
    index = create_index_data(games, non_games, developers, inspirations, games_by_genre, index_lists)
    template = environment.get_template('index.jinja')
    write(template.render(index=index), ['index.html'])

    # inspirations folder
    set_page_metadata(
        base,
        'OSGL | Inspirational games',
        f'Browse {len(inspirations)} games that inspired projects in the Open Source Games List.',
    )
    base['url_to'] = partial(url_to, inspirations_path)
    base['active_nav'] = 'inspirations'

    # inspirations

    # inspirations single pages
    template_listing_inspirations = environment.get_template('listing_inspirations.jinja')
    for letter in extended_alphabet:
        letter_description = 'non-alphabetical titles' if letter == extra else f'names beginning with {letter}'
        set_page_metadata(
            base,
            f'OSGL | Inspirations | {letter}',
            f'Browse {len(inspirations_by_alphabet[letter])} inspirational games with {letter_description}.',
        )
        listing = {
            'title': f'Inspirations ({letter.capitalize()})',
            'items': inspirations_by_alphabet[letter]
        }
        write(template_listing_inspirations.render(listing=listing), inspirations_path + [f'{letter.capitalize()}.html'])

    # inspirations index
    set_page_metadata(
        base,
        'OSGL | Inspirational games',
        f'Browse an alphabetical index of {len(inspirations)} games that inspired open source projects.',
    )
    extended_alphabet_names['_'] = 'Most used'
    top_inspirations = [inspiration for inspiration in inspirations if len(inspiration['Inspired entries']) >= TOP_INSPIRATION_THRESHOLD]
    inspirations_by_alphabet['_'] = top_inspirations
    index = divide_in_three_columns_and_transform(inspirations_by_alphabet, inspiration_index)
    index['title'] = 'Inspirations'
    index['subtitle'] = make_text(f'Alphabetical index of {len(inspirations)} games used as inspirations')
    index['categories'] = '_' + extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 10
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), inspirations_index_path)

    # developers folder
    set_page_metadata(
        base,
        'OSGL | Games | Developers',
        f'Browse {len(developers)} developers and organizations behind open source games and frameworks.',
    )
    base['url_to'] = partial(url_to, developers_path)
    base['active_nav'] = 'developers'

    # developers single pages
    template_listing_developers = environment.get_template('listing_developers.jinja')
    for letter in extended_alphabet:
        letter_description = 'non-alphabetical names' if letter == extra else f'names beginning with {letter}'
        set_page_metadata(
            base,
            f'OSGL | Developers | {letter}',
            f'Browse {len(developers_by_alphabet[letter])} open source game developers with {letter_description}.',
        )
        listing = {
            'title': f'Open source game developers ({letter.capitalize()})',
            'items': developers_by_alphabet[letter]
        }
        write(template_listing_developers.render(listing=listing), developers_path + [f'{letter.capitalize()}.html'])

    # developers index
    set_page_metadata(
        base,
        'OSGL | Games | Developers',
        f'Browse an alphabetical index of {len(developers)} open source game developers and organizations.',
    )
    extended_alphabet_names['_'] = 'Most active'
    top_developers = [developer for developer in developers if len(developer['Games']) >= TOP_DEVELOPER_THRESHOLD]
    developers_by_alphabet['_'] = top_developers
    index = divide_in_three_columns_and_transform(developers_by_alphabet, developer_index)
    index['title'] = 'Open source game developers'
    index['subtitle'] = make_text(f'Alphabetical index of {len(developers)} developers')
    index['categories'] = '_' + extended_alphabet
    index['category-names'] = extended_alphabet_names
    index['category-icons'] = {}
    index['number_entries_per_category_threshold'] = 10
    index['category-infos'] = {}
    write(template_categorical_index.render(index=index), developers_index_path)

    # dynamic table (is in top level folder)
    set_page_metadata(
        base,
        'OSGL | Entries | Table',
        'Search and sort the complete Open Source Games List by title, state, tags, platform, programming language, and license.',
    )
    base['url_to'] = partial(url_to, [])
    base['css'].append('simple-datatables.css')
    base['js'].append('simple-datatables.js')
    base['active_nav'] = 'table'
    template = environment.get_template('table.jinja')
    index['tags'] = make_text(', '.join(c.interesting_keywords))
    index['platforms'] = make_text(', '.join(c.valid_platforms))
    write(template.render(index=index), ['table.html'])


def main():
    """
    Regenerates the static website in the docs folder from entries, inspirations and developers.
    """

    start_time = time.process_time()

    # create dictionary of file hashes
    print('estimate file hashes')
    for dirpath, dirnames, filenames in c.web_path.walk():
        for filename in filenames:
            if filename.endswith('.html'):
                filename = dirpath / filename
                text = utils.read_text(filename)
                previous_files[filename] = {'hash': file_hash(text), 'text': text}

    # clean the output directory
    print('clean current static website')
    utils.recreate_directory(c.web_path)

    # load entries, inspirations and developers and sort them alphabetically
    print('load entries, inspirations and developers')
    entries = osg.read_entries()
    entries.sort(key=lambda x: str.casefold(x['Title']))

    # add screenshot information
    add_screenshot_information(entries)

    inspirations = osg.read_inspirations()
    inspirations = list(inspirations.values())
    inspirations.sort(key=lambda x: str.casefold(x['Name']))
    # remove orphaned inspirations for the website creation
    inspirations = [inspiration for inspiration in inspirations if inspiration['Inspired entries']]

    developers = osg.read_developers()
    developers = list(developers.values())
    developers.sort(key=lambda x: str.casefold(x['Name']))
    # remove orphaned developers for the website creation
    developers = [developer for developer in developers if developer['Games']]

    # re-generate static website
    print('re-generate static website')
    generate(entries, inspirations, developers)

    # timing
    print(f'took {time.process_time() - start_time:.3f}s')


if __name__ == "__main__":
    main()
