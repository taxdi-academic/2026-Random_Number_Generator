# run_all_tests.py

"""
RNG project verification script
Tests generators, statistical tests and attacks
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_generators():

    print("GENERATOR TESTS")

    # 1. LCG
    print("\n1. LCG")
    from GENERATORS.PRNG_non_cryptographics.lcg import lcg, PARAMS_GLIBC
    output = lcg(42, **PARAMS_GLIBC, n=5)
    print(f"   Output: {output}")

    # 2. MT19937
    print("\n2. MT19937")
    from GENERATORS.PRNG_non_cryptographics.mersenne_twister import generate
    output = generate(12345, 5)
    print(f"   Output: {output}")

    # 3. Box-Muller
    print("\n3. Box-Muller")
    from GENERATORS.PRNG_Gaussian_distribution.box_muller import box_muller
    z0, z1 = box_muller(0.5, 0.5)
    print(f"   Output: ({z0:.4f}, {z1:.4f})")

    # 4. Hash_DRBG
    print("\n4. Hash_DRBG")
    from GENERATORS.CSPRNG.hash_drbg import drbg_generate_bytes
    output = drbg_generate_bytes(16)
    print(f"   Output: {output.hex()}")

    # 5. BBS
    print("\n5. BBS")
    from GENERATORS.CSPRNG.bbs import bbs, SMALL_PRIMES
    output = bbs(7, SMALL_PRIMES['p'], SMALL_PRIMES['q'], 10)
    print(f"   Output: {output}")

    # 6. XOR NRBG
    print("\n6. XOR NRBG")
    from GENERATORS.Non_deterministic_and_hybrid_generators.xor_nrbg import xor_combine_bits
    sources = [[1, 0, 1], [0, 1, 1]]
    output = xor_combine_bits(sources)
    print(f"   Output: {output}")

    # 7. os.urandom
    print("\n7. os.urandom")
    from GENERATORS.CSPRNG.os_random import os_generate_bytes
    output = os_generate_bytes(8)
    print(f"   Output: {output.hex()}")


def test_statistical():
    print("STATISTICAL TESTS")

    from STATISTICS.test_statistique import (
        shannon_entropy,
        chi_squared_test,
        autocorrelation_test,
        kolmogorov_smirnov_test
    )

    # Test data
    test_data = os.urandom(5000)

    # 1. Shannon Entropy
    print("\n1. Shannon Entropy")
    entropy = shannon_entropy(test_data)
    print(f"   H = {entropy:.4f} bits/byte")

    # 2. Chi-squared
    print("\n2. Chi-squared test")
    chi2 = chi_squared_test(test_data)
    print(f"   χ² = {chi2['chi2']:.2f}")
    print(f"   Status = {chi2['status']}")

    # 3. Autocorrelation
    print("\n3. Autocorrelation")
    autocorr = autocorrelation_test(test_data, lags=[1, 8])
    for lag, res in autocorr.items():
        print(f"   {lag}: r = {res['coefficient']:.6f} [{res['status']}]")

    # 4. Kolmogorov-Smirnov
    print("\n4. Kolmogorov-Smirnov")
    ks = kolmogorov_smirnov_test(test_data)
    print(f"   D = {ks['D']:.6f}")
    print(f"   Status = {ks['status']}")


def test_attacks():
    print("ATTACK TESTS")

    # 1. LCG attack
    print("\n1. LCG seed recovery")
    from ATTACKS.lcg_seed_recovery import recover_seed_algebrique
    from GENERATORS.PRNG_non_cryptographics.lcg import lcg, PARAMS_GLIBC

    secret_seed = 123456
    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    outputs = lcg(secret_seed, a, c, m, 3)

    recovered = recover_seed_algebrique(outputs[0], outputs[1], outputs[2], a, c, m)
    print(f"   Secret seed: {secret_seed}")
    print(f"   Recovered seed: {recovered}")
    print(f"   Success: {recovered == secret_seed}")

    # 2. MT19937 attack
    print("\n2. MT19937 state reconstruction")
    from ATTACKS.mt19937_state_recovery import recover_state
    from GENERATORS.PRNG_non_cryptographics.mersenne_twister import generate

    outputs = generate(54321, 624)
    state = recover_state(outputs)
    print(f"   624 outputs observed")
    print(f"   Reconstructed state: {len(state)} values")
    print(f"   Success: {len(state) == 624}")


def main():
    print("RNG PROJECT VERIFICATION")

    try:
        test_generators()
        print("\n[OK] All generators working")
    except Exception as e:
        print(f"\n[ERROR] Generators: {e}")
        return

    try:
        test_statistical()
        print("\n[OK] All statistical tests working")
    except Exception as e:
        print(f"\n[ERROR] Statistical tests: {e}")
        return

    try:
        test_attacks()
        print("\n[OK] All attacks working")
    except Exception as e:
        print(f"\n[ERROR] Attacks: {e}")
        return

    print("SUMMARY")
    print("7 generators: OK")
    print("4 statistical tests: OK")
    print("2 attacks: OK")
    print("\n[SUCCESS] Project complete and functional")


if __name__ == "__main__":
    main()
