import numpy
from geometry.imageplane import ImagePlane
from util import array_stats

ORIGIN = numpy.array([0, 0, 0])
PLUS_X = numpy.array([1, 0, 0])
PLUS_Y = numpy.array([0, 1, 0])

class StereographicProjection:
    def __init__(self, hemispheres=None, shape=None):
        if hemispheres is not None:
            north_image, south_image = hemispheres
            self.northern_hemisphere = ImagePlane(
                ORIGIN,
                PLUS_X,
                PLUS_Y,
                north_image
            )
            self.southern_hemisphere = ImagePlane(
                ORIGIN,
                PLUS_X,
                PLUS_Y,
                south_image
            )
        else:
            self.northern_hemisphere = ImagePlane(
                ORIGIN,
                PLUS_X,
                PLUS_Y,
                shape=shape
            )

            # Same image plane setup, it's the projection point that
            # changes.
            self.southern_hemisphere = ImagePlane(
                ORIGIN,
                PLUS_X,
                PLUS_Y,
                shape=shape
            )

    def project_from(self, sphere):
        # TODO: Plan how to render the two projections
        raise NotImplementedError

    def unproject_to(self, sphere):
        (x, y, z) = sphere.get_world_coords()

        # Each point is projected to the same point as the
        # point at (x, y, -z), so abs(z) will handle both at once!
        denominator = 1 + abs(z)
        
        # (x, y, z) projects to (a, b, 0)
        a = x / denominator
        b = y / denominator
        zero = numpy.zeros_like(x)
        projected = (a, b, zero)

        is_northern = z >= 0
        is_southern = ~is_northern

        northern_colors = self.northern_hemisphere.lookup_colors(projected)
        southern_colors = self.southern_hemisphere.lookup_colors(projected)

        image = northern_colors
        image[is_southern] = southern_colors[is_southern]
        sphere.image = image