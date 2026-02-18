# visualisations.py
"""
Visualisations des résultats du projet RNG

Courbes pour :
    1. Tests statistiques (distribution, entropie, autocorrélation, KS)
    2. Attaque LCG (prédiction vs réalité)
    3. Attaque MT19937 (reconstruction état)
    4. Comparatif de tous les générateurs
"""

import os
import sys
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from collections import Counter

# Import des modules du projet
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
# Helpers communs
# =============================================================================

RES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RES")
os.makedirs(RES_DIR, exist_ok=True)


def _sauvegarder(fig, nom):
    """Sauvegarde dans /res + affichage"""
    fig.tight_layout()
    chemin = os.path.join(RES_DIR, nom)
    fig.savefig(chemin, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"  [OK] Sauvegardé : {chemin}")


# =============================================================================
# 1) TESTS STATISTIQUES
# =============================================================================

def plot_distributions():
    """
    Distribution des octets sur 3 datasets
    Compare visuellement l'uniformité attendue (ligne pointillée)
    """
    print("\n1. Distribution des octets")

    datasets = {
        "os.urandom (référence)" : list(os_generate_bytes(5000)),
        "Motif répété [0,1,2]"   : [i % 3 for i in range(5000)],
        "Constante 0x42"         : [0x42] * 5000,
    }

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=False)
    fig.suptitle("Distribution des octets — comparaison 3 datasets", fontsize=13)

    for ax, (label, data) in zip(axes, datasets.items()):
        freq = Counter(data)
        x = list(range(256))
        y = [freq.get(i, 0) for i in x]

        n = len(data)
        attendu = n / 256

        ax.bar(x, y, width=1.0, color='steelblue', alpha=0.7, label="Observé")
        ax.axhline(attendu, color='red', linestyle='--', linewidth=1.5,
                   label=f"Attendu ({attendu:.0f})")

        H = shannon_entropy(data)
        ax.set_title(f"{label}\nH = {H:.3f} bits/octet", fontsize=10)
        ax.set_xlabel("Valeur octet [0-255]")
        ax.set_ylabel("Fréquence")
        ax.legend(fontsize=8)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(64))

    _sauvegarder(fig, "plot_distributions.png")


def plot_entropie_glissante():
    """
    Entropie de Shannon glissante (fenêtre de 256 octets)
    Montre comment l'entropie évolue au fil de la séquence
    """
    print("\n2. Entropie glissante")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']

    sequences = {
        "LCG (glibc)"  : [x % 256 for x in lcg(42, a, c, m, 2000)],
        "MT19937"      : [x % 256 for x in mt_generate(42, 2000)],
        "os.urandom"   : list(os_generate_bytes(2000)),
    }

    fenetre = 256

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle(f"Entropie de Shannon glissante (fenêtre = {fenetre} octets)", fontsize=13)

    couleurs = ['red', 'orange', 'green']

    for (label, data), couleur in zip(sequences.items(), couleurs):
        entropies = []
        positions = []

        for i in range(0, len(data) - fenetre, 10):
            fenetre_data = data[i:i + fenetre]
            H = shannon_entropy(fenetre_data)
            entropies.append(H)
            positions.append(i)

        ax.plot(positions, entropies, label=label, color=couleur, linewidth=1.8, alpha=0.9)

    ax.axhline(7.9, color='gray',  linestyle=':',  linewidth=1.2, label="Seuil PASS (7.9)")
    ax.axhline(8.0, color='black', linestyle='--', linewidth=1.0, label="Maximum théorique (8.0)")

    ax.set_xlabel("Position dans la séquence (octets)")
    ax.set_ylabel("Entropie H (bits/octet)")
    ax.set_ylim(0, 8.5)
    ax.legend()
    ax.grid(True, alpha=0.3)

    _sauvegarder(fig, "plot_entropie_glissante.png")


def plot_autocorrelation():
    """
    Coefficients d'autocorrélation pour lags 1 à 32
    Met en évidence les corrélations des générateurs faibles
    """
    print("\n3. Autocorrélation (lags 1..32)")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    lags = list(range(1, 33))

    sequences = {
        "LCG (glibc)"  : [x % 256 for x in lcg(42, a, c, m, 5000)],
        "MT19937"      : [x % 256 for x in mt_generate(42, 5000)],
        "os.urandom"   : list(os_generate_bytes(5000)),
    }

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    fig.suptitle("Autocorrélation — coefficients r pour lags 1 à 32", fontsize=13)

    for ax, (label, data) in zip(axes, sequences.items()):
        coeffs = [autocorrelation(data, lag) for lag in lags]

        bar_colors = ['green' if abs(r) < 0.05 else 'red' for r in coeffs]

        ax.bar(lags, coeffs, color=bar_colors, alpha=0.8, width=0.7)
        ax.axhline( 0.05, color='gray', linestyle='--', linewidth=1.0, label="Seuil ±0.05")
        ax.axhline(-0.05, color='gray', linestyle='--', linewidth=1.0)
        ax.axhline(0,     color='black', linewidth=0.8)

        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Lag")
        ax.set_ylabel("r" if ax == axes[0] else "")
        ax.set_ylim(-0.2, 0.2)
        ax.legend(fontsize=7)

    _sauvegarder(fig, "plot_autocorrelation.png")


