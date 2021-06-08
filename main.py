import argparse
import cv2

from geometry.cubemap import Cubemap
from geometry.unitsphere import UnitSphere

"""
Convert between 2:1 equirectangular panorama (e.g. from a 360° camera)
to other formats such as a cubemap

This script was written as a quick utility for myself, I tried to keep it
simple.
"""

def main(args):
    """
    Compute 6 cubemap images from an equirectangular image, and write them
    into the output/ directory.
    """
    sphere = UnitSphere(args.image_equirectangular)
    cubemap = Cubemap(shape=(args.size, args.size, 3))
    cubemap.project_from(sphere)
    cubemap.write("output/skybox{}.png")

def image(fname):
    """
    Argument type conversion function for an image. This just throws exceptions
    if the read fails.

    :param str fname: The filename of the image to load
    :return: The image if OpenCV was able to read it.
    :rtype: numpy.ndarray
    """
    return cv2.imread(fname)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("image_equirectangular",
        type=image,
        help="Image to turn into a cubemap. It must be a 2:1 equirectangular image")
    parser.add_argument("-s", '--size',
        type=int,
        default=2048,
        help="Texture size for each face of the cubemap Defaults to 2048")
    parser.add_argument("-p", "--prefix",
        default="skybox",
        help="Prefix for the filename. For example, if this is 'skybox', output files will look like 'output/skybox+x.png'")
    args = parser.parse_args()

    main(args)