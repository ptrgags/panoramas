import argparse
import cv2
import numpy

"""
Convert a 2:1 equirectangular panorama to 6 cubemap images.

This is optimized for use with CesiumJS, which uses a Z-up, right-handed
coordinate system. Consequently, the cubemap output will look a little different
than if this was designed for general purpose OpenGL or WebGL cubemaps which
use a Y-up, left-handed coordinate system.

This script was written as a quick utility for myself, I tried to keep it
simple.
"""

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
    [0, 0, -1],
    [1, 0, 0],
    [1, 0, 0],
    [0, 0, 1],
    [-1, 0, 0],
    [-1, 0, 0]
])

# face_index x component
V_DIRECTIONS = numpy.array([
    [0, -1, 0],
    [0, 0, -1],
    [0, -1, 0],
    [0, -1, 0],
    [0, 0, 1],
    [0, -1, 0]
])

def rescale(in_min, in_max, out_min, out_max, value):
    """
    rescale value linearly from the range [old_min, old_max]
    to the range [new_min, new_max]

    :param float in_min: The low end of the current range
    :param float in_max: The high end of the current range
    :param float out_min: The low end of the desired range
    :param float out_max: The high end of the desired range
    :param numpy.ndarray value: The values to scale
    :return: The rescaled values
    :rtype: numpy.ndarray
    """
    delta_out = out_max - out_min
    delta_in = in_max - in_min
    return delta_out / delta_in * (value - in_min) + out_min

class ImagePlane:
    def __init__(self, image, center, u_dir, v_dir):
        self.image = image
        self.shape = image.shape
        self.center = center
        self.u_dir = u_dir
        self.v_dir = v_dir
    
    def get_indices(self):
        return numpy.indices(self.shape, dtype=numpy.float32)
    
    def to_world(self, indices):
        """
        Convert pixels of the image to world coordinates
        """
        # get pixel cordinates
        i, j = indices

        # Rescale to UV coordinates. u is to the right, v is up.
        (H, W) = self.shape
        u = rescale(0, W - 1, -1, 1, j)
        v = rescale(0, H - 1, 1, -1, i)

        # Because I always forget how NumPy broadcasting works:
        # Matrix: Shape
        # u: N x N
        # u_dir: 3
        # u[:, :, None]: N x N x 1
        # u_dir[None, None, :]: 1 x 1 x 3
        # product: N x N x 3
        position = (
            self.center[None, None, :] +
            u[:, :, None] * self.u_dir[None, None, :] +
            v[:, :, None] * self.v_dir[None, None, :]
        )

        x = position[:, :, 0]
        y = position[:, :, 1]
        z = position[:, :, 2]
        return (x, y, z)

    def to_indices(self, world_coords):
        """
        Convert world space coordinates to pixel coordinates
        """
        # TODO: would it be better to pass in the world coordinates as an
        # array?
        (x, y, z) = world_coords
        (cx, cy, cz) = self.center

        px = x - cx
        py = y - cy
        pz = z - cz

        # project u and v
        # TODO: Can this be done with some built-in Numpy operation?
        (ux, uy, uz) = self.u_dir
        (vx, vy, vz) = self.v_dir
        u = px * ux + py * uy + pz * uz
        v = px * vx + py * vy + pz * vz

        # rescale to pixel coordinates. u is up, v is down
        (H, W) = self.shape
        i = rescale(-1, 1, H - 1, 0, v)
        j = rescale(-1, 1, 0, W -1, u)

        return (i, j)