def plot_ks():
    """
    CDF empirique vs CDF uniforme théorique (test de Kolmogorov-Smirnov)
    La statistique D est la distance maximale entre les deux courbes
    """
    print("\n4. Test Kolmogorov-Smirnov — CDF empirique vs théorique")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']

    datasets = {
        "LCG (glibc)"          : [x % 256 for x in lcg(42, a, c, m, 2000)],
        "os.urandom (CSPRNG)"  : list(os_generate_bytes(2000)),
        "Motif répété [0,1,2]" : [i % 3 for i in range(2000)],
    }

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("CDF empirique vs CDF uniforme théorique (test KS)", fontsize=13)

    for ax, (label, data) in zip(axes, datasets.items()):
        n = len(data)
        normalized = sorted([x / 255.0 for x in data])

        x_emp = normalized
        y_emp = [(i + 1) / n for i in range(n)]

        x_theo = [0.0] + normalized + [1.0]
        y_theo = [0.0] + normalized + [1.0]

        # Calcul de D
        max_diff = 0.0
        for xe, ye in zip(x_emp, y_emp):
            max_diff = max(max_diff, abs(ye - xe))

        critical = 1.36 / math.sqrt(n)
        verdict  = "PASS" if max_diff < critical else "FAIL"
        couleur  = 'green' if verdict == "PASS" else 'red'

        ax.plot(x_emp,  y_emp,  color='steelblue', linewidth=1.5, label="CDF empirique")
        ax.plot(x_theo, y_theo, color='red', linewidth=1.5,
                linestyle='--', label="CDF uniforme théorique")

        ax.set_title(f"{label}\nD={max_diff:.4f} — {verdict}", fontsize=10, color=couleur)
        ax.set_xlabel("Valeur normalisée [0,1]")
        ax.set_ylabel("Probabilité cumulée")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    _sauvegarder(fig, "plot_ks.png")


# =============================================================================
# 2) ATTAQUE LCG
# =============================================================================

def plot_lcg_attack():
    """
    Attaque LCG : séquences réelle vs prédite (après récupération graine)
    Montre la prédiction parfaite obtenue via résolution algébrique
    """
    print("\n5. Attaque LCG — prédiction vs réalité")

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
        f"Attaque LCG — Récupération algébrique\n"
        f"Graine secrète : {secret_seed}  |  Graine récupérée : {recovered}",
        fontsize=12
    )

    # Sous-figure 1 : séquences superposées
    ax = axes[0]
    match = sum(p == r for p, r in zip(future_pred, future_real))
    ax.plot(indices, future_real, 'o-', color='steelblue', linewidth=1.5,
            markersize=4, label="Séquence réelle (victime)", alpha=0.9)
    ax.plot(indices, future_pred, 'x--', color='red', linewidth=1.5,
            markersize=5, label="Séquence prédite (attaquant)", alpha=0.9)
    ax.set_ylabel("Valeur LCG")
    ax.set_title(f"Sorties futures : réelles vs prédites ({match}/{n_pred} correspondances)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Sous-figure 2 : résidus
    ax2 = axes[1]
    residus = [r - p for r, p in zip(future_real, future_pred)]
    bar_colors = ['green' if r == 0 else 'red' for r in residus]
    ax2.bar(indices, residus, color=bar_colors, alpha=0.8, width=0.7)
    ax2.axhline(0, color='black', linewidth=1.0)
    ax2.set_xlabel("Indice de sortie")
    ax2.set_ylabel("Résidu (réel − prédit)")
    ax2.set_title("Résidus — 0 = prédiction parfaite")
    ax2.grid(True, alpha=0.3)

    _sauvegarder(fig, "plot_lcg_attack.png")


# =============================================================================
# 3) ATTAQUE MT19937
# =============================================================================

def plot_mt19937_attack():
    """
    Attaque MT19937 : sorties réelles vs prédites après reconstruction état
    Montre aussi le seuil critique des 624 observations
    """
    print("\n6. Attaque MT19937 — reconstruction état")

    secret_seed = 987654321
    n_pred = 30

    all_outputs = mt_generate(secret_seed, MT_N + n_pred)
    observed    = all_outputs[:MT_N]
    future_real = all_outputs[MT_N:MT_N + n_pred]

    recovered_state = recover_state(observed)
    predicted       = predict_next(recovered_state, 0, n_pred)

    indices = list(range(n_pred))
    match   = sum(1 for r, p in zip(future_real, predicted) if r == p)

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle(
        f"Attaque MT19937 — Reconstruction état\n"
        f"{MT_N} observations → prédiction parfaite",
        fontsize=12
    )

    # Sous-figure 1 : scatter réel vs prédit
    ax = axes[0]
    ax.scatter(indices, future_real, s=40, color='steelblue',
               label="Réelles (victime)", marker='o', zorder=3)
    ax.scatter(indices, predicted,   s=20, color='red',
               label="Prédites (attaquant)", marker='x', linewidths=2, zorder=4)
    ax.set_title(f"Sorties futures : {match}/{n_pred} prédictions correctes (100%)")
    ax.set_ylabel("Valeur MT19937 (32 bits)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Sous-figure 2 : seuil critique d'observations
    ax2 = axes[1]
    n_obs_list  = [100, 300, 500, 623, 624, 625]
    labels_obs  = [str(n) for n in n_obs_list]
    succes      = [0, 0, 0, 0, 1, 1]
    bar_colors  = ['red' if s == 0 else 'green' for s in succes]

    bars = ax2.bar(labels_obs, succes, color=bar_colors, alpha=0.85, width=0.5)
    ax2.set_ylim(0, 1.4)
    ax2.set_xlabel("Nombre d'observations")
    ax2.set_ylabel("Attaque possible ?")
    ax2.set_title(f"Seuil critique : {MT_N} sorties nécessaires pour l'attaque")
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["Non (FAIL)", "Oui (PASS)"])

    for bar, label in zip(bars, ["FAIL"]*4 + ["PASS"]*2):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.05,
                 label, ha='center', va='bottom', fontsize=9,
                 color='red' if label == "FAIL" else 'green')

    _sauvegarder(fig, "plot_mt19937_attack.png")


