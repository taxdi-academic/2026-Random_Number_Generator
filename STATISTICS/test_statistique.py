# tests/statistical_tests.py

"""
Statistical tests to evaluate random number generator quality
"""

import math
from collections import Counter


# 1) Shannon Entropy
# https://en.wikipedia.org/wiki/Entropy_(information_theory)

def shannon_entropy(data):
    """
    Computes Shannon entropy per byte

    Interpretation (H = entropy):
        - H = 8 bits: perfect entropy (fully random)
        - H < 8 bits: lower quality (patterns or predictability present)

    Parameters:
        data: bytes or list of integers [0-255]

    Returns:
        Entropy in bits per byte
    """
    if not data:
        return 0.0

    # Count frequency of each byte value
    freq = Counter(data)
    n = len(data)

    # Compute entropy
    entropy = 0.0
    for count in freq.values():
        p = count / n  # Uniform probability
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def shannon_entropy_res(data):
    """
    Detailed entropy report

    Returns:
        dict with entropy, theoretical maximum, percentage
    """
    entropy = shannon_entropy(data)
    max_entropy = 8.0  # 8 bits

    return {
        'entropy': entropy,
        'max_entropy': max_entropy,
        'percentage': (entropy / max_entropy) * 100,
        'status': 'PASS' if entropy > 7.9 else 'FAIL'
    }


# 2) Chi-squared test (X^2)
# https://en.wikipedia.org/wiki/Chi-squared_test

def chi_squared_test(data, p=0.05):
    """
    Test for uniform byte distribution

    Null hypothesis H_0: bytes are uniformly distributed

    Parameters:
        data: bytes or list of integers [0-255]
        p: significance level (0.05 = 5%)

    Returns:
        dict with test results
    """
    if not data:
        return None

    # Count occurrences
    freq = Counter(data)
    n = len(data)

    # Expected frequency for uniformity
    expected = n / 256

    # Compute X^2
    chi2 = 0.0
    for i in range(256):
        observed = freq.get(i, 0)
        chi2 += ((observed - expected) ** 2) / expected

    # Degrees of freedom: 256 - 1 = 255
    df = 255

    # For p=0.05: X^2_critical ~ 293.25
    critical_value = 293.25

    p_value = "< 0.05" if chi2 > critical_value else "> 0.05"

    return {
        'chi2': chi2,
        'degrees_freedom': df,
        'critical_value': critical_value,
        'p_value': p_value,
        'status': 'PASS' if chi2 < critical_value else 'FAIL'
    }


# 3) Autocorrelation
# https://en.wikipedia.org/wiki/Autocorrelation

def autocorrelation(data, lag=1):
    """
    Computes the autocorrelation coefficient for a given lag

    Interpretation:
        r ~ 0: no correlation (good)
        |r| > 0.1: detectable correlation (suspicious)

    Parameters:
        data: list of numeric values
        lag: shift (1 = consecutive values)

    Returns:
        Autocorrelation coefficient [-1, 1]
    """
    if len(data) < lag + 1:
        return 0.0

    n = len(data) - lag

    # Mean
    mean = sum(data) / len(data)

    # Variance
    variance = sum((x - mean)**2 for x in data)
    if variance == 0:
        return 0.0

    # Covariance with shift
    covariance = sum((data[i] - mean) * (data[i + lag] - mean) for i in range(n))

    # Coefficient
    r = covariance / variance

    return r


def autocorrelation_test(data, lags=[1, 8, 16, 32]):
    """
    Autocorrelation test for multiple lags

    Parameters:
        data: bytes or list of integers
        lags: list of lags to test

    Returns:
        dict with coefficients for each lag
    """
    if isinstance(data, bytes):
        data = list(data)

    results = {}
    threshold = 0.05  # Tolerance threshold

    for lag in lags:
        r = autocorrelation(data, lag)
        results[f'lag_{lag}'] = {
            'coefficient': r,
            'status': 'PASS' if abs(r) < threshold else 'FAIL'
        }

    return results


