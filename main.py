#!/usr/bin/env python3
import argparse
from geometry.stereographic import StereographicProjection
import cv2

from geometry.cubemap import Cubemap
from geometry.unitsphere import UnitSphere

INPUT_FORMATS = [
    "sphere",
    "stereographic"
]

OUTPUT_FORMATS = [
    "cubemap",
    "sphere"
]

"""
Convert between 2:1 equirectangular panorama (e.g. from a 360° camera)
to other formats such as a cubemap

This script was written as a quick utility for myself, I tried to keep it
simple.
"""

def make_input_image(input_format, images):
    if input_format == "sphere":
        [equirectangular] = images
        return UnitSphere(image=equirectangular)
    # stereographic
    else:
        return StereographicProjection(hemispheres=images)

def make_output_image(output_format, shape):
    if output_format == "cubemap":
        return Cubemap(shape=shape)
    if output_format == "sphere":
        return UnitSphere(shape=shape)

def main(args):
    """
    Compute 6 cubemap images from an equirectangular image, and write them
    into the output/ directory.
    """
    input_image = make_input_image(args.input_format, args.input_images)
    output_pattern = f"output/{args.prefix}{{}}.png"
    
    # Exit early if input == output
    if args.input_format == args.output_format:
        print("Input format = output format. Copying files.")
        input_image.write(output_pattern)
        return

    output_image = make_output_image(args.output_format, args.output_shape)

    input_is_sphere = args.input_format == "sphere"
    output_is_sphere = args.output_format == "sphere"

    try:
        if input_is_sphere:
            output_image.project_from(input_image)
            output_image.write(output_pattern)
        elif output_is_sphere:
            input_image.unproject_to(output_image)
            output_image.write(output_pattern)
        else:
            raise NotImplementedError
    except NotImplementedError:
        print(f"Sorry, {args.input_format} -> {args.output_format} not supported.")
        return

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
    parser.add_argument("input_format",
        choices=INPUT_FORMATS,
        help="Format of the input image(s)"
    )
    parser.add_argument("output_format",
        choices=OUTPUT_FORMATS,
        help="Format of the output image(s). Not all combinations are supported."
    )
    parser.add_argument("input_images",
        type=image,
        nargs="+",
        help="Input Images"
    )
    parser.add_argument("-s", '--output-shape',
        type=int,
        nargs=2,
        help="Texture size for the output images if not the default")
    parser.add_argument("-p", "--prefix",
        default="skybox",
        help="Prefix for the filename. For example, if this is 'skybox', output files will look like 'output/skybox+x.png'")
    args = parser.parse_args()

    main(args)