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

def array_stats(array):
    """
    For debugging, print a NumPy array's stats

    :param numpy.ndarray array: the array to print
    """
    min_val = array.min()
    max_val = array.max()
    avg_val = array.mean()
    print(f"min: {min_val}")
    print(f"max: {max_val}")
    print(f"avg: {avg_val}")