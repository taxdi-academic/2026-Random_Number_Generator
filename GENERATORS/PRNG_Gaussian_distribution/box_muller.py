# generators/box_muller.py

"""
Transformée de Box-Muller
Convertit variables uniformes en variables gaussiennes (normales)
https://fr.wikipedia.org/wiki/M%C3%A9thode_de_Box-Muller
"""

import math

def box_muller(u1, u2):
    """
    Transformée de Box-Muller standard
    Formules:
        Z0 = sqrt(-2*ln(U1)) * cos(2π*U2)
        Z1 = sqrt(-2*ln(U1)) * sin(2π*U2)
    Paramètres:
        u1, u2: deux valeurs uniformes dans (0, 1), indépendantes
    Retourne:
        (z0, z1): deux valeurs gaussiennes N(0,1) indépendantes
    """
    # Éviter ln(0) qui donnerait -infini (non défini)
    if u1 <= 0:
        u1 = 1e-10
    if u2 <= 0:
        u2 = 1e-10
    
    # Transformation polaire
    r = math.sqrt(-2.0 * math.log(u1))
    theta = 2.0 * math.pi * u2
    
    # Coordonnées cartésiennes
    z0 = r * math.cos(theta)
    z1 = r * math.sin(theta)
    
    return z0, z1

def box_muller_series(uniform_rng, seed, n):
    """
    Génère n valeurs gaussiennes à partir d'un générateur uniforme
    Paramètres:
        uniform_rng: fonction générateur uniforme : (seed, n) --> list de flottant dans [0, 1]
        seed: graine pour le générateur uniforme
        n: nombre de valeurs gaussiennes désirées
    Retourne:
        Liste de n valeurs gaussiennes
    """
    # Calculer nombre d'uniformes nécessaires
    n_uniform = ((n + 1) // 2) * 2
    uniforms = uniform_rng(seed, n_uniform)
    
    results = []
    # Traiter par paires (pas de 2)
    for i in range(0, len(uniforms) - 1, 2):
        z0, z1 = box_muller(uniforms[i], uniforms[i + 1])
        results.extend([z0, z1])
    
    # Retourner n valeurs
    return results[:n]
