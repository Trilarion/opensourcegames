"""
Central place to calculate statistics about the entries. Used for updating the statistics.md file and the statistics page
of the website. Also renders statistics diagrams.
"""

import io
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence

import matplotlib
import numpy as np
from matplotlib.figure import Figure

BASE_FIGURE_SIZE = 4

# fixed salt for the element ids of the SVG output, makes the output reproducible
SVG_HASH_SALT = 'osgl'


def get_field_statistics(
    entries: Iterable[Mapping], field: str, sub_field: str | None = None, include_na: bool = True,
) -> list[tuple[str, int]]:
    """
    Count how often each value of a field occurs in the given entries.

    :param entries: list of entries
    :param field: name of the field whose values are counted
    :param sub_field: if given, the field is looked up inside this sub field of each entry (e.g. 'Building')
    :param include_na: if true, entries without the field are counted as 'N/A'
    :return: list of tuples (field value, occurrences) sorted by descending occurrences, then by name
    """
    counter = Counter()
    for entry in entries:
        if sub_field:
            entry = entry[sub_field]
        if field in entry:
            counter.update(entry[field])
        elif include_na:
            counter['N/A'] += 1

    # highest occurrence first, then case-insensitive by name (the name itself as final tie-breaker)
    return sorted(counter.items(), key=lambda item: (-item[1], str.casefold(item[0]), item[0]))


def truncate_stats(
    stat: Sequence[tuple[str, int]], threshold: int, name: str = 'Other',
) -> list[tuple[str, int]]:
    """
    Combine all items (value, count) with a count below the threshold into a single item.

    :param stat: statistics as returned by get_field_statistics
    :param threshold: items with a count below this value are combined
    :param name: name of the combined item
    :return: the items at or above the threshold (in the original order), followed by the combined item if any items
        were combined
    """
    kept = [item for item in stat if item[1] >= threshold]
    combined_count = sum(item[1] for item in stat if item[1] < threshold)
    if combined_count > 0:
        kept.append((name, combined_count))
    return kept


def _figure_to_svg(figure: Figure) -> str:
    """
    Render a figure as SVG text.

    The output is reproducible: the element ids use a fixed salt and the creation date is omitted, so the same chart
    always gives the same text.
    """
    buffer = io.StringIO()
    with matplotlib.rc_context({'svg.hashsalt': SVG_HASH_SALT}):
        figure.savefig(buffer, format='svg', transparent=True, metadata={'Date': None})
    return buffer.getvalue()


def export_pie_chart(stat: Sequence[tuple[str, int]]) -> str:
    """
    Create a pie chart of the given statistics and return it as SVG text.
    """
    labels = [item[0] for item in stat]
    sizes = [item[1] for item in stat]

    figure = Figure(figsize=(BASE_FIGURE_SIZE, BASE_FIGURE_SIZE), tight_layout=True)
    axes = figure.add_subplot()
    axes.pie(sizes, labels=labels, autopct='%1.1f%%', pctdistance=0.8, shadow=True, labeldistance=1.2, normalize=True)

    return _figure_to_svg(figure)


def export_bar_chart(stat: Sequence[tuple[str, int]], aspect_ratio: float = 1, tick_label_rotation: float = 0) -> str:
    """
    Create a bar chart of the given statistics and return it as SVG text.

    :param aspect_ratio: width of the figure relative to its height
    :param tick_label_rotation: rotation of the labels on the x axis in degrees
    """
    positions = np.arange(len(stat))
    labels = [item[0] for item in stat]
    heights = [item[1] for item in stat]

    figure = Figure(figsize=(aspect_ratio * BASE_FIGURE_SIZE, BASE_FIGURE_SIZE), tight_layout=True)
    axes = figure.add_subplot()
    bars = axes.bar(positions, heights, tick_label=labels, edgecolor='black')
    axes.bar_label(bars)
    axes.spines['top'].set_visible(False)
    axes.spines['right'].set_visible(False)
    axes.tick_params(axis='x', labelrotation=tick_label_rotation)

    return _figure_to_svg(figure)
