# Implémentation des Générateurs de Nombres Aléatoires et Analyse de la Qualité

**Random Number Generators Implementation and Quality Analysis**

Engineering school project on the implementation of random number generators and quality analysis.

## Table of Contents
- [Context and Motivation](#context-and-motivation)
- [Project Objectives](#project-objectives)
- [Generators Implemented](#generators-implemented)
- [Testing Methods](#testing-methods)
- [Project Structure](#project-structure)
- [Installation and Usage](#installation-and-usage)
- [Deliverables](#deliverables)
- [References](#references)

## Context and Motivation

Randomness and the ability to produce random numbers are at the heart of computer security protocols. Random numbers are used to generate secret keys, nonces, initialization vectors (IVs), and CSRF tokens. Insecure generation would allow an attacker to infer or predict subsequent keys or tokens, thereby compromising the security of the system.

Even if robust theoretical constructions exist, they are sometimes poorly implemented, and when the quality of randomness is insufficient, the entire system becomes vulnerable.

## Project Objectives

The goal of this project is to:
- Implement several pseudorandom number generation (PRNG) methods in Python
- Evaluate their quality and uniformity
- Formulate practical recommendations for secure usage
- Demonstrate pedagogical attacks exploiting PRNG weaknesses
- Compare the robustness of studied generators

### Educational Objectives
- Implement different generators (PRNG and CSPRNG) in Python
- Implement a suite of statistical tests measuring quality and uniformity
- Perform pedagogical attack demonstrations exploiting PRNG weaknesses
- Compare the robustness of studied generators
- Produce commented code and a written report

**Important Notice**: All attacks implemented in this project are for educational purposes only and are strictly prohibited on real systems without authorization.

## Generators Implemented

### Non-Cryptographic PRNGs
- **Linear Congruential Generator (LCG)**: Simple and fast pseudorandom generator based on a recursive linear relation. Suffers from weak statistical properties and complete absence of cryptographic security.
- **Mersenne Twister (MT19937)**: Widely used generator offering excellent statistical properties, but unsuitable for cryptographic uses.

### Gaussian Distribution PRNGs
- **Box-Muller Transform**: Algorithm transforming two independent uniform random variables into variables following a normal distribution.

### Cryptographically Secure PRNGs (CSPRNG)
- **NIST SP 800-90A DRBG (Deterministic Random Bit Generators)**: Family of pseudorandom generators defined by the NIST SP 800-90A standard. These generators are designed for cryptographic applications and offer formal guarantees against prediction and backward security.
- **Blum-Blum-Shub (BBS)**: Generator based on number theory hypotheses, renowned for its theoretical security. *Modified version using three Blum primes* for thesis research.
- **System Generator (os.urandom)**: Interface provided by the operating system, relying on hardware and software entropy sources. Commonly used as a cryptographically secure generator in practice.

### Non-Deterministic and Hybrid Generators
- **XOR NRBG Construction (Non-Random Bit Generator)**: Hybrid generator combining multiple bit generators (or sources) via bit-by-bit XOR operation. This construction aims to improve robustness against partial failure of a randomness source.

## Testing Methods

### Statistical Tests
- **Shannon Entropy Estimation** per byte
- **Chi-square (χ²) Test** for byte uniformity
- **Autocorrelation** (lags 1, 8, ...)
- **Kolmogorov-Smirnov (KS) Test**

### Experiments and Attacks
At least two of the following pedagogical attacks/experiments:
- **LCG Seed Recovery**: Known-plaintext/keystream XOR demonstration - seed recovery via linear solving or exhaustive search on small seed spaces
- **MT19937 State Reconstruction**: Recovery of internal state from 624 32-bit outputs and prediction of future outputs
- **AES-CTR Nonce Reuse**: Demonstrating XOR message leakage when the same nonce/IV is reused
- **AES-CBC Predictable IV**: Example showing how a predictable or deterministic IV can lead to information leakage or facilitate message equality detection

## Project Structure

```
Random_Number_Generator/
├── README.md                 # This file
├── CSPRNG/                   # Cryptographically Secure PRNGs
│   ├── BBS.py                # Blum-Blum-Shub implementation
│   ├── BBS_doc_en.md         # BBS documentation (English)
│   ├── BBS_doc_fr.md         # BBS documentation (French)
│   └── DRBG.py               # NIST SP 800-90A DRBG
├── PRNG_non-cryptographics/  # Non-cryptographic PRNGs
│   ├── LCG.py                # Linear Congruential Generator
│   ├── MT19937.py            # MT19937 implementation
├── PRNG_Gaussin-distribution
│   └── box-muller.py          # Box-Muller transform
├── Tests/                    # Statistical tests
│   ├── entropy.py            # Shannon entropy estimation
│   ├── chi_square.py         # Chi-square test
│   ├── autocorrelation.py    # Autocorrelation test
│   └── kolmogorov_smirnov.py # KS test
├── Attacks/                  # Pedagogical attacks
│   ├── lcg_seed_recovery.py  # LCG seed recovery
│   ├── mt_state_recovery.py  # MT19937 state reconstruction
│   └── aes_attacks.py        # AES-CTR/CBC attacks
└── docs/                     # Documentation and reports
    └── Projet_GNAs_25_26.pdf # Project specifications
```

## Installation and Usage

### Requirements
```bash
# Python 3.8 or higher required
pip install numpy scipy matplotlib
```

### Running a Generator
```bash
# Example: Run Blum-Blum-Shub
python CSPRNG/BBS.py

# Example: Run LCG
python PRNG/LCG.py
```

### Running Tests
```bash
# Run statistical tests on generated sequences
python Tests/entropy.py
python Tests/chi_square.py
```

### Running Pedagogical Attacks
```bash
# For educational purposes only
python Attacks/lcg_seed_recovery.py
python Attacks/mt_state_recovery.py
```

## Deliverables

1. **Written Report** including:
   - Abstract and keywords
   - Responsibility note stating attacks are pedagogical and prohibited on real systems
   - Introduction and motivation
   - Algorithm descriptions and implementations
   - Statistical testing methodology
   - Attack protocols and results
   - Discussion and practical recommendations
   - Conclusion
   - Numbered references
   - Annexes with code listings and figures

2. **Git Repository** containing:
   - Python code
   - Jupyter notebooks
   - Results and figures
   - Documentation

3. **10-Minute Demonstration**

## Evaluation

- **Implementation, testing, code quality, and demonstration**: 80%
- **Written report**: 20%

## Project Organization

- **Duration**: 7 sessions
- **Team Size**: Maximum 3 students per group
- **Each team member must**:
  - Understand all parts of the project
  - Be able to answer questions about all stages and implementations
- **AI Usage**: Limited use authorized, but all usage must be properly cited

## References

1. Vergnaud, Damien. "L'aléatoire, clé de voûte de la sécurité informatique." *La Recherche*, n°549, juillet-août 2019, pp. 46-49. [Online](https://www.larecherche.fr)

2. Johnston, David. *Random Number Generators—Principles and Practices: A Guide for Engineers and Programmers*. De Gruyter, 2018. ISBN: 978-1501506062. [Online](https://www.degruyterbrill.com/document/doi/10.1515/9781501506062/html)

3. Bureaud, Thierry. "Cybersécurité et qualité des générateurs informatiques de nombres aléatoires." Projet E3, ESIEE Paris, 2019-2020. [Online](https://perso.esiee.fr/~bureaud/Unites/Pr302i/1920/ProjetsE3/e320vr01.pdf)

4. Blum, L., Blum, M., & Shub, M. (1986). "A Simple Unpredictable Pseudo-Random Number Generator." *SIAM Journal on Computing*.

5. NIST Special Publication 800-90A: "Recommendation for Random Number Generation Using Deterministic Random Bit Generators."

---

**Note**: This project is part of an engineering school curriculum focusing on cryptography and computer security. All implementations are for educational purposes.

**Date**: January 28, 2026