# 4) Kolmogorov-Smirnov test
# https://en.wikipedia.org/wiki/Kolmogorov%E2%80%93Smirnov_test

def kolmogorov_smirnov_test(data):
    """
    KS test comparing empirical distribution vs uniform [0, 255]

    Parameters:
        data: bytes or list of integers [0-255]

    Returns:
        dict with statistic and verdict
    """
    if not data:
        return None

    # Normalize to [0, 1]
    normalized = sorted([x / 255.0 for x in data])
    n = len(normalized)

    # Compute D (maximum distance)
    max_diff = 0.0

    for i, value in enumerate(normalized):
        # Empirical value at point i
        empi = (i + 1) / n

        # Theoretical uniform [0,1]
        theo = value

        # Distance
        diff = abs(empi - theo)
        max_diff = max(max_diff, diff)

    # Critical value (approximation for n > 35)
    # D_critical = 1.36 / sqrt(n) for alpha = 0.05
    critical_value = 1.36 / math.sqrt(n)

    return {
        'D': max_diff,
        'critical_value': critical_value,
        'n': n,
        'status': 'PASS' if max_diff < critical_value else 'FAIL'
    }


# Full report

def full_statistical_res(data):
    """
    Runs all statistical tests

    Parameters:
        data: bytes or list of integers

    Returns:
        dict with results of all tests
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
    print("STATISTICAL TEST REPORT")

    print(f"\nSample size: {res['data_size']} bytes")

    print("\n1. SHANNON ENTROPY\n")
    ent = res['shannon_entropy']
    print(f"   Entropy: {ent['entropy']:.4f} bits/byte")
    print(f"   Maximum: {ent['max_entropy']:.4f} bits/byte")
    print(f"   Percentage: {ent['percentage']:.2f}%")
    print(f"   Verdict: {ent['status']}")

    print("\n2. CHI-SQUARED TEST (uniformity)\n")
    chi = res['chi_squared']
    print(f"   X^2 = {chi['chi2']:.2f}")
    print(f"   Degrees of freedom: {chi['degrees_freedom']}")
    print(f"   Critical value (α=0.05): {chi['critical_value']:.2f}")
    print(f"   P-value: {chi['p_value']}")
    print(f"   Verdict: {chi['status']}")

    print("\n3. AUTOCORRELATION\n")
    for lag_name, result in res['autocorrelation'].items():
        lag_num = lag_name.split('_')[1]
        print(f"   Lag {lag_num}: r = {result['coefficient']:+.6f} [{result['status']}]")

    print("\n4. KOLMOGOROV-SMIRNOV TEST\n")
    ks = res['kolmogorov_smirnov']
    print(f"   D = {ks['D']:.6f}")
    print(f"   Critical value: {ks['critical_value']:.6f}")
    print(f"   Verdict: {ks['status']}")

    print("*"*50 + "\n")
    print("Final Verdict\n")
    global_st = res['global_status']
    print(f"   Tests passed: {global_st['passed']}/{global_st['total']}")
    print(f"   STATUS: {global_st['verdict']}")
    print("*"*50 + "\n")


# TESTS

if __name__ == "__main__":
    print("Unit tests for statistical functions\n")

    # Test 1: Random data
    import os
    print("Test 1: os.urandom (reference)")
    random_data = os.urandom(10000)
    res1 = full_statistical_res(random_data)
    print_res(res1)

    # Test 2: Biased data (repeated pattern)
    print("\nTest 2: Biased data (repeated pattern)")
    biased_data = bytes([0, 1, 2] * 1000)
    res2 = full_statistical_res(biased_data)
    print_res(res2)

    # Test 3: Constant data (worst case)
    print("\nTest 3: Constant data (0x42 repeated)")
    constant_data = bytes([0x42] * 1000)
    res3 = full_statistical_res(constant_data)
    print_res(res3)
