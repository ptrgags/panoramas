import argparse
import cv2
import numpy

# Names of of the 6 faces for labeling the filenames.
FACE_NAMES = [
    '+x',
    '+y',
    '+z',
    '-x',
    '-y',
    '-z',
]

# By definition
# face_index x component
CENTERS = numpy.array([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
    [-1, 0, 0],
    [0, -1, 0],
    [0, 0, -1],
])

# OpenGL/WebGL cubemaps are weird, they use a _left-handed_ coordinate
# system!!! Also it wasn't immediately obvious to me that the UV direction
# is based on the _inside_ of the cube. This page helped explain this:
# https://www.khronos.org/opengl/wiki/Cubemap_Texture#Upload_and_orientation

# face_index x component
U_DIRECTIONS = numpy.array([
    [0, 0, 1],
    [1, 0, 0],
    [-1, 0, 0],
    [0, 0, -1],
    [1, 0, 0],
    [1, 0, 0]
])

# face_index x component
V_DIRECTIONS = numpy.array([
    [0, 1, 0],
    [0, 0, 1],
    [0, 1, 0],
    [0, 1, 0],
    [0, 0, -1],
    [0, 1, 0]
])

def make_face(equirectangular, face_index, size): 
    """
    :P

    Jokes aside, this function reprojects the equirectangular panorama to
    one of the 6 views of a cubemap.

    :param numpy.ndarray equirectangular: The equirectangular panag
    :param int face_index: Integer from 0-5 to select one of the 6 faces of
        the cubemap. See `FACE_NAMES` 
    :param int size: The size of the output texture. This should be a power of
        two.
    :return: One face as part of the cubemap.
    :rtype: numpy.ndarray
    """
    # make grid indices for the output image.
    i, j = numpy.indices((size, size), dtype=numpy.float32)

    # u and v are in the range [-1, 1]
    u = 2 * j / (size - 1) - 1
    v = 2 * i / (size - 1) - 1

    # compute the 3D position on the unit cube
    center = CENTERS[face_index]
    u_dir = U_DIRECTIONS[face_index]
    v_dir = V_DIRECTIONS[face_index]

    # Because I always forget how NumPy broadcasting works:
    # Matrix: Shape
    # u: N x N
    # u_dir: 3
    # u[:, :, None]: N x N x 1
    # u_dir[None, None, :]: 1 x 1 x 3
    # product: N x N x 3
    position = (
        center[None, None, :] +
        u[:, :, None] * u_dir[None, None, :] +
        v[:, :, None] * v_dir[None, None, :])
    x = position[:, :, 0]
    y = position[:, :, 1]
    z = position[:, :, 2]

    # convert to spherical coordinates. We don't need the radius, only
    # the direction (lon, lat). Remember that we're in a left-handed coordinate
    # system!
    longitude = numpy.arctan2(x, y)
    s = numpy.sqrt(x ** 2 + y ** 2)
    latitude = numpy.arctan2(z, s)

    # scale longitude [-pi, pi] -> [0, 1]
    # and latitude [-pi/2, pi/2] -> [0, 1]
    (W, H, _) = equirectangular.shape
    equi_x = 0.5 * longitude / numpy.pi + 0.5
    equi_y = latitude / numpy.pi + 0.5

    # scale to match the dimensions of the image
    (H, W, _) = equirectangular.shape
    equi_x *= (W - 1)
    equi_y *= (H - 1)

    # Let OpenCV handle the inverse projection for us :)
    face = cv2.remap(
        equirectangular,
        equi_x.astype(numpy.float32),
        equi_y.astype(numpy.float32), 
        cv2.INTER_LINEAR)
    return face

def main(args):
    """
    Compute 6 cubemap images from an equirectangular image, and write them
    into the output/ directory.
    """
    equirectangular = args.image_equirectangular
    prefix = args.prefix

    for i in range(6):
        face_img = make_face(equirectangular, i, args.size)
        face_name = FACE_NAMES[i]
        filename = f"output/{prefix}{face_name}.png"
        print(f"Computing face {filename}")
        cv2.imwrite(filename, face_img)

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