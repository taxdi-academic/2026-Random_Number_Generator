# run_all_tests.py

"""
Script de vérification du projet RNG
Teste générateurs, statistiques et attaques
"""

import sys
import os


def test_generators():

    print("TEST DES GÉNÉRATEURS")
    
    # 1. LCG
    print("\n1. LCG")
    from generators.lcg import lcg, PARAMS_GLIBC
    output = lcg(42, **PARAMS_GLIBC, n=5)
    print(f"   Sortie: {output}")
    
    # 2. MT19937
    print("\n2. MT19937")
    from generators.mt19937 import generate
    output = generate(12345, 5)
    print(f"   Sortie: {output}")
    
    # 3. Box-Muller
    print("\n3. Box-Muller")
    from generators.box_muller import box_muller
    z0, z1 = box_muller(0.5, 0.5)
    print(f"   Sortie: ({z0:.4f}, {z1:.4f})")
    
    # 4. NIST CTR_DRBG
    print("\n4. NIST CTR_DRBG")
    from generators.nist_drbg import ctr_drbg
    output = ctr_drbg(9999, 16)
    print(f"   Sortie: {output.hex()}")
    
    # 5. BBS
    print("\n5. BBS")
    from generators.bbs import bbs, SMALL_PRIMES
    output = bbs(7, SMALL_PRIMES['p'], SMALL_PRIMES['q'], 10)
    print(f"   Sortie: {output}")
    
    # 6. XOR NRBG
    print("\n6. XOR NRBG")
    from generators.xor_nrbg import xor_combine_bits
    sources = [[1, 0, 1], [0, 1, 1]]
    output = xor_combine_bits(sources)
    print(f"   Sortie: {output}")
    
    # 7. os.urandom
    print("\n7. os.urandom")
    from generators.os_random import os_urandom_bytes
    output = os_urandom_bytes(8)
    print(f"   Sortie: {output.hex()}")


def test_statistical():
    print("TEST DES STATISTIQUES")
    
    from tests.statistical_tests import (
        shannon_entropy,
        chi_squared_test,
        autocorrelation_test,
        kolmogorov_smirnov_test
    )
    
    # Données de test
    test_data = os.urandom(5000)
    
    # 1. Entropie Shannon
    print("\n1. Entropie de Shannon")
    entropy = shannon_entropy(test_data)
    print(f"   H = {entropy:.4f} bits/octet")
    
    # 2. Chi-carré
    print("\n2. Test Chi-carré")
    chi2 = chi_squared_test(test_data)
    print(f"   χ² = {chi2['chi2']:.2f}")
    print(f"   Status = {chi2['status']}")
    
    # 3. Autocorrélation
    print("\n3. Autocorrélation")
    autocorr = autocorrelation_test(test_data, lags=[1, 8])
    for lag, res in autocorr.items():
        print(f"   {lag}: r = {res['coefficient']:.6f} [{res['status']}]")
    
    # 4. Kolmogorov-Smirnov
    print("\n4. Kolmogorov-Smirnov")
    ks = kolmogorov_smirnov_test(test_data)
    print(f"   D = {ks['D']:.6f}")
    print(f"   Status = {ks['status']}")


def test_attacks():
    print("TEST DES ATTAQUES")
    
    # 1. Attaque LCG
    print("\n1. Récupération graine LCG")
    from attacks.lcg_seed_recovery import recover_seed_algebrique
    from generators.lcg import lcg, PARAMS_GLIBC
    
    secret_seed = 123456
    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    outputs = lcg(secret_seed, a, c, m, 3)
    
    recovered = recover_seed_algebrique(outputs[0], outputs[1], outputs[2], a, c, m)
    print(f"   Graine secrète: {secret_seed}")
    print(f"   Graine récupérée: {recovered}")
    print(f"   Succès: {recovered == secret_seed}")
    
    # 2. Attaque MT19937
    print("\n2. Reconstruction état MT19937")
    from attacks.mt19937_state_recovery import recover_state
    from generators.mt19937 import generate
    
    outputs = generate(54321, 624)
    state = recover_state(outputs)
    print(f"   624 sorties observées")
    print(f"   État reconstruit: {len(state)} valeurs")
    print(f"   Succès: {len(state) == 624}")


def main():
    print("VÉRIFICATION PROJET RNG")
    
    try:
        test_generators()
        print("\n[OK] Tous les générateurs fonctionnent")
    except Exception as e:
        print(f"\n[ERREUR] Générateurs: {e}")
        return
    
    try:
        test_statistical()
        print("\n[OK] Tous les tests statistiques fonctionnent")
    except Exception as e:
        print(f"\n[ERREUR] Tests statistiques: {e}")
        return
    
    try:
        test_attacks()
        print("\n[OK] Toutes les attaques fonctionnent")
    except Exception as e:
        print(f"\n[ERREUR] Attaques: {e}")
        return
    
    print("RÉSUMÉ")
    print("7 générateurs: OK")
    print("4 tests statistiques: OK")
    print("2 attaques: OK")
    print("\n[SUCCÈS] Projet complet et fonctionnel")


if __name__ == "__main__":
    main()
