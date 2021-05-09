import argparse
import cv2
import numpy

FACE_NAMES = [
    '+x',
    '+y',
    '+z',
    '-x',
    '-y',
    '-z',
]

# face_index x component
CENTERS = numpy.array([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
    [-1, 0, 0],
    [0, -1, 0],
    [0, 0, -1],
])

# face_index x component
U_DIRECTIONS = numpy.array([
    [0, 1, 0],
    [-1, 0, 0],
    [0, 1, 0],
    [0, -1, 0],
    [1, 0, 0],
    [0, 1, 0]
])

# face_index x component
V_DIRECTIONS = numpy.array([
    [0, 0, 1],
    [0, 0, 1],
    [-1, 0, 0],
    [0, 0, 1],
    [0, 0, 1],
    [1, 0, 0]
])

def make_face(equirectangular, face_index, size): # :P
    j, i = numpy.indices((size, size), dtype=numpy.float32)
    # u and v are in the range [-1, 1]
    u = 2 * i / (size - 1) - 1
    v = 2 * j / (size - 1) - 1

    # compute the 3D position on the unit cube
    center = CENTERS[face_index]
    u_dir = U_DIRECTIONS[face_index]
    v_dir = V_DIRECTIONS[face_index]

    # Because I always forget how broadcasting works:
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
    # the direction (lon, lat)
    longitude = numpy.arctan2(y, x)
    s = numpy.sqrt(x ** 2 + y ** 2)
    latitude = numpy.arctan2(z, s)

    lon_range = [numpy.min(longitude), numpy.max(longitude)]
    lat_range = [numpy.min(latitude), numpy.max(latitude)]
    print(f"{FACE_NAMES[face_index]} - longitude: {lon_range}, lat: {lat_range}")

    # scale longitude [-pi, pi] -> [0, 1]
    # and latitude [-pi/2, pi/2] -> [0, 1]
    (W, H, _) = equirectangular.shape
    equi_x = 0.5 * longitude / numpy.pi + 0.5
    equi_y = latitude / numpy.pi + 0.5

    # scale to match the dimensions of the image
    (H, W, _) = equirectangular.shape
    equi_x *= (W - 1)
    equi_y *= (H - 1)

    x_range = [numpy.min(equi_x), numpy.max(equi_x)]
    y_range = [numpy.min(equi_y), numpy.max(equi_y)]
    print(f"{FACE_NAMES[face_index]} - equi_x: {x_range}, equi_y: {y_range}")

    face = cv2.remap(equirectangular, equi_x.astype(numpy.float32), equi_y.astype(numpy.float32), cv2.INTER_LINEAR)
    return face

def main(args):
    equirectangular = args.image_equirectangular

    for i in range(6):
        face_img = make_face(equirectangular, i, args.size)
        face_name = FACE_NAMES[i]
        cv2.imwrite(f"skybox{face_name}.png", face_img)

def image(fname):
    return cv2.imread(fname)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("image_equirectangular", type=image, help="Image to turn into a cubemap. It must be a 2:1 equirectangular image")
    parser.add_argument("-s", '--size', type=int, default=2048, help="Texture size for each face of the cubemap Defaults to 2048")
    args = parser.parse_args()
    main(args)