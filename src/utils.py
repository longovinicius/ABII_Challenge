import math


def cartesian_to_polar(x, y):
    r = math.sqrt(x**2 + y**2)
    theta = math.atan2(x, y)
    return int(r * 100), int(math.degrees(theta))
