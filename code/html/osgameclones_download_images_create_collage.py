"""
  Downloads images from games, stored in the osgameclones-database, then creates a collage of them.
"""

import ruamel.yaml as yaml
import os
import requests
from PIL import Image
from io import BytesIO
import numpy as np

from progress.bar import IncrementalBar

def download_images():
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
        name = "".join(x for x in url[5:] if (x.isalnum() or x in '._-'))
        outfile = os.path.join(download_path, name)
        if not os.path.isfile(outfile):
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'},
                             timeout=20, allow_redirects=True)
                if r.status_code == requests.codes.ok:
                    im = Image.open(BytesIO(r.content))
                    im.save(outfile)
                    print('saved {}'.format(url))
            except:
                pass

def downsize_images():
    scale_factor = 10
    for file in os.listdir(download_path):
        file_path = os.path.join(download_path, file)
        if not os.path.isfile(file_path):
            continue
        outfile = os.path.join(downsized_path, file[:-4]+'.png')  # losless storage of downsize image
        if os.path.isfile(outfile):
            continue
        im = Image.open(file_path)
        if im.mode != 'RGB':
            print('{} - {}'.format(file, im.mode))
            continue
        width = im.width
        height = im.height
        if width < target_width * scale_factor or height < target_height * scale_factor:
            continue
        box = [(width-target_width*scale_factor)/2, (height-target_height*scale_factor)/2, target_width * scale_factor, target_height * scale_factor]
        box[2] += box[0]
        box[3] += box[1]
        im_resized = im.resize((target_width, target_height), resample=Image.LANCZOS, box=box)
        im_resized.save(outfile)
        print('saved {}'.format(file))


def assemble_collage():
    print('start assembling collage')

    # load all from downsized path
    files = os.listdir(downsized_path)
    files = [file for file in files if os.path.isfile(os.path.join(downsized_path, file))]
    images = []
    bar = IncrementalBar('Loading', max=len(files))
    for file in files:
        im = Image.open(os.path.join(downsized_path, file))
        im = np.asarray(im)
        images.append(im)
        bar.next()
    bar.finish()

    # compute total amount of light in each image and only keep the N brightest
    images = [(np.sum(image), image) for image in images]
    images.sort(key=lambda x: x[0], reverse=True)
    images = images[:N]
    images = [x[1] for x in images]

    # compute the average color in each quadrant
    Cx = int(target_height / 2)
    Cy = int(target_width / 2)
    U = [np.mean(image[:Cx, :, :], axis=(1, 2)) for image in images]
    D = [np.mean(image[Cx:, :, :], axis=(1, 2)) for image in images]
    R = [np.mean(image[:, :Cy, :], axis=(1, 2)) for image in images]
    L = [np.mean(image[:, Cy:, :], axis=(1, 2)) for image in images]

    # initially just sort them in randomly
    map = np.random.permutation(N).reshape((Nx, Ny))

    # optimize neighbors with a stochastic metropolis algorithm
    Ni = 500000
    T = np.linspace(150, 2, Ni)
    A = np.zeros((Ni, 1))
    u = lambda x: (x + 1) % Nx
    d = lambda x: (x - 1) % Nx
    r = lambda x: (x + 1) % Ny
    l = lambda x: (x - 1) % Ny
    score = lambda i1, j1, i2, j2: np.linalg.norm(U[map[i1, j1]] - D[map[u(i2), j2]]) + np.linalg.norm(D[map[i1, j1]] - U[map[d(i2), j2]]) + np.linalg.norm(L[map[i1, j1]] - R[map[i2, l(j2)]]) + np.linalg.norm(R[map[i1, j1]] - L[map[i2, r(j2)]])
    bar = IncrementalBar('Optimization', max=Ni)
    for ai in range(Ni):
        # get two non-equal random locations
        i1 = np.random.randint(Nx)
        j1 = np.random.randint(Ny)
        while True:
            i2 = np.random.randint(Nx)
            j2 = np.random.randint(Ny)
            if i1 != i2 or j1 != j2:
                break
        # compute score
        x = score(i1, j1, i1, j1) - score(i1, j1, i2, j2) + score(i2, j2, i2, j2) - score(i2, j2, i1, j1)

        # exchange
        # if x < 0:
        # if x > 0:
        if x > 0 or np.exp(x / T[ai]) > np.random.uniform():
            map[i1, j1], map[i2, j2] = map[i2, j2], map[i1, j1]
            A[ai] = 1

        bar.next()
    bar.finish()
    # time evolution of acceptance rate
    Nc = int(np.floor(Ni / 20))
    for ai in range(20):
        print('{}: {}'.format(ai, np.mean(A[ai*Nc:(ai+1)*Nc])))

    # shift brightest to center
    B = np.zeros((Nx, Ny))
    for i in range(Nx):
        for j in range(Ny):
            B[i, j] = np.sum(images[map[i, j]])
    sk = np.array([0.25, 0.5, 1, 0.5, 0.25])
    # convolve in 1D along all rows and all columns
    for i in range(Nx):
        B[i, :] = np.convolve(B[i, :], sk, mode='same')
    for j in range(Ny):
        B[:, j] = np.convolve(B[:, j], sk, mode='same')
    cx, cy = np.unravel_index(np.argmax(B), B.shape)
    map = np.roll(map, (int(Nx/2-cx), int(Ny/2-cy)), axis=(0, 1))

    # assemble image
    final = np.zeros((Nx * target_height, Ny * target_width, 3), dtype=np.uint8)
    for i in range(Nx):
        for j in range(Ny):
            final[i*target_height:(i+1)*target_height, j*target_width:(j+1)*target_width] = images[map[i, j]]

    # convert back to pillow image and save
    im = Image.fromarray(final)
    im.save(output_file)


if __name__ == "__main__":

    target_height = 60
    target_width = 80

    Nx = 12  # vertical
    Ny = 18  # horizontal
    N = Nx * Ny

    # paths
    root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    download_path = os.path.join(root_path, 'code', '', 'images-download')
    downsized_path = os.path.join(download_path, 'downsized')
    output_file = os.path.join(root_path, 'code', '', 'collage_games.jpg')
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    if not os.path.exists(downsized_path):
        os.mkdir(downsized_path)

    # download files
    # download_images()

    # downsize downloaded images
    # downsize_images()

    # assemble collage
    assemble_collage()