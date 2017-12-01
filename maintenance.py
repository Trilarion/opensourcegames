"""
    Counts the number of records each subfolder and updates the overview. Sorts the entries in the contents files of
    each subfolder alphabetically.
"""

import os
import re

readme_regex = re.compile(r"- \[(.+)\]\((.+)\/_toc.md\)")
toc_regex = re.compile(r"- \[(.+)\]\((.+)\)")

if __name__ == "__main__":

    # readme file location
    base_path = os.path.abspath(os.path.dirname(__file__))
    readme_path = os.path.join(base_path, 'README.md')

    # read readme
    with open(readme_path) as f:
        readme_lines = f.readlines()

    # apply regex search on all lines
    matched_lines = [readme_regex.findall(line) for line in readme_lines]

    # empty subfolder list
    subfolders = []

    # loop over the lines
    for line, match in enumerate(matched_lines):
        if match:
            # get first group (should be only one)
            match = match[0]

            # add to subfolders list
            subfolders.append(match[1])

            # subfolder path
            subfolder_path = os.path.join(base_path, match[1])

            # get number of files in that path (-1 for _toc.md)
            n = len(os.listdir(subfolder_path)) - 1

            # generate new line
            readme_lines[line] = "- [{}]({}/_toc.md) ({})\n".format(match[0], match[1], n)

    # write readme again
    with open(readme_path, "w") as f:
        f.writelines(readme_lines)

    # loop over all subfolders
    for subfolder in subfolders:

        # get contents file of that subfolder
        toc_path = os.path.join(base_path, subfolder, '_toc.md')

        # read contents file
        with open(toc_path) as f:
            toc = f.readlines()

        # only if there are at least 4 lines (header, empty, two entries)
        if len(toc) >= 4:

            # apply regex search on all entries (should work on all)
            matched_entries = [toc_regex.findall(line)[0] for line in toc[2:]]

            # sort according to first entry
            matched_entries.sort(key=lambda x: x[0])

            # generate links again
            lines = ["- [{}]({})\n".format(*match) for match in matched_entries]

            # reassemble toc
            toc = toc[0:2]
            toc.extend(lines)

            # write contents file again
            with open(toc_path, "w") as f:
                f.writelines(toc)
