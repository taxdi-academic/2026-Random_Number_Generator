# Random Number Generator — Implementation, Testing and Attacks

Engineering school project on the implementation of pseudorandom number generators, statistical quality evaluation, and pedagogical cryptographic attacks.

> **Important notice**: All attacks implemented in this project are strictly for educational purposes and are prohibited on real systems without explicit authorization.

---

## Table of Contents

- [Context and Motivation](#context-and-motivation)
- [Project Objectives](#project-objectives)
- [Generators Implemented](#generators-implemented)
- [Statistical Tests](#statistical-tests)
- [Pedagogical Attacks](#pedagogical-attacks)
- [Project Structure](#project-structure)
- [Installation and Usage](#installation-and-usage)
- [References](#references)

---

## Context and Motivation

Randomness is at the heart of computer security protocols. Random numbers are used to generate secret keys, nonces, initialization vectors (IVs), and tokens. If the generation is insecure, an attacker can infer or predict subsequent values, compromising the entire system.

Even when robust theoretical constructions exist, they are sometimes poorly implemented. This project explores the spectrum from simple non-cryptographic PRNGs to standardized CSPRNGs, and demonstrates why the distinction matters.

---

## Project Objectives

- Implement several pseudorandom number generation methods in Python (PRNG and CSPRNG)
- Evaluate their quality using a suite of statistical tests
- Demonstrate pedagogical attacks exploiting PRNG weaknesses
- Compare the robustness of the studied generators
- Produce commented code and a written report

---

## Generators Implemented

### Non-Cryptographic PRNGs

| Generator | File | Description |
|-----------|------|-------------|
| Linear Congruential Generator (LCG) | `GENERATORS/PRNG_non_cryptographics/lcg.py` | Simple recurrence `X_{n+1} = (a*X_n + c) mod m`. Fast but linearly predictable. Includes glibc, RANDU and MMIX parameters. |
| Mersenne Twister (MT19937) | `GENERATORS/PRNG_non_cryptographics/mersenne_twister.py` | Period 2^19937−1, excellent statistical properties. Used by Python's `random` module. State reconstructible from 624 outputs. |

### Gaussian Distribution

| Generator | File | Description |
|-----------|------|-------------|
| Box-Muller Transform | `GENERATORS/PRNG_Gaussian_distribution/box_muller.py` | Converts two independent uniform values into two N(0,1) Gaussian values. Requires a uniform PRNG as input. |

### Cryptographically Secure PRNGs (CSPRNG)

| Generator | File | Description |
|-----------|------|-------------|
| Blum-Blum-Shub (BBS) | `GENERATORS/CSPRNG/bbs.py` | Based on quadratic residues modulo M=p×q. Provably secure under the factoring assumption. |
| Hash_DRBG (NIST SP 800-90A) | `GENERATORS/CSPRNG/hash_drbg.py` | SHA-256-based deterministic random bit generator. Compliant with NIST SP 800-90A. Supports instantiation, generation and reseed. |
| os.urandom | `GENERATORS/CSPRNG/os_random.py` | System interface to `/dev/urandom` (Linux). Hardware entropy sources. Reference CSPRNG for the project. |

### Non-Deterministic and Hybrid

| Generator | File | Description |
|-----------|------|-------------|
| XOR NRBG | `GENERATORS/Non_deterministic_and_hybrid_generators/xor_nrbg.py` | Combines multiple generators via XOR. If at least one source is truly random, the output remains unpredictable. |

---

## Statistical Tests

All tests are implemented in `STATISTICS/test_statistique.py`. Each test produces a PASS/FAIL verdict at significance level α = 0.05.

| Test | Criterion | What it detects |
|------|-----------|-----------------|
| Shannon Entropy | H > 7.9 bits/byte | Lack of diversity in byte values |
| Chi-squared (χ²) | χ² < 293.25 (df=255) | Non-uniform byte distribution |
| Autocorrelation | \|r(k)\| < 0.05 for lags 1, 8, 16, 32 | Linear dependence between successive values |
| Kolmogorov-Smirnov (KS) | D < 1.36/√n | Deviation from uniform CDF |

---

## Pedagogical Attacks

### LCG Seed Recovery — `ATTACKS/lcg_seed_recovery.py`

Three methods demonstrating why LCG must never be used in cryptography:

1. **Algebraic recovery** — recovers seed X₀ from a single output using modular inverse: `X₀ = (X₁ - c) × a⁻¹ mod m`. Complexity: O(log m).
2. **Brute force** — exhaustive search over small seed spaces (timestamp, PID, counter). Complexity: O(seed_max).
3. **Known-plaintext** — recovers the LCG keystream from a known (plaintext, ciphertext) pair when LCG is used as an XOR stream cipher.

### MT19937 State Reconstruction — `ATTACKS/mt19937_state_recovery.py`

Demonstrates that MT19937 is fully predictable after observing 624 consecutive 32-bit outputs:

1. **Tempering inversion** — each of the 4 tempering operations is inverted bit-by-bit (`untemper`)
2. **State recovery** — applying `untemper` to 624 outputs reconstructs the full 624-word internal state
3. **Future prediction** — applying `twist` then `temper` on the recovered state predicts all subsequent outputs with 100% accuracy

---

## Project Structure

```
Random_Number_Generator/
│
├── GENERATORS/
│   ├── PRNG_non_cryptographics/
│   │   ├── lcg.py                   # Linear Congruential Generator
│   │   └── mersenne_twister.py      # MT19937
│   ├── PRNG_Gaussian_distribution/
│   │   └── box_muller.py            # Box-Muller transform
│   ├── CSPRNG/
│   │   ├── bbs.py                   # Blum-Blum-Shub
│   │   ├── hash_drbg.py             # Hash_DRBG (NIST SP 800-90A / SHA-256)
│   │   └── os_random.py             # os.urandom wrapper
│   └── Non_deterministic_and_hybrid_generators/
│       └── xor_nrbg.py              # XOR NRBG
│
├── STATISTICS/
│   └── test_statistique.py          # Shannon, Chi², Autocorrelation, KS
│
├── ATTACKS/
│   ├── lcg_seed_recovery.py         # LCG: algebraic, brute force, known-plaintext
│   └── mt19937_state_recovery.py    # MT19937: state reconstruction & prediction
│
├── RES/                             # Generated figures (visualisations.py output)
├── screens/                         # Assets (logo)
│
├── run_all_tests.py                 # Runs all generators + statistical tests + attacks
├── visualisations.py                # Generates all plots and saves them to RES/
│
└── Projet_GNAs_25_26.pdf            # Project specifications
```

---

## Installation and Usage

### Requirements

```bash
# Python 3.8 or higher
pip install matplotlib
```

No external dependencies beyond the standard library and matplotlib.

### Run All Tests

Verifies all generators, statistical tests and attacks:

```bash
python run_all_tests.py
```

Expected output:

```
[OK] All generators working
[OK] All statistical tests working
[OK] All attacks working
[SUCCESS] Project complete and functional
```

### Generate Plots

Produces all figures and saves them to `RES/`:

```bash
python visualisations.py
```

Figures generated:
- `plot_distributions.png` — byte frequency distribution per generator
- `plot_entropie_glissante.png` — sliding Shannon entropy
- `plot_autocorrelation.png` — autocorrelation coefficients for lags 1–32
- `plot_ks.png` — empirical CDF vs. uniform theoretical CDF
- `plot_lcg_attack.png` — LCG attack: predicted vs. real outputs
- `plot_mt19937_attack.png` — MT19937 attack: reconstruction threshold
- `plot_comparatif_generateurs.png` — Shannon entropy comparison across all generators

### Run a Specific Generator

```bash
python GENERATORS/PRNG_non_cryptographics/lcg.py
python GENERATORS/PRNG_non_cryptographics/mersenne_twister.py
python GENERATORS/CSPRNG/hash_drbg.py
python GENERATORS/CSPRNG/bbs.py
python GENERATORS/CSPRNG/os_random.py
python GENERATORS/PRNG_Gaussian_distribution/box_muller.py
python GENERATORS/Non_deterministic_and_hybrid_generators/xor_nrbg.py
```

### Run Statistical Tests

```bash
python STATISTICS/test_statistique.py
```

### Run Pedagogical Attacks

```bash
# For educational purposes only
python ATTACKS/lcg_seed_recovery.py
python ATTACKS/mt19937_state_recovery.py
```

---

## References

1. Knuth, D. E. (1997). *The Art of Computer Programming, Volume 2: Seminumerical Algorithms*. Addison-Wesley.

2. Matsumoto, M., & Nishimura, T. (1998). Mersenne twister: A 623-dimensionally equidistributed uniform pseudo-random number generator. *ACM Transactions on Modeling and Computer Simulation*, 8(1), 3–30.

3. Marsaglia, G. (1968). Random numbers fall mainly in the planes. *Proceedings of the National Academy of Sciences*, 61(1), 25–28.

4. National Institute of Standards and Technology. (2015). *NIST SP 800-90A Rev. 1: Recommendation for random number generation using deterministic random bit generators*. U.S. Department of Commerce.

5. Kolmogorov, A. N. (1933). Sulla determinazione empirica di una legge di distribuzione. *Giornale dell'Istituto Italiano degli Attuari*, 4, 83–91.

6. Blum, L., Blum, M., & Shub, M. (1986). A simple unpredictable pseudo-random number generator. *SIAM Journal on Computing*, 15(2), 364–383.

---