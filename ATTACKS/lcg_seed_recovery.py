# attacks/lcg_seed_recovery.py

"""
Pedagogical attack: LCG seed recovery
Demonstrates why LCG is UNSUITABLE for cryptography
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GENERATORS.PRNG_non_cryptographics.lcg import lcg, PARAMS_GLIBC



# METHOD 1: ALGEBRAIC RESOLUTION

def recover_seed_algebrique(x1, x2, x3, a, c, m):
    """
    Recovers X_0 from 3 consecutive outputs

    Mathematical principle:
        X_1 = (a*X_0 + c) mod m
        X_2 = (a*X_1 + c) mod m

        Inversion: X_0 = (X_1 - c) * a^(-1) mod m

    Complexity: O(log m) for modular inverse

    Parameters:
        x1, x2, x3: observed outputs
        a, c, m: LCG parameters (assumed public)

    Returns:
        X_0 (seed) or None on failure
    """
    try:
        # Modular inverse of a
        a_inv = pow(a, -1, m)
    except ValueError:
        print("Error: gcd(a, m) != 1")
        return None

    # Recover: X_0 = (X_1 - c) * a^(-1) mod m
    x0 = ((x1 - c) * a_inv) % m

    return x0


# METHOD 2: BRUTE FORCE

def recover_seed_bruteforce(outputs, a, c, m, seed_max=1000000):
    """
    Exhaustive search over a limited seed space

    Scenario: weak seed (e.g. timestamp, PID, counter)

    Complexity: O(seed_max * len(outputs))

    Parameters:
        outputs: observed outputs (>= 3 for validation)
        a, c, m: LCG parameters
        seed_max: search limit

    Returns:
        Found seed or None
    """
    for candidate in range(seed_max):
        generated = lcg(candidate, a, c, m, len(outputs))
        if generated == outputs:
            return candidate
    return None


# METHOD 3: KNOWN-PLAINTEXT (XOR encryption)

def xor_bytes(b1, b2):
    """XOR of two byte strings"""
    return bytes(a ^ b for a, b in zip(b1, b2))


def recover_seed_from_xor(plaintext, ciphertext, a, c, m, seed_max=100000):
    """
    Known-plaintext attack on XOR + LCG encryption

    Scenario:
        1. Victim encrypts: C = P XOR LCG_keystream
        2. Attacker knows P and C
        3. Recovers keystream: K = P XOR C
        4. Brute-forces seeds until match

    Parameters:
        plaintext: known plaintext
        ciphertext: intercepted ciphertext
        a, c, m: LCG parameters
        seed_max: search space

    Returns:
        Found seed or None
    """
    # Step 1: Recover keystream
    keystream = xor_bytes(plaintext, ciphertext)
    keystream_ints = list(keystream)

    # Step 2: Search for seed
    for candidate in range(seed_max):
        generated = lcg(candidate, a, c, m, len(keystream))
        generated_bytes = [x % 256 for x in generated]

        if generated_bytes == keystream_ints:
            return candidate

    return None



# DEMOS

def demo_1_algebraic():
    """Demo: Recovery from 3 outputs"""
    print("ATTACK 1: Algebraic recovery")
    print("\nThreat model:")
    print("  - Attacker observes 3 consecutive LCG outputs")
    print("  - Parameters (a, c, m) are public/known")
    print("  - Goal: recover X_0 and predict future outputs")

    # Setup
    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    secret_seed = 123456789

    # Victim generates 3 outputs
    outputs = lcg(secret_seed, a, c, m, 3)

    print(f"\n[Victim] Secret seed: {secret_seed}")
    print(f"[Victim] Generates: {outputs[:3]}")

    # Attack
    print("\n[Attacker] Observing 3 outputs...")
    recovered = recover_seed_algebrique(outputs[0], outputs[1], outputs[2], a, c, m)

    print(f"[Attacker] Recovered seed: {recovered}")
    print(f"\n Success: {recovered == secret_seed}")

    # Prediction
    print("\nPredicting future outputs")
    future_real = lcg(secret_seed, a, c, m, 8)[3:]
    future_pred = lcg(recovered, a, c, m, 8)[3:]

    print(f"Real:      {future_real}")
    print(f"Predicted: {future_pred}")
    print(f"Match: {future_real == future_pred}")

    print("\n[Conclusion] LCG fully compromised in 3 outputs.")


def demo_2_bruteforce():
    """Demo: Brute force over small space"""
    print("ATTACK 2: Brute force (limited space)")
    print("\nThreat model:")
    print("  - Weak seed (e.g. PID, truncated timestamp)")
    print("  - Space: [0, 100000)")
    print("  - Multiple observed outputs for validation")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    secret_seed = 42424
    outputs = lcg(secret_seed, a, c, m, 5)

    print(f"\n[Victim] Seed: {secret_seed} (within [0, 100000))")
    print(f"[Victim] Outputs: {outputs}")

    print("\n[Attacker] Starting exhaustive search...")
    recovered = recover_seed_bruteforce(outputs, a, c, m, seed_max=100000)

    print(f"[Attacker] Found seed: {recovered}")
    print(f"\nSuccess: {recovered == secret_seed}")

    print("\n[Conclusion] Weak seeds = trivial attack.")


def demo_3_known_plaintext():
    """Demo: Known-plaintext attack on XOR"""
    print("ATTACK 3: Known-plaintext (XOR + LCG encryption)")
    print("\nThreat model:")
    print("  - Victim encrypts with: C = P XOR LCG_keystream")
    print("  - Attacker knows/guesses plaintext P")
    print("  - Attacker intercepts ciphertext C")
    print("  - Goal: recover seed and decrypt other messages")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    secret_seed = 31337
    plaintext = b"ATTACK_AT_DAWN"

    # Encryption
    keystream_vals = lcg(secret_seed, a, c, m, len(plaintext))
    keystream = bytes([x % 256 for x in keystream_vals])
    ciphertext = xor_bytes(plaintext, keystream)

    print(f"\n[Victim] Plaintext:  {plaintext}")
    print(f"[Victim] Ciphertext: {ciphertext.hex()}")

    # Attack
    print("\n[Attacker] Recovering keystream: K = P XOR C")
    recovered_keystream = xor_bytes(plaintext, ciphertext)
    print(f"[Attacker] Keystream: {recovered_keystream.hex()}")

    print("\n[Attacker] Brute-forcing seeds...")
    recovered_seed = recover_seed_from_xor(plaintext, ciphertext, a, c, m, seed_max=50000)

    print(f"\n[Attacker] Recovered seed: {recovered_seed}")
    print(f"Success: {recovered_seed == secret_seed}")

    # Exploitation
    print("\nExploitation: decrypting another message")
    other_plaintext = b"SECRET_KEY_42"
    other_keystream_vals = lcg(recovered_seed, a, c, m, len(other_plaintext))
    other_keystream = bytes([x % 256 for x in other_keystream_vals[:len(other_plaintext)]])
    other_ciphertext = xor_bytes(other_plaintext, other_keystream)

    # Attacker decrypts
    decrypted = xor_bytes(other_ciphertext, other_keystream)
    print(f"[Victim] Encrypts new message: {other_ciphertext.hex()}")
    print(f"[Attacker] Decrypts: {decrypted}")
    print(f"Decryption successful: {decrypted == other_plaintext}")

    print("\n[Conclusion] LCG as keystream = CATASTROPHIC.")


def run_all_attacks():
    """Run all demonstrations"""
    print("# DEMOS: ATTACKS AGAINST LCG")

    demo_1_algebraic()
    demo_2_bruteforce()
    demo_3_known_plaintext()



if __name__ == "__main__":
    run_all_attacks()
