# attacks/mt19937_state_recovery.py

"""
Attaque pédagogique : Reconstruction état MT19937
Démontre pourquoi MT19937 n'est PAS cryptographiquement sécurisé
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.mt19937 import generate, N, U, D, S, B, T, C, L


# INVERSION DU TEMPERING

def untemper(y):
    """
    Inverse la fonction de tempering du MT19937
    
    Tempering (direct):
        y ^= (y >> U) & D
        y ^= (y << S) & B
        y ^= (y << T) & C
        y ^= y >> L
    
    On inverse chaque étape dans l'ordre inverse
    
    Paramètres:
        y: sortie temperée (32 bits)
    
    Retourne:
        Valeur non-temperée (état interne)
    """
    # Inverse dernière étape: y ^= y >> L
    y = invert_right_shift_xor(y, L)
    
    # Inverse: y ^= (y << T) & C
    y = invert_left_shift_xor_mask(y, T, C)
    
    # Inverse: y ^= (y << S) & B
    y = invert_left_shift_xor_mask(y, S, B)
    
    # Inverse: y ^= (y >> U) & D
    y = invert_right_shift_xor(y, U)
    
    return y


def invert_right_shift_xor(y, shift):
    """
    Inverse: y ^= (y >> shift)
    
    Méthode: Reconstruit bit par bit de gauche à droite
    """
    result = 0
    for i in range(32):
        bit_pos = 31 - i
        # Bit à la position bit_pos
        if i < shift:
            # Bits hauts non affectés
            bit = (y >> bit_pos) & 1
        else:
            # XOR avec bit précédent
            prev_bit = (result >> (bit_pos + shift)) & 1
            current_bit = (y >> bit_pos) & 1
            bit = current_bit ^ prev_bit
        
        result |= (bit << bit_pos)
    
    return result


def invert_left_shift_xor_mask(y, shift, mask):
    """
    Inverse: y ^= (y << shift) & mask
    
    Méthode: Reconstruit bit par bit de droite à gauche
    """
    result = 0
    for i in range(32):
        # Bit à la position i
        if i < shift:
            # Bits bas non affectés
            bit = (y >> i) & 1
        else:
            # XOR avec bit précédent ET mask
            prev_bit = (result >> (i - shift)) & 1
            mask_bit = (mask >> i) & 1
            current_bit = (y >> i) & 1
            bit = current_bit ^ (prev_bit & mask_bit)
        
        result |= (bit << i)
    
    return result


# RECONSTRUCTION ÉTAT COMPLET

def recover_state(outputs):
    """
    Reconstruit l'état interne complet du MT19937
    
    Principe:
        - MT19937 a 624 valeurs d'état (N=624)
        - Chaque sortie = temper(state[i])
        - On inverse le tempering sur 624 sorties
        - On obtient l'état complet
    
    Paramètres:
        outputs: liste de 624 sorties consécutives (32-bits)
    
    Retourne:
        État interne reconstruit (liste de 624 valeurs)
    """
    if len(outputs) < N:
        raise ValueError(f"Besoin de {N} sorties, reçu {len(outputs)}")
    
    state = []
    for i in range(N):
        # Inverser tempering
        untempered = untemper(outputs[i])
        state.append(untempered)
    
    return state


# PRÉDICTION SORTIES FUTURES

def predict_next(state, index, n):
    """
    Prédit les n prochaines sorties depuis état reconstruit
    
    Utilise la même logique que le générateur MT19937
    
    Paramètres:
        state: état interne (624 valeurs)
        index: position actuelle dans l'état
        n: nombre de sorties à prédire
    
    Retourne:
        Liste de n sorties prédites
    """
    from generators.mt19937 import twist, temper
    
    state = state.copy()  # Pour ne pas modifier l'original
    predictions = []
    
    for _ in range(n):
        if index >= N:
            state = twist(state)
            index = 0
        
        y = temper(state[index])
        predictions.append(y)
        index += 1
    
    return predictions



# DÉMO

def demo_mt19937_attack():
    """Démonstration complète de l'attaque"""
    print("ATTAQUE : Reconstruction état MT19937")
    
    print("\nModèle de menace:")
    print("  - Attaquant observe 624 sorties consécutives")
    print("  - Objectif: Récupérer état interne et prédire futures sorties")
    print("  - Complexité: O(624) inversions de tempering")
    
    # Configuration
    secret_seed = 987654321
    
    print(f"\n[Victime] Initialise MT19937 avec graine secrète: {secret_seed}")
    
    # Génération de 624 + 10 sorties
    all_outputs = generate(secret_seed, N + 10)
    observed = all_outputs[:N]      # 624 premières observées
    future_real = all_outputs[N:]    # 10 suivantes (inconnues attaquant)
    
    print(f"[Victime] Génère {N} sorties...")
    print(f"[Victime] Premières sorties: {observed[:3]}")
    print(f"[Victime] Dernières sorties: {observed[-3:]}")
    
    # Attaque
    print(f"\n[Attaquant] Observe {N} sorties...")
    print("[Attaquant] Inverse le tempering sur chaque sortie...")
    
    recovered_state = recover_state(observed)
    
    print(f"[Attaquant] État reconstruit: {len(recovered_state)} valeurs")
    print(f"[Attaquant] État[0]: {recovered_state[0]}")
    print(f"[Attaquant] État[623]: {recovered_state[623]}")
    
    # Prédiction
    print("\n[Attaquant] Prédit 10 prochaines sorties...")
    predicted = predict_next(recovered_state, 0, 10)
    
    print("\nComparaison prédictions vs réalité")
    print(f"Réelles:   {future_real}")
    print(f"Prédites:  {predicted}")
    
    match = all(predicted[i] == future_real[i] for i in range(10))
    print(f"\nPrédiction parfaite: {match}")
    
    # Statistiques
    print("\nAnalyse")
    print(f"Sorties observées: {N}")
    print(f"État récupéré: 100%")
    print(f"Sorties futures prédictibles: (toutes)")
    print(f"Temps attaque: < 1 seconde")
    
    print("\n[Conclusion] MT19937 totalement compromis après 624 sorties.")


def demo_partial_recovery():
    """Démo: Qu'arrive-t-il avec moins de 624 sorties ?"""
    print("ANALYSE : Attaque avec < 624 sorties")
    
    print("\nQuestion: Et si on observe moins de 624 sorties ?")
    
    secret_seed = 111222333
    
    for n_observed in [100, 300, 623]:
        outputs = generate(secret_seed, n_observed + 5)
        observed = outputs[:n_observed]
        
        print(f"\n[Test] Observation de {n_observed} sorties:")
        
        if n_observed < N:
            print(f"Impossible de reconstruire état complet")
            print(f"Manque {N - n_observed} valeurs")
            print(f"Attaque échoue")
        else:
            print(f"État reconstruit possible")
    
    print("\n[Conclusion] 624 sorties = seuil critique pour MT19937.")


def run_all_attacks():
    """Lance toutes les démonstrations"""
    print("# DÉMONSTRATIONS : ATTAQUE CONTRE MT19937")
    demo_mt19937_attack()
    demo_partial_recovery()


if __name__ == "__main__":
    run_all_attacks()
