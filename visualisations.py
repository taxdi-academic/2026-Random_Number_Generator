# visualisations.py
"""
Visualisations of RNG project results

Plots for:
    1. Statistical tests (distribution, entropy, autocorrelation, KS)
    2. LCG attack (prediction vs reality)
    3. MT19937 attack (state reconstruction)
    4. Comparison of all generators
"""

import os
import sys
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from collections import Counter

# Project module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from GENERATORS.PRNG_non_cryptographics.lcg        import lcg, PARAMS_GLIBC
from GENERATORS.PRNG_non_cryptographics.mersenne_twister import generate as mt_generate, N as MT_N
from GENERATORS.CSPRNG.bbs                         import bbs, SMALL_PRIMES
from GENERATORS.PRNG_Gaussian_distribution.box_muller import box_muller_series
from GENERATORS.CSPRNG.hash_drbg                   import drbg_generate_bytes
from GENERATORS.CSPRNG.os_random                   import os_generate_bytes
from GENERATORS.Non_deterministic_and_hybrid_generators.xor_nrbg import xor_nrbg

from STATISTICS.test_statistique import (
    shannon_entropy, autocorrelation, full_statistical_res
)

from ATTACKS.lcg_seed_recovery      import recover_seed_algebrique
from ATTACKS.mt19937_state_recovery import recover_state, predict_next


# =============================================================================
# Common helpers
# =============================================================================

RES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RES")
os.makedirs(RES_DIR, exist_ok=True)


def _save(fig, name):
    """Save to /RES + display"""
    fig.tight_layout()
    path = os.path.join(RES_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"  [OK] Saved: {path}")


# =============================================================================
# 1) STATISTICAL TESTS
# =============================================================================

def plot_distributions():
    """
    Byte distribution over 3 datasets
    Visually compares uniformity against expected value (dashed line)
    """
    print("\n1. Byte distribution")

    datasets = {
        "os.urandom (reference)" : list(os_generate_bytes(5000)),
        "Repeated pattern [0,1,2]": [i % 3 for i in range(5000)],
        "Constant 0x42"          : [0x42] * 5000,
    }

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=False)
    fig.suptitle("Byte distribution — comparison across 3 datasets", fontsize=13)

    for ax, (label, data) in zip(axes, datasets.items()):
        freq = Counter(data)
        x = list(range(256))
        y = [freq.get(i, 0) for i in x]

        n = len(data)
        expected = n / 256

        ax.bar(x, y, width=1.0, color='steelblue', alpha=0.7, label="Observed")
        ax.axhline(expected, color='red', linestyle='--', linewidth=1.5,
                   label=f"Expected ({expected:.0f})")

        H = shannon_entropy(data)
        ax.set_title(f"{label}\nH = {H:.3f} bits/byte", fontsize=10)
        ax.set_xlabel("Byte value [0-255]")
        ax.set_ylabel("Frequency")
        ax.legend(fontsize=8)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(64))

    _save(fig, "plot_distributions.png")


def plot_entropie_glissante():
    """
    Sliding Shannon entropy (256-byte window)
    Shows how entropy evolves along the sequence
    """
    print("\n2. Sliding entropy")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']

    sequences = {
        "LCG (glibc)" : [x % 256 for x in lcg(42, a, c, m, 2000)],
        "MT19937"     : [x % 256 for x in mt_generate(42, 2000)],
        "os.urandom"  : list(os_generate_bytes(2000)),
    }

    window = 256

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle(f"Sliding Shannon entropy (window = {window} bytes)", fontsize=13)

    colors = ['red', 'orange', 'green']

    for (label, data), color in zip(sequences.items(), colors):
        entropies = []
        positions = []

        for i in range(0, len(data) - window, 10):
            window_data = data[i:i + window]
            H = shannon_entropy(window_data)
            entropies.append(H)
            positions.append(i)

        ax.plot(positions, entropies, label=label, color=color, linewidth=1.8, alpha=0.9)

    ax.axhline(7.9, color='gray',  linestyle=':',  linewidth=1.2, label="PASS threshold (7.9)")
    ax.axhline(8.0, color='black', linestyle='--', linewidth=1.0, label="Theoretical maximum (8.0)")

    ax.set_xlabel("Position in sequence (bytes)")
    ax.set_ylabel("Entropy H (bits/byte)")
    ax.set_ylim(0, 8.5)
    ax.legend()
    ax.grid(True, alpha=0.3)

    _save(fig, "plot_entropie_glissante.png")


