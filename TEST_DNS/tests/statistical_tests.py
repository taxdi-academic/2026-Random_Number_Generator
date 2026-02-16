# tests/statistical_tests.py

"""
Tests statistiques pour évaluer la qualité des générateurs aléatoires
"""

import math
from collections import Counter


# 1) Entropie de Shannon
# https://fr.wikipedia.org/wiki/Entropie_de_Shannon

def shannon_entropy(data):
    """
    Calcule l'entropie de Shannon par octet
    
    Interprétation avec H l'entropie :
        - si H = 8 bits : parfaite entropie (totalement aléatoire)
        - si H < 8 bits : moins bon (présence de patterns, ou prédictibilité)
    
    Paramètres:
        data: octet ou bien liste d'entiers [0-255]
    
    Retourne:
        Entropie en bits par octet
    """
    if not data:
        return 0.0
    
    # Compter fréquences de chaque octet
    freq = Counter(data)
    n = len(data)
    
    # Calculer entropie
    entropy = 0.0
    for count in freq.values() :
        p = count / n  # Proba uniforme
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def shannon_entropy_res(data):
    """
    Rapport détaillé d'entropie
    
    Retourne:
        dico avec entropie, max théorique, pourcentage
    """
    entropy = shannon_entropy(data)
    max_entropy = 8.0  # 8 bits
    
    return {
        'entropy': entropy,
        'max_entropy': max_entropy,
        'percentage': (entropy / max_entropy) * 100,
        'status': 'PASS' if entropy > 7.9 else 'FAIL'
    }


# 2) Test du Chi-Carre (X^2)
# https://fr.wikipedia.org/wiki/Test_du_%CF%87%C2%B2

def chi_squared_test(data, p=0.05):
    """
    Test pour uniformité de distribution des octets
    
    Hypothèse H_0: les octets sont uniformément distribués
    
    Paramètres:
        data: octets ou liste d'entiers [0-255]
        p: seuil de signification (0.05 = 5%)
    
    Retourne:
        dico 
    """
    if not data:
        return None
    
    # Compter occurrences
    freq = Counter(data)
    n = len(data)
    
    # Fréquence attendue pour uniformité
    expected = n / 256
    
    # Calculer X^2
    chi2 = 0.0
    for i in range(256):
        observed = freq.get(i, 0)
        chi2 += ((observed - expected) ** 2) / expected
    
    # Degrés de liberté: 256 - 1 = 255
    df = 255
    
    
    # Pour p=0.05: X^2_critique ~ 293.25
    critical_value = 293.25
    
    p_value = "< 0.05" if chi2 > critical_value else "> 0.05"
    
    return {
        'chi2': chi2,
        'degrees_freedom': df,
        'critical_value': critical_value,
        'p_value': p_value,
        'status': 'PASS' if chi2 < critical_value else 'FAIL'
    }


# 3) Autocorrélation
# https://fr.wikipedia.org/wiki/Autocorr%C3%A9lation

def autocorrelation(data, lag=1):
    """
    Calcule le coefficient d'autocorrélation pour un décalage donné
    
    Interprétation:
        r ~ 0 : pas de corrélation (donc c'est bon)
        |r| > 0.1 : corrélation détectable (donc suspect)
    
    Paramètres:
        data: liste de valeurs numériques
        lag: décalage (1 = valeurs consécutives)
    
    Retourne:
        Coefficient d'autocorrélation [-1, 1]
    """
    if len(data) < lag + 1:
        return 0.0
    
    n = len(data) - lag
    
    # Moyenne
    moy = sum(data) / len(data)
    
    # Variance
    variance = sum((x - moy)**2 for x in data)
    if variance == 0:
        return 0.0
    
    # Covariance avec décalage
    covariance = sum((data[i] - moy) * (data[i + lag] - moy) for i in range(n))
    
    # Coefficient
    r = covariance / variance
    
    return r


def autocorrelation_test(data, lags=[1, 8, 16, 32]):
    """
    Test d'autocorrélation pour plusieurs décalages
    
    Paramètres:
        data: octets ou liste d'entiers
        lags: liste de décalages à tester
    
    Retourne:
        dict avec coefficients pour chaque lag
    """
    if isinstance(data, bytes):
        data = list(data)
    
    results = {}
    threshold = 0.05  # Seuil tolérance
    
    for lag in lags:
        r = autocorrelation(data, lag)
        results[f'lag_{lag}'] = {
            'coefficient': r,
            'status': 'PASS' if abs(r) < threshold else 'FAIL'
        }
    
    return results


# 4) Test de kolmogorov-Smirnov
# http://fr.wikipedia.org/wiki/Test_de_Kolmogorov-Smirnov

