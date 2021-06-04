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
        """
        Get indices for the pixels in the underlying image

        :return: an array containing the i, j indices.
        :rtype: numpy.ndarray
        """
        (H, W, _) = self.shape
        return numpy.indices((H, W), dtype=numpy.float32)
    
    def to_world(self, indices):
        """
        Convert pixels of the image to world coordinates
        """
        # get pixel cordinates
        i, j = indices

        # Rescale to UV coordinates. u is to the right, v is up.
        (H, W, _) = self.shape
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
        (H, W, _) = self.shape
        i = rescale(-1, 1, H - 1, 0, v)
        j = rescale(-1, 1, 0, W -1, u)

        return (i, j)

class UnitSphere:
    """
    A unit sphere, textured with a spherical panorama. The sphere is viewed
    from the inside.
    """
    def __init__(self, image):
        """
        Constructor

        :param numpy.ndarray image: An equirectangular image representing a
            spherical panorama. This should be an image with a 2:1 aspect
            ratio.
        """
        self.image = image
        self.shape = image.shape

    def get_indices(self):
        """
        Get indices for the pixels in the underlying image

        :return: an array containing the i, j indices.
        :rtype: numpy.ndarray
        """
        (H, W, _) = self.shape
        return numpy.indices((H, W), dtype=numpy.float32)

    def to_world(self, indices):
        """
        Convert from pixels of the image to world coordinates. Remember that
        the equirectangular image is the inside of the sphere.
        
        :param numpy.ndarray indices: the indices array from get_indices()
        :return: The world coordinates arrays as a triple (x, y, z)
        :rtype: tuple
        """
        i, j = indices
        
        # Convert indices to longitude/latitude. The longitude increases to
        # the right, and the latitude increases upwards
        (H, W, _) = self.shape
        longitude = rescale(0, W - 1, -numpy.pi, numpy.pi, j)
        latitude = rescale(0, H - 1, numpy.pi / 2, -numpy.pi / 2, i)

        # horizontal radius
        s = numpy.cos(latitude)

        # The equirectangular image is on the inside of the sphere,
        # so flip y so it goes clockwise
        x = s * numpy.cos(longitude)
        y = -s * numpy.sin(longitude)
        z = numpy.sin(latitude)
        return (x, y, z)
    
    def to_indices(self, world_coords):
        """
        Convert from world coordinates on the sphere to coordinates of the
        equirectangular image

        :param tuple indices: tuple of indices from
        """
        (x, y, z) = world_coords
        longitude = numpy.arctan2(y, x)
        s = numpy.sqrt(x ** 2 + y ** 2)
        latitude = numpy.arctan2(z, s)

        (H, W, _) = self.shape
        i = rescale(-numpy.pi / 2, numpy.pi / 2, H - 1, 0, latitude)
        j = rescale(-numpy.pi, numpy.pi, 0, W - 1, longitude)

        return (i, j)

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
    (x, y, z) = world_coords
    length = numpy.sqrt(x ** 2 + y ** 2 + z ** 2)
    return (x / length, y / length, z / length)

def sphere_to_plane(world_coords):
    """
    Project coordinates from the sphere onto the plane. This only handles
    the +x axis at the moment
    """
    (x, y, z) = world_coords

    # project the vector onto the center axis
    # r proj center = (r dot center)center = ((x, y, z) dot (1, 0, 0))center 
    # = (x, 0, 0)
    # compute the rejection, that is r - r proj center
    # = (x, y, z) - (x, 0, 0) = (0, y, z)
    # compute the scale factor
    # |plane| / |rejection| = |center| / |projection|
    # |plane| / |rejection| = 1 / x
    # so scale up the rejection by (1/x) (remember, x < 1) and add an offset
    # of center to get the projected coordinates. No trig functions needed!
    return (numpy.ones_like(x), y / x, z / x)

def main(args):
    """
    Compute 6 cubemap images from an equirectangular image, and write them
    into the output/ directory.
    """
    sphere = UnitSphere(args.image_equirectangular)
    plus_x = ImagePlane(
        numpy.zeros((args.size, args.size, 3)),
        numpy.array([1, 0, 0]),
        # expected u=-y, v=z, actual u=-z, v=y
        numpy.array([0, 0, -1]),
        numpy.array([0, 1, 0])
    )
    project(sphere, plus_x, plane_to_sphere)
    cv2.imwrite("output/skybox+x.png", plus_x.image)

    plus_y = ImagePlane(
        numpy.zeros((args.size, args.size, 3)),
        # WHY IS THIS NEGATIVE Y???
        numpy.array([0, -1, 0]),
        numpy.array([1, 0, 0]),
        numpy.array([0, 0, 1])
    )
    project(sphere, plus_y, plane_to_sphere)
    cv2.imwrite("output/skybox+y.png", plus_y.image)

    plus_z = ImagePlane(
        numpy.zeros((args.size, args.size, 3)),
        numpy.array([0, 0, 1]),
        numpy.array([1, 0, 0]),
        numpy.array([0, 1, 0])
    )
    project(sphere, plus_z, plane_to_sphere)
    cv2.imwrite("output/skybox+z.png", plus_z.image)

    neg_x = ImagePlane(
        numpy.zeros((args.size, args.size, 3)),
        numpy.array([-1, 0, 0]),
        numpy.array([0, 0, 1]),
        numpy.array([0, 1, 0])
    )
    project(sphere, neg_x, plane_to_sphere)
    cv2.imwrite("output/skybox-x.png", neg_x.image)

    neg_y = ImagePlane(
        numpy.zeros((args.size, args.size, 3)),
        # WHY IS THIS NEGATIVE Y???
        numpy.array([0, 1, 0]),
        numpy.array([1, 0, 0]),
        numpy.array([0, 0, -1])
    )
    project(sphere, neg_y, plane_to_sphere)
    cv2.imwrite("output/skybox-y.png", neg_y.image)

    neg_z = ImagePlane(
        numpy.zeros((args.size, args.size, 3)),
        numpy.array([0, 0, -1]),
        numpy.array([-1, 0, 0]),
        numpy.array([0, 1, 0])
    )
    project(sphere, neg_z, plane_to_sphere)
    cv2.imwrite("output/skybox-z.png", neg_z.image)

    out_sphere = UnitSphere(numpy.zeros(args.image_equirectangular.shape))
    project(plus_x, out_sphere, sphere_to_plane)
    cv2.imwrite("output/equirectangular.png", out_sphere.image)

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