def plot_autocorrelation():
    """
    Autocorrelation coefficients for lags 1 to 32
    Highlights correlations in weak generators
    """
    print("\n3. Autocorrelation (lags 1..32)")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    lags = list(range(1, 33))

    sequences = {
        "LCG (glibc)" : [x % 256 for x in lcg(42, a, c, m, 5000)],
        "MT19937"     : [x % 256 for x in mt_generate(42, 5000)],
        "os.urandom"  : list(os_generate_bytes(5000)),
    }

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    fig.suptitle("Autocorrelation — coefficients r for lags 1 to 32", fontsize=13)

    for ax, (label, data) in zip(axes, sequences.items()):
        coeffs = [autocorrelation(data, lag) for lag in lags]

        bar_colors = ['green' if abs(r) < 0.05 else 'red' for r in coeffs]

        ax.bar(lags, coeffs, color=bar_colors, alpha=0.8, width=0.7)
        ax.axhline( 0.05, color='gray', linestyle='--', linewidth=1.0, label="Threshold ±0.05")
        ax.axhline(-0.05, color='gray', linestyle='--', linewidth=1.0)
        ax.axhline(0,     color='black', linewidth=0.8)

        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Lag")
        ax.set_ylabel("r" if ax == axes[0] else "")
        ax.set_ylim(-0.2, 0.2)
        ax.legend(fontsize=7)

    _save(fig, "plot_autocorrelation.png")


def plot_ks():
    """
    Empirical CDF vs theoretical uniform CDF (Kolmogorov-Smirnov test)
    D is the maximum distance between the two curves
    """
    print("\n4. Kolmogorov-Smirnov test — empirical vs theoretical CDF")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']

    datasets = {
        "LCG (glibc)"          : [x % 256 for x in lcg(42, a, c, m, 2000)],
        "os.urandom (CSPRNG)"  : list(os_generate_bytes(2000)),
        "Repeated pattern [0,1,2]": [i % 3 for i in range(2000)],
    }

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Empirical CDF vs theoretical uniform CDF (KS test)", fontsize=13)

    for ax, (label, data) in zip(axes, datasets.items()):
        n = len(data)
        normalized = sorted([x / 255.0 for x in data])

        x_emp = normalized
        y_emp = [(i + 1) / n for i in range(n)]

        x_theo = [0.0] + normalized + [1.0]
        y_theo = [0.0] + normalized + [1.0]

        # Compute D
        max_diff = 0.0
        for xe, ye in zip(x_emp, y_emp):
            max_diff = max(max_diff, abs(ye - xe))

        critical = 1.36 / math.sqrt(n)
        verdict  = "PASS" if max_diff < critical else "FAIL"
        color    = 'green' if verdict == "PASS" else 'red'

        ax.plot(x_emp,  y_emp,  color='steelblue', linewidth=1.5, label="Empirical CDF")
        ax.plot(x_theo, y_theo, color='red', linewidth=1.5,
                linestyle='--', label="Theoretical uniform CDF")

        ax.set_title(f"{label}\nD={max_diff:.4f} — {verdict}", fontsize=10, color=color)
        ax.set_xlabel("Normalized value [0,1]")
        ax.set_ylabel("Cumulative probability")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    _save(fig, "plot_ks.png")


# =============================================================================
# 2) LCG ATTACK
# =============================================================================

