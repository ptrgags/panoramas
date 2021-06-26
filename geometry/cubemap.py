import numpy

from geometry.imageplane import ImagePlane

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

FACES = ['+x', '-x', '+y', '-y', '+z', '-z']

CENTERS = {
    '+x': numpy.array([1, 0, 0]),
    '-x': numpy.array([-1, 0, 0]),
    '+y': numpy.array([0, 1, 0]),
    '-y': numpy.array([0, -1, 0]),
    '+z': numpy.array([0, 0, 1]),
    '-z': numpy.array([0, 0, -1])
}

# These directions seem weird, but this is how OpenGL expects
# the axes to be oriented with a left-hand coordinate system
# see https://www.khronos.org/opengl/wiki/Cubemap_Texture#Upload_and_orientation
U_DIRECTIONS = {
    '+x': numpy.array([0, 0, -1]),
    '-x': numpy.array([0, 0, 1]),
    '+y': numpy.array([1, 0, 0]),
    '-y': numpy.array([1, 0, 0]),
    '+z': numpy.array([1, 0, 0]),
    '-z': numpy.array([-1, 0, 0])
}

V_DIRECTIONS = {
    '+x': numpy.array([0, -1, 0]),
    '-x': numpy.array([0, -1, 0]),
    '+y': numpy.array([0, 0, 1]),
    '-y': numpy.array([0, 0, -1]),
    '+z': numpy.array([0, -1, 0]),
    '-z': numpy.array([0, -1, 0])
}

class Cubemap:
    def __init__(self, faces=None, shape=None):
        if faces is not None:
            self.faces = faces
        else:
            self.faces = Cubemap.create_faces(shape)
    
    def project_from(self, sphere):
        for face_name, face in self.faces.items():
            print(f"projecting to face {face_name}")
            plane_world = face.get_world_coords()
            sphere_world = unproject_gnomonic(plane_world)
            face.image = sphere.lookup_colors(sphere_world)
    
    def unproject_to(self, sphere):
        # TODO: determine how to divide the coordinates into the 6 faces
        raise NotImplementedError
    
    def write(self, fname_pattern):
        for face_name, face in self.faces.items():
            full_filename = fname_pattern.format(face_name)
            face.write(full_filename)
    
    @classmethod
    def create_faces(cls, shape):
        faces = {}
        for face_name in FACES:
            faces[face_name] = ImagePlane(
                CENTERS[face_name],
                U_DIRECTIONS[face_name],
                V_DIRECTIONS[face_name],
                shape=shape
            )
        return faces