"""
Tests for small helper modules: archive folder names, repository name normalization and statistics.
"""

import pytest

from osgl import archive, statistics
from osgl.external import github, gitlab


# Archive folder names (must be stable, otherwise the local archive gets cloned again)


@pytest.mark.parametrize('url, expected', [
    ('https://github.com/example/sample.git', 'github.example.sample.git'),
    ('https://gitlab.com/group/sub/project.git', 'gitlab.group.sub.project.git'),
    ('https://git.code.sf.net/p/game/code', 'sourceforge.game.code'),
    ('https://anongit.kde.org/game.git', 'kde.org.game.git'),
    ('https://example.org/repo.git', 'example.org.repo.git'),
    ('git://example.org/repo.git', 'example.org.repo.git'),
])
def test_git_folder_name(url, expected):
    """
    Known services are shortened, other URLs only lose their scheme, slashes become dots.
    """
    assert archive.git_folder_name(url) == expected


def test_derive_folder_name_malformed_url():
    """
    URLs without a known scheme are rejected.
    """
    with pytest.raises(RuntimeError, match='malformed url'):
        archive.derive_folder_name('example.org/repo', {})


# Repository names


@pytest.mark.parametrize('module, url', [
    (github, 'https://github.com/example/sample.git'),
    (gitlab, 'https://gitlab.com/example/sample.git'),
])
def test_normalize_repo_name(module, url):
    """
    Repository URLs are reduced to owner/name.
    """
    assert module.normalize_repo_name(url) == 'example/sample'
    assert module.normalize_repo_name('example/sample') == 'example/sample'


# Statistics


ENTRIES = [
    {'Code language': ['C', 'Lua'], 'Building': {'Build system': ['CMake']}},
    {'Code language': ['C'], 'Building': {}},
    {'Building': {'Build system': ['Make']}},
]


def test_get_field_statistics():
    """
    Values are counted, sorted by occurrence and then by name, missing fields count as N/A.
    """
    assert statistics.get_field_statistics(ENTRIES, 'Code language') == [('C', 2), ('Lua', 1), ('N/A', 1)]
    assert statistics.get_field_statistics(ENTRIES, 'Code language', include_NA=False) == [('C', 2), ('Lua', 1)]


def test_get_field_statistics_sub_field():
    """
    Fields in a sub field (e.g. Building) can be evaluated.
    """
    stats = statistics.get_field_statistics(ENTRIES, 'Build system', sub_field='Building')
    assert stats == [('CMake', 1), ('Make', 1), ('N/A', 1)]


def test_truncate_stats():
    """
    Items below the threshold are combined into a single last item.
    """
    stats = [('C', 20), ('Lua', 3), ('Go', 2)]
    assert statistics.truncate_stats(stats, 10) == [('C', 20), ['Other', 5]]
    assert statistics.truncate_stats(stats, 1) == stats


@pytest.mark.parametrize('export', [statistics.export_pie_chart, statistics.export_bar_chart])
def test_export_charts(tmp_path, export):
    """
    Charts are written as SVG files, the containing folder is created if needed.
    """
    file = tmp_path / 'charts' / 'chart.svg'
    export([('C', 2), ('Lua', 1)], file)
    assert file.read_text(encoding='utf-8').lstrip().startswith('<?xml')