def plot_lcg_attack():
    """
    LCG attack: real vs predicted sequences (after seed recovery)
    Shows perfect prediction via algebraic resolution
    """
    print("\n5. LCG attack — prediction vs reality")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    secret_seed = 123456789
    n_pred = 50

    all_outputs = lcg(secret_seed, a, c, m, n_pred + 3)
    observed    = all_outputs[:3]
    future_real = all_outputs[3:3 + n_pred]

    recovered   = recover_seed_algebrique(observed[0], observed[1], observed[2], a, c, m)
    future_pred = lcg(recovered, a, c, m, n_pred + 3)[3:3 + n_pred]

    indices = list(range(n_pred))

    fig, axes = plt.subplots(2, 1, figsize=(14, 7))
    fig.suptitle(
        f"LCG Attack — Algebraic recovery\n"
        f"Secret seed: {secret_seed}  |  Recovered seed: {recovered}",
        fontsize=12
    )

    # Sub-figure 1: overlapping sequences
    ax = axes[0]
    match = sum(p == r for p, r in zip(future_pred, future_real))
    ax.plot(indices, future_real, 'o-', color='steelblue', linewidth=1.5,
            markersize=4, label="Real sequence (victim)", alpha=0.9)
    ax.plot(indices, future_pred, 'x--', color='red', linewidth=1.5,
            markersize=5, label="Predicted sequence (attacker)", alpha=0.9)
    ax.set_ylabel("LCG value")
    ax.set_title(f"Future outputs: real vs predicted ({match}/{n_pred} matches)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Sub-figure 2: residuals
    ax2 = axes[1]
    residuals = [r - p for r, p in zip(future_real, future_pred)]
    bar_colors = ['green' if r == 0 else 'red' for r in residuals]
    ax2.bar(indices, residuals, color=bar_colors, alpha=0.8, width=0.7)
    ax2.axhline(0, color='black', linewidth=1.0)
    ax2.set_xlabel("Output index")
    ax2.set_ylabel("Residual (real − predicted)")
    ax2.set_title("Residuals — 0 = perfect prediction")
    ax2.grid(True, alpha=0.3)

    _save(fig, "plot_lcg_attack.png")


# =============================================================================
# 3) MT19937 ATTACK
# =============================================================================

def plot_mt19937_attack():
    """
    MT19937 attack: real vs predicted outputs after state reconstruction
    Also shows the critical 624-observation threshold
    """
    print("\n6. MT19937 attack — state reconstruction")

    secret_seed = 987654321
    n_pred = 30

    all_outputs = mt_generate(secret_seed, MT_N + n_pred)
    observed    = all_outputs[:MT_N]
    future_real = all_outputs[MT_N:MT_N + n_pred]

    recovered_state = recover_state(observed)
    predicted = predict_next(recovered_state, MT_N, n_pred)

    indices = list(range(n_pred))
    match   = sum(1 for r, p in zip(future_real, predicted) if r == p)

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle(
        f"MT19937 Attack — State reconstruction\n"
        f"{MT_N} observations → perfect prediction",
        fontsize=12
    )

    # Sub-figure 1: real vs predicted scatter
    ax = axes[0]
    ax.scatter(indices, future_real, s=40, color='steelblue',
               label="Real (victim)", marker='o', zorder=3)
    ax.scatter(indices, predicted,   s=20, color='red',
               label="Predicted (attacker)", marker='x', linewidths=2, zorder=4)
    ax.set_title(f"Future outputs: {match}/{n_pred} correct predictions (100%)")
    ax.set_ylabel("MT19937 value (32 bits)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Sub-figure 2: critical observation threshold
    ax2 = axes[1]
    n_obs_list  = [100, 300, 500, 623, 624, 625]
    labels_obs  = [str(n) for n in n_obs_list]
    success     = [0, 0, 0, 0, 1, 1]
    bar_colors  = ['red' if s == 0 else 'green' for s in success]

    bars = ax2.bar(labels_obs, success, color=bar_colors, alpha=0.85, width=0.5)
    ax2.set_ylim(0, 1.4)
    ax2.set_xlabel("Number of observations")
    ax2.set_ylabel("Attack possible?")
    ax2.set_title(f"Critical threshold: {MT_N} outputs required for the attack")
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["No (FAIL)", "Yes (PASS)"])

    for bar, label in zip(bars, ["FAIL"]*4 + ["PASS"]*2):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.05,
                 label, ha='center', va='bottom', fontsize=9,
                 color='red' if label == "FAIL" else 'green')

    _save(fig, "plot_mt19937_attack.png")