# =============================================================================
# 4) COMPARATIF TOUS GÉNÉRATEURS
# =============================================================================

def plot_comparatif_generateurs():
    """
    Compare l'entropie de Shannon de tous les générateurs
    Un seul coup d'œil pour situer chaque générateur
    """
    print("\n7. Comparatif entropie — tous les générateurs")

    a, c, m = PARAMS_GLIBC['a'], PARAMS_GLIBC['c'], PARAMS_GLIBC['m']
    N_OCTETS = 5000
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

    generateurs = {
        "LCG (glibc)"    : lcg_bytes(SEED, N_OCTETS),
        "MT19937"        : mt_bytes(SEED, N_OCTETS),
        "Box-Muller"     : bytes([int(abs(z) * 32) % 256 for z in
                                  box_muller_series(uniform_rng_for_bm, SEED, N_OCTETS)]),
        "Hash_DRBG"      : drbg_generate_bytes(N_OCTETS),
        "BBS"            : bbs_bytes(SEED, N_OCTETS),
        "os.urandom"     : os_generate_bytes(N_OCTETS),
        "XOR NRBG"       : xor_bytes_gen(SEED, N_OCTETS),
    }

    labels    = list(generateurs.keys())
    entropies = [shannon_entropy(list(data)) for data in generateurs.values()]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("Entropie de Shannon comparée — tous les générateurs", fontsize=13)

    bar_colors = ['green' if H > 7.9 else 'red' for H in entropies]
    bars = ax.barh(labels, entropies, color=bar_colors, alpha=0.85, height=0.5)

    ax.axvline(7.9, color='gray',  linestyle=':',  linewidth=1.5, label="Seuil PASS (7.9)")
    ax.axvline(8.0, color='black', linestyle='--', linewidth=1.2, label="Maximum (8.0)")

    for bar, H in zip(bars, entropies):
        ax.text(bar.get_width() - 0.05, bar.get_y() + bar.get_height() / 2,
                f"{H:.4f}", va='center', ha='right', fontsize=9,
                color='white', fontweight='bold')

    ax.set_xlim(0, 8.3)
    ax.set_xlabel("Entropie H (bits/octet)")
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3, axis='x')

    _sauvegarder(fig, "plot_comparatif_generateurs.png")


# =============================================================================
# LANCEMENT
# =============================================================================

def run_all_plots():
    """Lance toutes les visualisations"""
    print("=" * 60)
    print("  VISUALISATIONS — PROJET RNG")
    print("=" * 60)

    # 1. Tests statistiques
    plot_distributions()
    plot_entropie_glissante()
    plot_autocorrelation()
    plot_ks()

    # 2. Attaques
    plot_lcg_attack()
    plot_mt19937_attack()

    # 3. Comparatif
    plot_comparatif_generateurs()

    print("\n" + "=" * 60)
    print("  Toutes les figures ont été générées.")
    print(f"  Dossier : ./res/")
    print("=" * 60)


if __name__ == "__main__":
    run_all_plots()
