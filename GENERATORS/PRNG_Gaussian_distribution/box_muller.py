# generators/box_muller.py

"""
Box-Muller Transform
Converts uniform variables into Gaussian (normal) variables
https://en.wikipedia.org/wiki/Box%E2%80%93Muller_transform
"""

import math

def box_muller(u1, u2):
    """
    Standard Box-Muller transform
    Formulas:
        Z0 = sqrt(-2*ln(U1)) * cos(2π*U2)
        Z1 = sqrt(-2*ln(U1)) * sin(2π*U2)
    Parameters:
        u1, u2: two independent uniform values in (0, 1)
    Returns:
        (z0, z1): two independent N(0,1) Gaussian values
    """
    # Avoid ln(0) which would give -infinity (undefined)
    if u1 <= 0:
        u1 = 1e-10
    if u2 <= 0:
        u2 = 1e-10

    # Polar transformation
    r = math.sqrt(-2.0 * math.log(u1))
    theta = 2.0 * math.pi * u2

    # Cartesian coordinates
    z0 = r * math.cos(theta)
    z1 = r * math.sin(theta)

    return z0, z1

def box_muller_series(uniform_rng, seed, n):
    """
    Generates n Gaussian values from a uniform generator
    Parameters:
        uniform_rng: uniform generator function: (seed, n) --> list of floats in [0, 1]
        seed: seed for the uniform generator
        n: number of Gaussian values desired
    Returns:
        List of n Gaussian values
    """
    # Compute number of uniform values needed
    n_uniform = ((n + 1) // 2) * 2
    uniforms = uniform_rng(seed, n_uniform)

    results = []
    # Process in pairs (step of 2)
    for i in range(0, len(uniforms) - 1, 2):
        z0, z1 = box_muller(uniforms[i], uniforms[i + 1])
        results.extend([z0, z1])

    # Return n values
    return results[:n]
