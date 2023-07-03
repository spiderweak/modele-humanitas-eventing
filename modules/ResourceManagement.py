
def fit_resource(new_value, limit_value):
    try:
        return min(limit_value / new_value, 1)
    except ZeroDivisionError:
        return 1


def custom_distance(A,B):
    """
    Defines a custom distance for device wireless coverage to account for less coverage due to floor interception.

    If A and B are not of the same size, distance is calculated among the first values up to min(len(A),len(B))

    Args:
    -----
    A : `list`
        List of coords for point A
    B : `list`
        List of coords for point B

    Returns:
    --------
    distance : `int`
        Distance (as coverage) between A and B.
    """
    return sum([((b-a)**2) for a,b in zip(A,B)]) ** 0.5