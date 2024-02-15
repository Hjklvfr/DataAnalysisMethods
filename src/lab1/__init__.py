import math
from itertools import groupby

from numpy.typing import ArrayLike


def sample_mean(x: ArrayLike) -> float:
    n = len(x)
    return sum(x) / n


def sample_mode(x: ArrayLike) -> float:
    frequency_map = map(lambda y: (y[0], len(list(y[1]))), groupby(sorted(x)))
    return max(frequency_map, key=lambda y: y[1])[0]


def sample_median(x: ArrayLike) -> float:
    half = int(len(x) / 2)
    half_next = int(len(x) / 2 + 1)
    sorted_x = list(sorted(x))
    if len(x) % 2 == 0:
        return (sorted_x[half] + sorted_x[half_next]) / 2
    else:
        return sorted_x[half]


def sample_std(x: ArrayLike) -> float:
    mu = sample_mean(x)
    n = len(x)
    return math.sqrt(sum(map(lambda y: (y - mu)**2, x)) / n)


def sample_asymmetry_coefficient(x: ArrayLike) -> float:
    return (sample_mean(x) - sample_mode(x)) / sample_std(x)


def forth_centrality(x: ArrayLike) -> float:
    mean = sample_mean(x)
    return sum(map(lambda y: (y - mean)**4, x))


def sample_excess_coefficient(x: ArrayLike) -> float:
    return forth_centrality(x) / sample_asymmetry_coefficient(x) - 3
