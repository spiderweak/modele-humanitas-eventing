
def fit_resource(new_value, limit_value):
    try:
        return min(limit_value / new_value, 1)
    except ZeroDivisionError:
        return 1


def custom_distance(x1, y1, z1, x2, y2, z2):
    """
    Defines a custom distance for device wireless coverage to account for less coverage due to floor interception.

    Args:
        x1 : x value, device 1
        z1 : z value, device 1
        y1 : y value, device 1
        x2 : x value, device 2
        y2 : y value, device 2
        z2 : z value, device 2

    Returns:
        distance : int, distance (as coverage) between device 1 and device 2.
    """
    distance = ((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)**0.5
    return distance