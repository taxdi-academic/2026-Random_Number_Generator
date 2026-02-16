"""
Linear Congruential Generator (LCG)
Generateur pseudo-aleatoire deterministe base sur une recurrence lineaire
https://fr.wikipedia.org/wiki/G%C3%A9n%C3%A9rateur_congruentiel_lin%C3%A9aire
"""

def lcg(seed, a, c, m, n):
    """
    Genere n nombres avec LCG
    Formule: X_{i+1} = (a * X_i + c) mod m
    Retourne:
        Liste de n entiers dans [0, m-1]
    """
    x = seed
    results = []
    for _ in range(n):
        x = (a * x + c) % m  # Relation de recurrence (formule de la suite)
        results.append(x)
    return results

# Parametres standards connus
# Source: glibc (bibliotheque standard C)
PARAMS_GLIBC = {
    'a': 1103515245,
    'c': 12345,
    'm': 2**31
}

# RANDU: exemple de mauvais LCG
PARAMS_RANDU = {
    'a': 65539,
    'c': 0,
    'm': 2**31
}

# MMIX de Knuth : bien
PARAMS_KNUTH = {
    'a': 6364136223846793005,
    'c': 1442695040888963407,
    'm': 2**64
}
