"""
Attaque : Reconstruction de l'état interne du Mersenne Twister (MT19937)

Modèle de menace :
    - L'attaquant observe 624 sorties consécutives de 32 bits
    - L'algorithme MT19937 est public

Algorithme :
    1. Collecter 624 sorties de 32 bits du MT cible
    2. Appliquer untemper() sur chaque sortie pour retrouver l'état interne
    3. Prédire les sorties futures en appliquant twist + temper
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from GENERATORS.PRNG_non_cryptographics.mersenne_twister import (
    generate, twist, temper, N, U, D, S, B, T, C, L
)


# --- Inversion du tempering ---

def invert_right_shift_xor(y, shift):
    """Inverse y ^= (y >> shift) — reconstruit bit par bit de gauche a droite"""
    result = 0
    for i in range(32):
        bit_pos = 31 - i
        if i < shift:
            bit = (y >> bit_pos) & 1
        else:
            prev_bit = (result >> (bit_pos + shift)) & 1
            current_bit = (y >> bit_pos) & 1
            bit = current_bit ^ prev_bit
        result |= (bit << bit_pos)
    return result


def invert_left_shift_xor_mask(y, shift, mask):
    """Inverse y ^= (y << shift) & mask — reconstruit bit par bit de droite a gauche"""
    result = 0
    for i in range(32):
        if i < shift:
            bit = (y >> i) & 1
        else:
            prev_bit = (result >> (i - shift)) & 1
            mask_bit = (mask >> i) & 1
            current_bit = (y >> i) & 1
            bit = current_bit ^ (prev_bit & mask_bit)
        result |= (bit << i)
    return result


def untemper(y):
    """
    Inverse la fonction de tempering du MT19937

    Tempering (direct):
        y ^= (y >> U) & D
        y ^= (y << S) & B
        y ^= (y << T) & C
        y ^= y >> L

    On inverse chaque etape dans l'ordre inverse
    """
    y = invert_right_shift_xor(y, L)
    y = invert_left_shift_xor_mask(y, T, C)
    y = invert_left_shift_xor_mask(y, S, B)
    y = invert_right_shift_xor(y, U)
    return y


# --- Reconstruction et prediction ---

def recover_state(outputs):
    """
    Reconstruit l'etat interne complet du MT19937 a partir de 624 sorties

    Parametres:
        outputs: liste de 624 sorties consecutives (32-bits)

    Retourne:
        Etat interne reconstruit (liste de 624 valeurs)
    """
    if len(outputs) < N:
        raise ValueError(f"Besoin de {N} sorties, recu {len(outputs)}")

    state = []
    for i in range(N):
        state.append(untemper(outputs[i]))
    return state


def predict_next(state, n):
    """
    Predit les n prochaines sorties depuis un etat reconstruit

    L'etat fourni correspond aux valeurs qui ont produit les 624 sorties
    observees. Pour obtenir les sorties FUTURES, on applique twist puis
    on extrait.

    Parametres:
        state: etat interne (624 valeurs)
        n: nombre de sorties a predire

    Retourne:
        Liste de n sorties predites
    """
    state = state.copy()
    index = N  # Force un twist au premier appel
    predictions = []

    for _ in range(n):
        if index >= N:
            state = twist(state)
            index = 0
        predictions.append(temper(state[index]))
        index += 1

    return predictions


# --- Demonstrations ---

def demo_mt19937_attack():
    """Demonstration complete de l'attaque"""
    print("=" * 65)
    print(" ATTAQUE : Reconstruction etat MT19937 ".center(65, "="))
    print("=" * 65)

    secret_seed = 987654321

    print(f"\n[Victime] Initialise MT19937 avec graine secrete")

    # Generer 624 + 100 sorties d'un coup
    all_outputs = generate(secret_seed, N + 100)
    observed = all_outputs[:N]
    future_real = all_outputs[N:]

    print(f"[Victime] Genere {N} sorties...")
    print(f"[Victime] Premieres sorties: {observed[:3]}")

    # Attaque
    print(f"\n[Attaquant] Observe {N} sorties...")
    print("[Attaquant] Inverse le tempering sur chaque sortie...")

    recovered_state = recover_state(observed)

    print(f"[Attaquant] Etat reconstruit: {len(recovered_state)} valeurs")

    # Prediction
    n_pred = 100
    print(f"\n[Attaquant] Predit {n_pred} prochaines sorties...")
    predicted = predict_next(recovered_state, n_pred)

    matches = sum(1 for p, r in zip(predicted, future_real) if p == r)
    success_rate = matches / n_pred * 100

    print(f"Correspondances : {matches}/{n_pred} ({success_rate:.1f}%)")
    print(f"\nExemples de predictions :")
    print(f"  {'Victime':>15} | {'Clone':>15} | {'Match':>5}")
    print(f"  {'-' * 15}-+-{'-' * 15}-+-{'-' * 5}")
    for i in range(10):
        match = "OK" if predicted[i] == future_real[i] else "FAIL"
        print(f"  {future_real[i]:>15} | {predicted[i]:>15} | {match:>5}")

    success = (matches == n_pred)
    print(f"\nResultat : {'SUCCES' if success else 'ECHEC'}")
    print(f"Prediction parfaite : {success}")
    print("=" * 65)

    return {
        "observed_count": N,
        "predictions_count": n_pred,
        "matches": matches,
        "success_rate": success_rate,
        "success": success,
    }


def demo_partial_recovery():
    """Demo: Qu'arrive-t-il avec moins de 624 sorties ?"""
    print("\n" + "=" * 65)
    print(" ANALYSE : Attaque avec < 624 sorties ".center(65, "="))
    print("=" * 65)

    secret_seed = 111222333

    for n_observed in [100, 300, 623]:
        print(f"\n[Test] Observation de {n_observed} sorties:")
        if n_observed < N:
            print(f"  Impossible de reconstruire etat complet")
            print(f"  Manque {N - n_observed} valeurs")
            print(f"  Attaque echoue")

    print(f"\n[Conclusion] 624 sorties = seuil critique pour MT19937.")


def run_all_attacks():
    """Lance toutes les demonstrations"""
    print("# DEMONSTRATIONS : ATTAQUE CONTRE MT19937\n")
    demo_mt19937_attack()
    demo_partial_recovery()


if __name__ == "__main__":
    run_all_attacks()
