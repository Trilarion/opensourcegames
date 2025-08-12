"""
Central place to calculate statistics about the entries. Used for updating the statistics.md file and the statistics page
of the website. Also renders statistics diagrams.
"""

import numpy as np
import matplotlib.pyplot as plt

BASE_FIGURE_SIZE = 4


def get_field_statistics(entries, field, sub_field=None, include_NA=True):
    """
    Given a list of entries, calculates statistics about a field content and returns the statistics.

    If include_NA is True, N/A is used if no field was specified

    :param entries: list of entries
    :param include_NA: If true, adds N/A if field is not contained in entry
    :return: list of tuples (field content, occurrence) sorted by descending occurrences
    """

    # gather field content
    values = []
    for entry in entries:
        if sub_field:
            entry = entry[sub_field]
        if field in entry:
            values.extend(entry[field])
        elif include_NA:
            values.append('N/A')

    # unique field content
    unique_values = set(values)

    # count occurrences and sort
    values_stat = [(l, values.count(l)) for l in unique_values]
    values_stat.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
    values_stat.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)

    return values_stat


def truncate_stats(stat, threshold, name='Other'):
    """
    Combines all entries (name, count) with a count below the threshold and appends a new entry

    :return: Truncated statistics with the last item being the sum of all truncated items.
    """
    a, b = [], []
    for s in stat:
        (a, b)[s[1] < threshold].append(s)
    c = 0
    for s in b:
        c += s[1]
    if c > 0:
        a.append([name, c])
    return a


def export_pie_chart(stat, file):
    """
    Given a statistics, creates a pie chart using matplotlib and exports it into a file as SVG.
    """
    labels = [x[0] for x in stat]
    sizes = [x[1] for x in stat]

    # create pie chart
    fig, ax = plt.subplots(figsize=[BASE_FIGURE_SIZE,BASE_FIGURE_SIZE], tight_layout=True)
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', pctdistance=0.8, shadow=True, labeldistance=1.2, normalize=True)

    # create output directory if necessary
    containing_dir = file.parent
    if not containing_dir.is_dir():
        containing_dir.mkdir()

    # save figure
    plt.savefig(file, transparent=True)  # TODO can we also just generate svg in text form and save later?


def export_bar_chart(stat, file, aspect_ratio = 1, tick_label_rotation=0):
    """
    Given a statistics, creates a bar chart using matplotlib and exports it into a file as SVG.
    """
    x = np.arange(len(stat))
    tick_label, height = [[x[i] for x in stat] for i in (0, 1)]

    # create pie chart
    fig, ax = plt.subplots(figsize=[aspect_ratio*BASE_FIGURE_SIZE,BASE_FIGURE_SIZE], tight_layout=True)
    p = ax.bar(x, height, tick_label=tick_label, edgecolor='black')
    ax.bar_label(p)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(rotation=tick_label_rotation)

    # create output directory if necessary
    containing_dir = file.parent
    if not containing_dir.is_dir():
        containing_dir.mkdir()

    # save figure
    plt.savefig(file, transparent=True)