import numpy
import cv2

from util import rescale

class UnitSphere:
    """
    A unit sphere, textured with a spherical panorama. The sphere is viewed
    from the inside.
    """
    def __init__(self, image=None, shape=None):
        """
        Constructor

        :param numpy.ndarray image: An equirectangular image representing a
            spherical panorama. This should be an image with a 2:1 aspect
            ratio.
        """
        if image is not None:
            self.image = image
            self.shape = image.shape
        else:
            self.image = None
            self.shape = shape

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
        # the equirectangular image is on the inside of the sphere, so
        # flip y so it goes clockwise
        longitude = numpy.arctan2(x, y)
        s = numpy.sqrt(x ** 2 + y ** 2)
        latitude = numpy.arctan2(z, s)

        (H, W, _) = self.shape
        i = rescale(-numpy.pi / 2, numpy.pi / 2, H - 1, 0, latitude)
        j = rescale(-numpy.pi, numpy.pi, 0, W - 1, longitude)

        return (i, j)
    
    def lookup_colors(self, world_coords):
        if self.image is None:
            raise RuntimeError(
                "lookup_colors only works for spheres with an image")

        i, j = self.to_indices(world_coords)
        return cv2.remap(
            self.image,
            j.astype(numpy.float32),
            i.astype(numpy.float32),
            cv2.INTER_LINEAR
        )