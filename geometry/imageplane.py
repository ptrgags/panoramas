import cv2
import numpy

from util import rescale

class ImagePlane:
    DEFAULT_SHAPE = (2048, 2048, 3)

    def __init__(self, center, u_dir, v_dir, image=None, shape=None):
        self.center = center
        self.u_dir = u_dir
        self.v_dir = v_dir

        if image is not None:
            self.image = image
            self.shape = image.shape
        else:
            self.shape = shape or self.DEFAULT_SHAPE
    
    def get_world_coords(self):
        """
        Convert pixels of the image to world coordinates
        """
        # get pixel cordinates
        (H, W, _) = self.shape
        i, j = numpy.indices((H, W), dtype=numpy.float32)

        # Rescale to UV coordinates. u is to the right, v is up.
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

    def lookup_colors(self, world_coords):
        if self.image is None:
            raise RuntimeError(
                "lookup_colors only works for image planes with an image")

        i, j = self.to_indices(world_coords)
        return cv2.remap(
            self.image,
            j.astype(numpy.float32),
            i.astype(numpy.float32),
            cv2.INTER_LINEAR
        )
    
    def write(self, fname):
        print(f"Writing {fname}")
        cv2.imwrite(fname, self.image)