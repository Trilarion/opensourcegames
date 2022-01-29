"""
Import of the screenshots by bzt in https://forum.freegamedev.net/viewtopic.php?f=20&t=12175

work on atrinik
HTTPSConnectionPool(host='www.atrinik.org', port=443): Max retries exceeded with url: /index4d0c.png?action=gallery;sa=viewpic;id=38 (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1131)')))


work on batrachians
HTTPSConnectionPool(host='perso.b2b2c.ca', port=443): Max retries exceeded with url: /~sarrazip/dev/images/batrachians-1.png (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1131)')))


work on burgerspace
HTTPSConnectionPool(host='perso.b2b2c.ca', port=443): Max retries exceeded with url: /~sarrazip/dev/images/burgerspace-1.png (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1131)')))


work on carnage3d
C:\Users\Jaggy\miniconda3\envs\py38_generic\lib\site-packages\PIL\Image.py:975: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(

work on decker
HTTPSConnectionPool(host='web.archive.org', port=443): Read timed out. (read timeout=5)

work on gnome_hearts
HTTPSConnectionPool(host='web.archive.org', port=443): Max retries exceeded with url: /web/20160314002856im_/http://www.jejik.com/images/hearts/hearts_medium.png (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x000001CC12F414F0>, 'Connection to web.archive.org timed out. (connect timeout=5)'))
"""

# TODO do not add if already 3, but print warning instead

import os
import requests
from io import BytesIO
from PIL import Image
from utils import utils as u, constants as c, osg as osg

if __name__ == "__main__":
    # paths
    root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))

    # read content of screenshots_bzt.txt
    info = u.read_text(os.path.join(root_path, 'code', 'synchronization', 'screenshots_bzt.txt'))
    info = info.split('\n') # split on line end
    info = [entry.split('\t') for entry in info] # split on tabs
    info = [[entry[0].strip(), entry[-1].strip()] for entry in info] # only keep first and last (in case multiple tabs were used)

    # read our screenshots
    screenshots = osg.read_screenshots_overview()

    # iterate over all new info
    for entry in info:
        name = entry[0]
        print('work on {}'.format(name))
        url = entry[1]

        # is contained?
        our_screenshots = screenshots.get(name, {})
        our_urls = [x[2] for x in our_screenshots.values()]
        if url not in our_urls:
            # down image
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}, timeout=5,
                                 allow_redirects=True)
            except Exception as e:
                print(e)
                # SSLError or other
                continue
            url = r.url  # just in case it got redirected
            if r.status_code == requests.codes.ok:
                try:
                    im = Image.open(BytesIO(r.content))
                except Exception as e:
                    # PIL.UNidentifiedImageError
                    print(e)
                    continue
                if im.mode != 'RGB':
                    im = im.convert('RGB')
                width = im.width
                height = im.height
                target_height = 128
                target_width = int(width / height * target_height)
                im_resized = im.resize((target_width, target_height), resample=Image.LANCZOS)
                idx = len(our_screenshots) + 1
                if any([url.startswith(x) for x in ('https://camo.githubusercontent', 'https://web.archive.org', ' https://user-content.gitlab', 'https://user-images.githubusercontent')]) or width <= 320:
                    url = '!' + url
                our_screenshots[idx] = [target_width, target_height, url]
                # store
                outfile = os.path.join(c.screenshots_path +'2', '{}_{:02d}.jpg'.format(name, idx))
                im_resized.save(outfile)
        if our_screenshots:
            screenshots[name] = our_screenshots

    # finally update screenshots readme
    osg.write_screenshots_overview(screenshots)