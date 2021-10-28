"""
Central place to calculate statistics about the entries. Used for updating the statistics.md file and the statistics page
of the website.
"""

import os
import matplotlib.pyplot as plt


def get_supported_platforms(entries):
    """

    :param entries:
    :return:
    """
    supported_platforms = []
    for entry in entries:
        supported_platforms.extend((entry.get('Platform', ['N/A'])))

    unique_supported_platforms = set(supported_platforms)

    supported_platforms_stat = [(l, supported_platforms.count(l)) for l in unique_supported_platforms]
    supported_platforms_stat.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
    supported_platforms_stat.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)

    return supported_platforms_stat


def get_build_systems(entries):
    """
    Given a list of entries, calculates statistics about the used build systems and returns the statistics as
    sorted list of elements (build-system-name, occurence).
    "n/a" is used if no build system was specified
    """
    build_systems = []
    for entry in entries:
        build_systems.extend(entry['Building'].get('Build system', ['N/A']))

    unique_build_systems = set(build_systems)

    build_systems_stat = [(l, build_systems.count(l)) for l in unique_build_systems]
    build_systems_stat.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
    build_systems_stat.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)

    return build_systems_stat


def truncate_stats(stat, threshold, name='Other'):
    """
    Combines all entries (name, count) with a count below the threshold and appends a new entry
    """
    a, b = [], []
    for s in stat:
        (a, b)[s[1] < threshold].append(s)
    c = 0
    for s in b:
        c += s[1]
    a.append([name, c])
    return a


def export_pie_chart(stat, file):
    """

    :param stat:
    :return:
    """
    labels = [x[0] for x in stat]
    sizes = [x[1] for x in stat]

    fig, ax = plt.subplots(figsize=[4,4], tight_layout=True)
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', pctdistance=0.8, shadow=True, labeldistance=1.2)
    # create output directory if necessary
    containing_dir = os.path.dirname(file)
    if not os.path.isdir(containing_dir):
        os.mkdir(containing_dir)
    plt.savefig(file, transparent=True)  # TODO can we also just generate svg in text form and save later?
