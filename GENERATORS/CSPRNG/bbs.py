# generators/bbs.py

"""
Blum-Blum-Shub (BBS)
Generator based on number-theoretic hardness assumptions,
renowned for its theoretical security.
https://en.wikipedia.org/wiki/Blum_Blum_Shub
"""

import random

def bbs(seed, p, q, n):
    """
    Formula: x_{n+1} = (x_n)^2 mod M, where M = p * q
    Output: least significant bit
    Parameters:
        seed: initial value (coprime with M, != 0, != 1)
        p, q: Blum primes (p = 3 mod 4, q = 3 mod 4)
        n: number of bits to generate
    """
    M = p * q
    x = (seed * seed) % M
    results = []
    for _ in range(n):
        x = (x * x) % M
        results.append(x & 1)
    return results

# Small Blum primes for testing
SMALL_PRIMES = {
    'p': 499,  # 499 % 4 = 3
    'q': 547   # 547 % 4 = 3
}