class UnitSphere:
    def __init__(self, image):
        self.image = image
        self.shape = image.shape

    def get_indices(self):
        return numpy.indices(self.shape, dtype=numpy.float32)

    def to_world(self, indices):
        i, j = indices
        
        (H, W) = self.shape
        longitude = rescale(0, W - 1, -numpy.pi, numpy.pi, j)
        latitude = rescale(0, H - 1, numpy.pi / 2, -numpy.pi / 2, i)

        s = numpy.cos(latitude)
        x = s * numpy.cos(longitude)
        y = s * numpy.sin(longitude)
        z = numpy.sin(latitude)
        return (x, y, z)
    
    def to_indices(self, world_coords):
        (x, y, z) = world_coords
        longitude = numpy.arctan2(y, x)
        s = numpy.sqrt(x ** 2 + y ** 2)
        latitude = numpy.arctan2(z, s)

        (H, W, _) = self.shape
        i = rescale(-numpy.pi / 2, numpy.pi / 2, H - 1, 0, latitude)
        j = rescale(-numpy.pi, numpy.pi, 0, W - 1, longitude)

        return (i, j)

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
    u = rescale(0, size - 1, -1, 1, j)
    v = rescale(0, size - 1, -1, 1, i)
    #u = 2 * j / (size - 1) - 1
    #v = 2 * i / (size - 1) - 1

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

    '''
    # scale longitude [-pi, pi] -> [0, 1]
    # and latitude [-pi/2, pi/2] -> [0, 1]
    (W, H, _) = equirectangular.shape
    equi_x = rescale(-numpy.pi, numpy.pi, 0, (W - 1), longitude)
    equi_y = rescale(-numpy.pi / 2, numpy.pi / 2, (H - 1), 0, latitude)

    #equi_x = 0.5 * longitude / numpy.pi + 0.5
    #equi_y = latitude / numpy.pi + 0.5
    
    # flip y to get image space coordinates
    equi_y = 1.0 - equi_y

    # scale to match the dimensions of the image
    (H, W, _) = equirectangular.shape
    equi_x *= (W - 1)
    equi_y *= (H - 1)
    '''

    # scale from lon/lat to pixels of the equirectangular image
    (H, W, _) = equirectangular.shape
    equi_x = rescale(-numpy.pi, numpy.pi, 0, (W - 1), longitude)
    equi_y = rescale(-numpy.pi / 2, numpy.pi / 2, (H - 1), 0, latitude)

    # Let OpenCV handle the inverse projection for us :)
    face = cv2.remap(
        equirectangular,
        equi_x.astype(numpy.float32),
        equi_y.astype(numpy.float32), 
        cv2.INTER_LINEAR)
    return face

def project(source, destination, dst_to_src_projection):
    dst_indices = destination.get_indices()
    dst_world = destination.to_world(dst_indices)
    src_world = dst_to_src_projection(dst_world)
    y, x = source.to_indices(src_world)

    # TODO: can I remap in place?
    destination.image = cv2.remap(
        source.image,
        x.astype(numpy.float32),
        y.astype(numpy.float32),
        cv2.INTER_LINEAR
    )

def plane_to_sphere(world_coords):
    x, y, z = world_coords
    length = numpy.sqrt(x ** 2 + y ** 2 + z ** 2)
    return (x / length, y / length, z / length)

def main(args):
    """
    Compute 6 cubemap images from an equirectangular image, and write them
    into the output/ directory.
    """
    sphere = UnitSphere(args.image_equirectangular)
    plus_x = ImagePlane(
        numpy.zeros((args.size, args.size)),
        numpy.array([1, 0, 0]),
        # expected u=-y, v=z, actual u=-z, v=y
        numpy.array([0, 0, -1]),
        numpy.array([0, 1, 0])
    )
    project(sphere, plus_x, plane_to_sphere)
    cv2.imwrite("output/skybox+x.png", plus_x.image)

    plus_y = ImagePlane(
        numpy.zeros((args.size, args.size)),
        # WHY IS THIS NEGATIVE Y???
        numpy.array([0, -1, 0]),
        numpy.array([1, 0, 0]),
        numpy.array([0, 0, 1])
    )
    project(sphere, plus_y, plane_to_sphere)
    cv2.imwrite("output/skybox+y.png", plus_y.image)

    plus_z = ImagePlane(
        numpy.zeros((args.size, args.size)),
        numpy.array([0, 0, 1]),
        numpy.array([1, 0, 0]),
        numpy.array([0, 1, 0])
    )
    project(sphere, plus_z, plane_to_sphere)
    cv2.imwrite("output/skybox+z.png", plus_z.image)

    neg_x = ImagePlane(
        numpy.zeros((args.size, args.size)),
        numpy.array([-1, 0, 0]),
        numpy.array([0, 0, 1]),
        numpy.array([0, 1, 0])
    )
    project(sphere, neg_x, plane_to_sphere)
    cv2.imwrite("output/skybox-x.png", neg_x.image)

    neg_y = ImagePlane(
        numpy.zeros((args.size, args.size)),
        # WHY IS THIS NEGATIVE Y???
        numpy.array([0, 1, 0]),
        numpy.array([1, 0, 0]),
        numpy.array([0, 0, -1])
    )
    project(sphere, neg_y, plane_to_sphere)
    cv2.imwrite("output/skybox-y.png", neg_y.image)

    neg_z = ImagePlane(
        numpy.zeros((args.size, args.size)),
        numpy.array([0, 0, -1]),
        numpy.array([-1, 0, 0]),
        numpy.array([0, 1, 0])
    )
    project(sphere, neg_z, plane_to_sphere)
    cv2.imwrite("output/skybox-z.png", neg_z.image)

    '''
    prefix = args.prefix
    for i in range(6):
        face_img = make_face(equirectangular, i, args.size)
        face_name = FACE_NAMES[i]
        filename = f"output/{prefix}{face_name}.png"
        print(f"Computing face {filename}")
        cv2.imwrite(filename, face_img)
    '''

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