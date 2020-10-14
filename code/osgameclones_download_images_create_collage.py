"""
  Downloads images from games, stored in the osgameclones-database, then creates a collage of them.
"""

import ruamel.yaml as yaml
import os
import requests
from PIL import Image
from io import BytesIO

if __name__ == "__main__":

    # paths
    root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    download_path = os.path.join(root_path, 'code', 'html', 'images-download')
    output_file = os.path.join(root_path, 'code', 'html', 'collage_games.jpg')

    # import the osgameclones data
    path = os.path.realpath(os.path.join(root_path, os.path.pardir, 'osgameclones.git', 'games'))
    files = os.listdir(path)

    # iterate over all yaml files in osgameclones/data folder and load contents
    entries = []
    for file in files:
        # read yaml
        with open(os.path.join(path, file), 'r', encoding='utf-8') as stream:
            try:
                _ = yaml.safe_load(stream)
            except Exception as exc:
                print(file)
                raise exc

        # add to entries
        entries.extend(_)

    print('imported {} entries'.format(len(entries)))

    # collect all image informations
    images = []
    for entry in entries:
        if 'images' in entry:
            images.extend(entry['images'])

    print('contain {} image links'.format(len(images)))

    # download them all
    for url in images:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'},
                     timeout=20, allow_redirects=True)

        if r.status_code == requests.codes.ok:
            im = Image.open(BytesIO(r.content))