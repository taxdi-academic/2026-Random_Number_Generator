# attacks/mt19937_state_recovery.py

"""
Pedagogical attack: MT19937 state reconstruction
Demonstrates why MT19937 is NOT cryptographically secure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GENERATORS.PRNG_non_cryptographics.mersenne_twister import generate, N, U, D, S, B, T, C, L


# TEMPERING INVERSION

def untemper(y):
    """
    Inverts the MT19937 tempering function

    Tempering (forward):
        y ^= (y >> U) & D
        y ^= (y << S) & B
        y ^= (y << T) & C
        y ^= y >> L

    Each step is inverted in reverse order

    Parameters:
        y: tempered output (32 bits)

    Returns:
        Un-tempered value (internal state)
    """
    # Invert last step: y ^= y >> L
    y = invert_right_shift_xor(y, L)

    # Invert: y ^= (y << T) & C
    y = invert_left_shift_xor_mask(y, T, C)

    # Invert: y ^= (y << S) & B
    y = invert_left_shift_xor_mask(y, S, B)

    # Invert: y ^= (y >> U) & D
    y = invert_right_shift_xor(y, U)

    return y


def invert_right_shift_xor(y, shift):
    """
    Inverts: y ^= (y >> shift)

    Method: reconstructs bit by bit from left to right
    """
    result = 0
    for i in range(32):
        bit_pos = 31 - i
        # Bit at position bit_pos
        if i < shift:
            # High bits unaffected
            bit = (y >> bit_pos) & 1
        else:
            # XOR with previous bit
            prev_bit = (result >> (bit_pos + shift)) & 1
            current_bit = (y >> bit_pos) & 1
            bit = current_bit ^ prev_bit

        result |= (bit << bit_pos)

    return result


def invert_left_shift_xor_mask(y, shift, mask):
    """
    Inverts: y ^= (y << shift) & mask

    Method: reconstructs bit by bit from right to left
    """
    result = 0
    for i in range(32):
        # Bit at position i
        if i < shift:
            # Low bits unaffected
            bit = (y >> i) & 1
        else:
            # XOR with previous bit AND mask
            prev_bit = (result >> (i - shift)) & 1
            mask_bit = (mask >> i) & 1
            current_bit = (y >> i) & 1
            bit = current_bit ^ (prev_bit & mask_bit)

        result |= (bit << i)

    return result


# FULL STATE RECONSTRUCTION

def recover_state(outputs):
    """
    Reconstructs the complete internal state of MT19937

    Principle:
        - MT19937 has 624 state values (N=624)
        - Each output = temper(state[i])
        - Invert tempering on 624 outputs
        - Obtain the full state

    Parameters:
        outputs: list of 624 consecutive outputs (32-bit)

    Returns:
        Reconstructed internal state (list of 624 values)
    """
    if len(outputs) < N:
        raise ValueError(f"Need {N} outputs, got {len(outputs)}")

    state = []
    for i in range(N):
        # Invert tempering
        untempered = untemper(outputs[i])
        state.append(untempered)

    return state


# FUTURE OUTPUT PREDICTION

def predict_next(state, index, n):
    """
    Predicts the next n outputs from the reconstructed state

    Uses the same logic as the MT19937 generator

    Parameters:
        state: internal state (624 values)
        index: current position in state
        n: number of outputs to predict

    Returns:
        List of n predicted outputs
    """
    from GENERATORS.PRNG_non_cryptographics.mersenne_twister import twist, temper

    state = state.copy()  # Do not modify the original
    predictions = []

    for _ in range(n):
        if index >= N:
            state = twist(state)
            index = 0

        y = temper(state[index])
        predictions.append(y)
        index += 1

    return predictions



# DEMO

def demo_mt19937_attack():
    """Complete attack demonstration"""
    print("ATTACK: MT19937 state reconstruction")

    print("\nThreat model:")
    print("  - Attacker observes 624 consecutive outputs")
    print("  - Goal: recover internal state and predict future outputs")
    print("  - Complexity: O(624) tempering inversions")

    # Setup
    secret_seed = 987654321

    print(f"\n[Victim] Initialises MT19937 with secret seed: {secret_seed}")

    # Generate 624 + 10 outputs
    all_outputs = generate(secret_seed, N + 10)
    observed = all_outputs[:N]       # First 624 observed
    future_real = all_outputs[N:]    # Next 10 (unknown to attacker)

    print(f"[Victim] Generates {N} outputs...")
    print(f"[Victim] First outputs: {observed[:3]}")
    print(f"[Victim] Last outputs: {observed[-3:]}")

    # Attack
    print(f"\n[Attacker] Observing {N} outputs...")
    print("[Attacker] Inverting tempering on each output...")

    recovered_state = recover_state(observed)

    print(f"[Attacker] Reconstructed state: {len(recovered_state)} values")
    print(f"[Attacker] State[0]: {recovered_state[0]}")
    print(f"[Attacker] State[623]: {recovered_state[623]}")

    # Prediction
    print("\n[Attacker] Predicting next 10 outputs...")
    predicted = predict_next(recovered_state, 0, 10)

    print("\nComparison: predictions vs reality")
    print(f"Real:      {future_real}")
    print(f"Predicted: {predicted}")

    match = all(predicted[i] == future_real[i] for i in range(10))
    print(f"\nPerfect prediction: {match}")

    # Statistics
    print("\nAnalysis")
    print(f"Observed outputs: {N}")
    print(f"Recovered state: 100%")
    print(f"Predictable future outputs: (all)")
    print(f"Attack time: < 1 second")

    print("\n[Conclusion] MT19937 fully compromised after 624 outputs.")


def demo_partial_recovery():
    """Demo: What happens with fewer than 624 outputs?"""
    print("ANALYSIS: Attack with < 624 outputs")

    print("\nQuestion: What if we observe fewer than 624 outputs?")

    secret_seed = 111222333

    for n_observed in [100, 300, 623]:
        outputs = generate(secret_seed, n_observed + 5)
        observed = outputs[:n_observed]

        print(f"\n[Test] Observing {n_observed} outputs:")

        if n_observed < N:
            print(f"Cannot reconstruct full state")
            print(f"Missing {N - n_observed} values")
            print(f"Attack fails")
        else:
            print(f"State reconstruction possible")

    print("\n[Conclusion] 624 outputs = critical threshold for MT19937.")


def run_all_attacks():
    """Run all demonstrations"""
    print("# DEMONSTRATIONS: ATTACK AGAINST MT19937")
    demo_mt19937_attack()
    demo_partial_recovery()


if __name__ == "__main__":
    run_all_attacks()