# =============================================================================
# 4) ALL-GENERATORS COMPARISON
# =============================================================================

def plot_comparatif_generateurs():
    """
    Compares Shannon entropy across all generators
    Single view to position each generator
    """
    print("\n7. Entropy comparison — all generators")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    N_BYTES = 5000
    SEED = 42

    def mt_bytes(seed, n):
        return bytes([x % 256 for x in mt_generate(seed, n)])

    def lcg_bytes(seed, n):
        return bytes([x % 256 for x in lcg(seed, a, c, m, n)])

    def bbs_bytes(seed, n):
        bits = bbs(seed, SMALL_PRIMES['p'], SMALL_PRIMES['q'], n * 8)
        result = bytearray(n)
        for i in range(n):
            byte = 0
            for b in range(8):
                byte = (byte << 1) | bits[i * 8 + b]
            result[i] = byte
        return bytes(result)

    def xor_bytes_gen(seed, n):
        gen1 = lambda s, k: [x % 256 for x in lcg(s, a, c, m, k)]
        gen2 = lambda s, k: [x % 256 for x in mt_generate(s, k)]
        combined = xor_nrbg([gen1, gen2], [seed, seed + 1], n)
        return bytes([x % 256 for x in combined])

    def uniform_rng_for_bm(seed, n):
        return [x / m for x in lcg(seed, a, c, m, n)]

    generators = {
        "LCG (glibc)"    : lcg_bytes(SEED, N_BYTES),
        "MT19937"        : mt_bytes(SEED, N_BYTES),
        "Box-Muller"     : bytes([int(abs(z) * 32) % 256 for z in
                                  box_muller_series(uniform_rng_for_bm, SEED, N_BYTES)]),
        "Hash_DRBG"      : drbg_generate_bytes(N_BYTES),
        "BBS"            : bbs_bytes(SEED, N_BYTES),
        "os.urandom"     : os_generate_bytes(N_BYTES),
        "XOR NRBG"       : xor_bytes_gen(SEED, N_BYTES),
    }

    labels    = list(generators.keys())
    entropies = [shannon_entropy(list(data)) for data in generators.values()]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("Shannon entropy comparison — all generators", fontsize=13)

    bar_colors = ['green' if H > 7.9 else 'red' for H in entropies]
    bars = ax.barh(labels, entropies, color=bar_colors, alpha=0.85, height=0.5)

    ax.axvline(7.9, color='gray',  linestyle=':',  linewidth=1.5, label="PASS threshold (7.9)")
    ax.axvline(8.0, color='black', linestyle='--', linewidth=1.2, label="Maximum (8.0)")

    for bar, H in zip(bars, entropies):
        ax.text(bar.get_width() - 0.05, bar.get_y() + bar.get_height() / 2,
                f"{H:.4f}", va='center', ha='right', fontsize=9,
                color='white', fontweight='bold')

    ax.set_xlim(0, 8.3)
    ax.set_xlabel("Entropy H (bits/byte)")
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3, axis='x')

    _save(fig, "plot_comparatif_generateurs.png")


# =============================================================================
# ENTRY POINT
# =============================================================================

def run_all_plots():
    """Run all visualisations"""
    print("=" * 60)
    print("  VISUALISATIONS — RNG PROJECT")
    print("=" * 60)

    # 1. Statistical tests
    plot_distributions()
    plot_entropie_glissante()
    plot_autocorrelation()
    plot_ks()

    # 2. Attacks
    plot_lcg_attack()
    plot_mt19937_attack()

    # 3. Comparison
    plot_comparatif_generateurs()

    print("\n" + "=" * 60)
    print("  All figures have been generated.")
    print(f"  Directory: ./RES/")
    print("=" * 60)


if __name__ == "__main__":
    run_all_plots()
