# attacks/lcg_seed_recovery.py

"""
Attaque pédagogique : Récupération de la graine LCG
Démontre pourquoi LCG est INADAPTÉ pour la cryptographie
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GENERATORS.PRNG_non_cryptographics.lcg import lcg, PARAMS_GLIBC



# MÉTHODE 1 : RÉSOLUTION ALGÉBRIQUE

def recover_seed_algebrique(x1, x2, x3, a, c, m):
    """
    Récupère X_0 à partir de 3 sorties consécutives
    
    Principe mathématique:
        X_1 = (a*X_0 + c) mod m
        X_2 = (a*X_1 + c) mod m
        
        On inverse: X_0 = (X_1 - c) * a^(-1) mod m
    
    Complexité: O(log m) pour l'inverse modulaire
    
    Paramètres:
        x1, x2, x3: sorties observées
        a, c, m: paramètres LCG (supposés publics)
    
    Retourne:
        X_0 (graine) ou None si échec
    """
    try:
        # Inverse modulaire de a
        a_inv = pow(a, -1, m)
    except ValueError:
        print("Erreur: pgcd(a, m) ≠ 1")
        return None
    
    # Remonter: X_0 = (X_1 - c) * a^(-1) mod m
    x0 = ((x1 - c) * a_inv) % m
    
    return x0


# MÉTHODE 2 : FORCE BRUTE

def recover_seed_bruteforce(outputs, a, c, m, seed_max=1000000):
    """
    Recherche exhaustive sur espace de graines limité
    
    Scénario: Graine faible (ex: timestamp, PID, compteur)
    
    Complexité: O(seed_max * len(outputs))
    
    Paramètres:
        outputs: sorties observées (≥3 pour validation)
        a, c, m: paramètres LCG
        seed_max: limite recherche
    
    Retourne:
        Graine trouvée ou None
    """
    for candidate in range(seed_max):
        generated = lcg(candidate, a, c, m, len(outputs))
        if generated == outputs:
            return candidate
    return None


# MÉTHODE 3 : KNOWN-PLAINTEXT (chiffrement XOR)

def xor_bytes(b1, b2):
    """XOR de deux bytes"""
    return bytes(a ^ b for a, b in zip(b1, b2))


def recover_seed_from_xor(plaintext, ciphertext, a, c, m, seed_max=100000):
    """
    Attaque known-plaintext sur chiffrement XOR + LCG
    
    Scénario:
        1. Victime chiffre: C = P [(+)xor] LCG_keystream
        2. Attaquant connaît P et C
        3. Récupère keystream: K = P [(+)xor] C
        4. Force brute sur graines jusqu'à match
    
    Paramètres:
        plaintext: message clair connu
        ciphertext: message chiffré intercepté
        a, c, m: paramètres LCG
        seed_max: espace recherche
    
    Retourne:
        Graine trouvée ou None
    """
    # Étape 1: Récupérer keystream
    keystream = xor_bytes(plaintext, ciphertext)
    keystream_ints = list(keystream)
    
    # Étape 2: Recherche graine
    for candidate in range(seed_max):
        generated = lcg(candidate, a, c, m, len(keystream))
        generated_bytes = [x % 256 for x in generated]
        
        if generated_bytes == keystream_ints:
            return candidate
    
    return None



# DÉMOS

def demo_1_algebraic():
    """Démo: Récupération en 3 sorties"""
    print("ATTAQUE 1 : Récupération algébrique")
    print("\nModèle de menace:")
    print("  - Attaquant observe 3 sorties consécutives du LCG")
    print("  - Paramètres (a, c, m) sont publics/connus")
    print("  - Objectif: Retrouver X_0 et prédire futures sorties")
    
    # Configuration
    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    secret_seed = 123456789
    
    # Victime génère 3 sorties
    outputs = lcg(secret_seed, a, c, m, 3)
    
    print(f"\n[Victime] Graine secrète: {secret_seed}")
    print(f"[Victime] Génère: {outputs[:3]}")
    
    # Attaque
    print("\n[Attaquant] Observe les 3 sorties...")
    recovered = recover_seed_algebrique(outputs[0], outputs[1], outputs[2], a, c, m)
    
    print(f"[Attaquant] Graine récupérée: {recovered}")
    print(f"\n Succès: {recovered == secret_seed}")
    
    # Prédiction
    print("\nPrédiction sorties futures")
    future_real = lcg(secret_seed, a, c, m, 8)[3:]
    future_pred = lcg(recovered, a, c, m, 8)[3:]
    
    print(f"Réelles:  {future_real}")
    print(f"Prédites: {future_pred}")
    print(f"Match: {future_real == future_pred}")
    
    print("\n[Conclusion] LCG compromis totalement en 3 sorties.")


def demo_2_bruteforce():
    """Démo: Force brute sur petit espace"""
    print("ATTAQUE 2 : Force brute (espace limité)")
    print("\nModèle de menace:")
    print("  - Graine faible (ex: PID, timestamp tronqué)")
    print("  - Espace: [0, 100000)")
    print("  - Plusieurs sorties observées pour validation")
    
    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    secret_seed = 42424
    outputs = lcg(secret_seed, a, c, m, 5)
    
    print(f"\n[Victime] Graine: {secret_seed} (dans [0, 100000))")
    print(f"[Victime] Sorties: {outputs}")
    
    print("\n[Attaquant] Lance recherche exhaustive...")
    recovered = recover_seed_bruteforce(outputs, a, c, m, seed_max=100000)
    
    print(f"[Attaquant] Graine trouvée: {recovered}")
    print(f"\nSuccès: {recovered == secret_seed}")
    
    print("\n[Conclusion] Graines faibles = attaque triviale.")


def demo_3_known_plaintext():
    """Démo: Attaque known-plaintext sur XOR"""
    print("ATTAQUE 3 : Known-plaintext (chiffrement XOR + LCG)")
    print("\nModèle de menace:")
    print("  - Victime chiffre avec: C = P [(+)xor] LCG_keystream")
    print("  - Attaquant connaît/devine plaintext P")
    print("  - Attaquant intercepte ciphertext C")
    print("  - Objectif: Récupérer graine et déchiffrer autres messages")
    
    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    secret_seed = 31337
    plaintext = b"ATTACK_AT_DAWN"
    
    # Chiffrement
    keystream_vals = lcg(secret_seed, a, c, m, len(plaintext))
    keystream = bytes([x % 256 for x in keystream_vals])
    ciphertext = xor_bytes(plaintext, keystream)
    
    print(f"\n[Victime] Plaintext:  {plaintext}")
    print(f"[Victime] Ciphertext: {ciphertext.hex()}")
    
    # Attaque
    print("\n[Attaquant] Récupère keystream: K = P [+(xor)] C")
    recovered_keystream = xor_bytes(plaintext, ciphertext)
    print(f"[Attaquant] Keystream: {recovered_keystream.hex()}")
    
    print("\n[Attaquant] Force brute sur graines...")
    recovered_seed = recover_seed_from_xor(plaintext, ciphertext, a, c, m, seed_max=50000)
    
    print(f"\n[Attaquant] Graine récupérée: {recovered_seed}")
    print(f"Succès: {recovered_seed == secret_seed}")
    
    # Exploitation
    print("\nExploitation: Déchiffrer autre message")
    other_plaintext = b"SECRET_KEY_42"
    other_keystream_vals = lcg(recovered_seed, a, c, m, len(other_plaintext))
    other_keystream = bytes([x % 256 for x in other_keystream_vals[:len(other_plaintext)]])
    other_ciphertext = xor_bytes(other_plaintext, other_keystream)
    
    # Attaquant déchiffre
    decrypted = xor_bytes(other_ciphertext, other_keystream)
    print(f"[Victime] Chiffre nouveau message: {other_ciphertext.hex()}")
    print(f"[Attaquant] Déchiffre: {decrypted}")
    print(f"Déchiffrement réussi: {decrypted == other_plaintext}")
    
    print("\n[Conclusion] LCG comme keystream = CATASTROPHIQUE.")


def run_all_attacks():
    """Lance toutes les démonstrations"""
    print("# DÉMOS (test simple) : ATTAQUES CONTRE LCG")
    
    demo_1_algebraic()
    demo_2_bruteforce()
    demo_3_known_plaintext()



if __name__ == "__main__":
    run_all_attacks()
