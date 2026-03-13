"""
Linear Congruential Generator (LCG)
Deterministic pseudorandom generator based on a linear recurrence
https://en.wikipedia.org/wiki/Linear_congruential_generator
"""

def lcg(seed, a, c, m, n):
    """
    Generates n numbers using LCG
    Formula: X_{i+1} = (a * X_i + c) mod m
    Returns:
        List of n integers in [0, m-1]
    """
    x = seed
    results = []
    for _ in range(n):
        x = (a * x + c) % m  # Recurrence relation
        results.append(x)
    return results

# Standard well-known parameters
# Source: glibc (C standard library)
PARAMS_GLIBC = {
    'a': 1103515245,
    'c': 12345,
    'm': 2**31
}

# RANDU: example of a bad LCG
PARAMS_RANDU = {
    'a': 65539,
    'c': 0,
    'm': 2**31
}

# Knuth MMIX: good parameters
PARAMS_KNUTH = {
    'a': 6364136223846793005,
    'c': 1442695040888963407,
    'm': 2**64
}
