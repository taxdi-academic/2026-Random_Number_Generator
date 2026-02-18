# generators/bbs.py

"""
Blum-Blum-Shub (BBS)
Générateur fondé sur des hypothèses de théorie des nombres,
réputé pour sa sécurité théorique.
https://fr.wikipedia.org/wiki/Blum_Blum_Shub
"""

import random

def bbs(seed, p, q, n):
    """
    Formule: x_{n+1} = (x_n)^2 mod M, où M = p * q
    Sortie: bit de poids faible
    Paramètres:
        seed: graine (premier avec M, != 0, != 1)
        p, q: premiers de Blum (p = 3 mod 4, q = 3 mod 4)
        n: nombre de bits
    """
    M = p * q
    x = (seed * seed) % M
    results = []
    for _ in range(n):
        x = (x * x) % M
        results.append(x & 1)
    return results

# Petits premiers de Blum pour tests
SMALL_PRIMES = {
    'p': 499,  # 499 % 4 = 3
    'q': 547   # 547 % 4 = 3
}
