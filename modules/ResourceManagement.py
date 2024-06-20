"""
ResourceManagement Module

This module provides utility functions for managing resources in a simulated environment.
It includes functions for calculating the resource fit and custom distance for devices.

Functions:
    fit_resource(new_value, limit_value): Calculates the fit resource value.
    custom_distance(A, B): Calculates a custom distance metric between two sets of coordinates.

Usage Example:
    fit = fit_resource(new_value, limit_value)
    distance = custom_distance(A, B)
"""

def fit_resource(new_value, limit_value):
    """
    Calculates the fit resource value.

    :param new_value: The new value to fit.
    :type new_value: float
    :param limit_value: The limiting value.
    :type limit_value: float
    :return: The fit resource value.
    :rtype: float
    """
    try:
        return min(limit_value / new_value, 1)
    except ZeroDivisionError:
        return 1

def custom_distance(A, B):
    """
    Defines a custom distance for device wireless coverage to account for less coverage due to floor interception.

    If A and B are not of the same size, distance is calculated among the first values up to min(len(A), len(B)).

    :param A: List of coordinates for point A.
    :type A: list
    :param B: List of coordinates for point B.
    :type B: list
    :return: Distance (as coverage) between A and B.
    :rtype: float
    """
    return sum([(b - a) ** 2 for a, b in zip(A, B)]) ** 0.5
