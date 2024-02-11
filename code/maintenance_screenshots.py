"""
Updates the readme for screenshots
"""

import os
from PIL import Image

from utils import constants as c, osg

HEIGHT = 128

if __name__ == "__main__":

    # read available screenshots (and get widths and heights)
    files = {}
    for file in os.listdir(c.screenshots_path):
        path = os.path.join(c.screenshots_path, file)
        if os.path.isdir(path) or path == c.screenshots_file:
            continue
        if not file.endswith('.jpg'):
            print('Screenshot with unexpected extension: {}'.format(file))
            continue
        # read with pillow and get width and height
        with Image.open(path) as im:
            sz = [im.width, im.height]
            if sz[1] != HEIGHT:
                print('Screenshot with unexpected height: {} {}'.format(file, sz[1]))
        # parse file name (name_xx.jpg)
        name = file[:-7]
        id = int(file[-6:-4])
        if name not in files:
            files[name] = {}
        files[name][id] = sz

    # read overview
    overview = osg.read_screenshots_overview()
    print('entries with screenshots {}'.format(len(overview)))

    # compare both

    # same keys
    a = set(files.keys())
    b = set(overview.keys())
    ab = a - b
    ba = b - a
    if ab:
        print('Names in screenshot files but not in overview: {}'.format(ab))
    if ba:
        print('Names in overview but not in screenshot files: {}'.format(ba))

    # update screenshots overview
    for name, a in overview.items():  # iterate over overview items
        b = files[name]  # get corresponding file information
        for id, ai in a.items():  # iterate over overview screenshots
            bi = b[id]  # get corresponding file information
            ai[0] = bi[0]  # update width and height
            ai[1] = bi[1]

    # update screenshots overview
    osg.write_screenshots_overview(overview)