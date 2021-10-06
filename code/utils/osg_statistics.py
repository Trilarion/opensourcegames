"""
Central place to calculate statistics about the entries. Used for updating the statistics.md file and the statistics page
of the website.
"""


def get_build_systems(entries):
    """
    Given a list of entries, calculates statistics about the used build systems and returns the statistics as
    sorted list of elements (build-system-name, occurence).
    "n/a" is used if no build system was specified
    """
    build_systems = []
    for entry in entries:
        build_systems.extend(entry['Building'].get('Build system', ['n/a']))

    unique_build_systems = set(build_systems)

    build_systems_stat = [(l, build_systems.count(l)) for l in unique_build_systems]
    build_systems_stat.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
    build_systems_stat.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)

    return build_systems_stat
