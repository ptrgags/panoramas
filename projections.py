import numpy

def project_gnomonic(sphere_world_coords, plane_direction):
    # This is going to take more thought
    raise NotImplementedError

    '''
    (x, y, z) = sphere_world_coords

    # project the vector onto the plane direction vector
    # r proj center = (r dot dir)dir
    (cx, cy, cz) = plane_direction
    projected_length = x * cx + y * cy + z * cz
    projected = projected_length * plane_direction

    # compute the rejection, r - (r proj center)
    rejected = sphere_world

    # |plane| / |rejection| = |center| / |projection|
    #               |plane| = |center||rejection| / |projection|
    #               |plane| = |rejection| / |projection|
    '''

def unproject_gnomonic(plane_world_coords):
    """
    Inverse of project_gnomonic, i.e. it takes a point on the image
    plane and projects it back to the unit sphere. The camera is at
    the center of the sphere

    :param tuple plane_world_coords: (x, y, z) coordinates on the
        image plane
    :return: the (x, y, z) coordinates on the unit sphere after projecting
        from the center of the sphere
    :rtype: tuple
    """
    (x, y, z) = plane_world_coords
    length = numpy.sqrt(x ** 2 + y ** 2 + z ** 2)
    return (x / length, y / length, z / length)