def kolmogorov_smirnov_test(data):
    """
    Test KS pour comparer distribution empirique vs uniforme [0, 255]
    
    Paramètres:
        data: octets ou liste d'entiers [0-255]
    
    Retourne:
        dico avec statistique, verdict
    """
    if not data:
        return None
    
    # On normalise dans [0, 1]
    normalized = sorted([x / 255.0 for x in data])
    n = len(normalized)
    
    # Calculer D (distance maximale)
    max_diff = 0.0
    
    for i, value in enumerate(normalized):
        # Empirique au point i
        empi = (i + 1) / n
        
        # Théorique uniforme [0,1]
        theo = value
        
        # Distance
        diff = abs(empi - theo)
        max_diff = max(max_diff, diff)
    
    # Valeur critique (approximation pour n > 35)
    # D_critique = 1.36 / sqrt(n) pour alpha = 0.05
    critical_value = 1.36 / math.sqrt(n)
    
    return {
        'D': max_diff,
        'critical_value': critical_value,
        'n': n,
        'status': 'PASS' if max_diff < critical_value else 'FAIL'
    }


# Final

def full_statistical_res(data):
    """
    Tests
    
    Paramètres:
        data: octets ou liste d'entiers
    
    Retourne:
        dico avec résultats de tous les tests
    """
    if isinstance(data, bytes):
        data_list = list(data)
    else:
        data_list = data
    
    res = {
        'data_size': len(data_list),
        'shannon_entropy': shannon_entropy_res(data_list),
        'chi_squared': chi_squared_test(data_list),
        'autocorrelation': autocorrelation_test(data_list),
        'kolmogorov_smirnov': kolmogorov_smirnov_test(data_list)
    }
    
    tests_passed = sum([
        res['shannon_entropy']['status'] == 'PASS',
        res['chi_squared']['status'] == 'PASS',
        all(v['status'] == 'PASS' for v in res['autocorrelation'].values()),
        res['kolmogorov_smirnov']['status'] == 'PASS'
    ])
    
    res['global_status'] = {
        'passed': tests_passed,
        'total': 4,
        'verdict': 'PASS' if tests_passed >= 3 else 'FAIL'
    }
    
    return res


def print_res(res):
    print("RAPPORT DE TESTS STATISTIQUES")
    
    print(f"\nTaille échantillon: {res['data_size']} octets")  
    
    print("\n1. ENTROPIE DE SHANNON \n") 
    ent = res['shannon_entropy']
    print(f"   Entropie: {ent['entropy']:.4f} bits/octet")
    print(f"   Maximum:  {ent['max_entropy']:.4f} bits/octet")
    print(f"   Pourcentage: {ent['percentage']:.2f}%")
    print(f"   Verdict: {ent['status']}")
    
    print("\n2. TEST CHI-CARRÉ (uniformité) \n")  
    chi = res['chi_squared']
    print(f"   X^2 = {chi['chi2']:.2f}")
    print(f"   Degrés liberté: {chi['degrees_freedom']}")
    print(f"   Valeur critique (α=0.05): {chi['critical_value']:.2f}")
    print(f"   P-value: {chi['p_value']}")
    print(f"   Verdict: {chi['status']}")
    
    print("\n3. AUTOCORRÉLATION \n")  
    for lag_name, result in res['autocorrelation'].items():
        lag_num = lag_name.split('_')[1]
        print(f"   Lag {lag_num}: r = {result['coefficient']:+.6f} [{result['status']}]")
    
    print("\n4. TEST KOLMOGOROV-SMIRNOV \n") 
    ks = res['kolmogorov_smirnov']
    print(f"   D = {ks['D']:.6f}")
    print(f"   Valeur critique: {ks['critical_value']:.6f}")
    print(f"   Verdict: {ks['status']}")
    
    print("*"*50 + "\n")  
    print("Verdict Final \n") 
    global_st = res['global_status']
    print(f"   Tests réussis: {global_st['passed']}/{global_st['total']}")
    print(f"   STATUT: {global_st['verdict']}")
    print("*"*50 + "\n")  



# TESTS

if __name__ == "__main__":
    print("Tests unitaires des fonctions statistiques\n")  
    
    # Test 1: Données aléatoires
    import os
    print("Test 1: os.urandom (référence)")
    random_data = os.urandom(10000)
    res1 = full_statistical_res(random_data)
    print_res(res1)
    
    # Test 2: Données biaisées (répétées)
    print("\nTest 2: Données biaisées (motif répété)")  
    biased_data = bytes([0, 1, 2] * 1000)
    res2 = full_statistical_res(biased_data)
    print_res(res2)
    
    # Test 3: Données constantes (pire cas)
    print("\nTest 3: Données constantes (0x42 répété)")  
    constant_data = bytes([0x42] * 1000)
    res3 = full_statistical_res(constant_data)
    print_res(res3)



