"""
Tests statistiques pour evaluer la qualite des generateurs de nombres aleatoires.

4 tests : Shannon, Chi-carre, Autocorrelation, Kolmogorov-Smirnov.
Aucune dependance externe (pas de scipy, numpy).
"""

import math
from collections import Counter


def _to_list(data):
    """Convertit bytes/bytearray en liste d'entiers."""
    return list(data) if isinstance(data, (bytes, bytearray)) else data


# --- 1. Entropie de Shannon ---
# H = -sum(p_i * log2(p_i)), H_max = 8 bits/octet pour 256 symboles

def shannon_entropy(data):
    """Entropie de Shannon en bits/octet (0 a 8)."""
    data = _to_list(data)
    n = len(data)
    if n == 0:
        return 0.0
    freq = Counter(data)
    return -sum((c / n) * math.log2(c / n) for c in freq.values() if c > 0)


def test_shannon(data):
    """PASS si H > 7.9 bits/octet."""
    H = shannon_entropy(data)
    return {
        "entropy": H, "max_entropy": 8.0,
        "percentage": (H / 8.0) * 100,
        "status": "PASS" if H > 7.9 else "FAIL",
    }


# --- 2. Chi-carre ---
# X2 = sum((O_i - E_i)^2 / E_i), df=255, seuil alpha=0.05 : 293.25

def chi_squared(data):
    """Statistique X2 pour uniformite des octets."""
    data = _to_list(data)
    n = len(data)
    if n == 0:
        return 0.0
    freq = Counter(data)
    expected = n / 256
    return sum(((freq.get(i, 0) - expected) ** 2) / expected for i in range(256))


def test_chi_squared(data):
    """PASS si X2 < 293.25 (alpha=0.05, df=255)."""
    chi2 = chi_squared(data)
    return {
        "chi2": chi2, "df": 255, "critical_value": 293.25,
        "p_approx": "< 0.05" if chi2 > 293.25 else "> 0.05",
        "status": "PASS" if chi2 < 293.25 else "FAIL",
    }


# --- 3. Autocorrelation ---
# r(k) = Cov(X_i, X_{i+k}) / Var(X), ideal : r(k) ~ 0

def autocorrelation(data, lag=1):
    """Coefficient d'autocorrelation r(k) dans [-1, 1]."""
    data = _to_list(data)
    n = len(data)
    if n < lag + 1:
        return 0.0
    mu = sum(data) / n
    variance = sum((x - mu) ** 2 for x in data)
    if variance == 0:
        return 0.0
    covariance = sum((data[i] - mu) * (data[i + lag] - mu) for i in range(n - lag))
    return covariance / variance


def test_autocorrelation(data, lags=(1, 8, 16, 32)):
    """PASS si |r(k)| < 0.05 pour chaque lag."""
    data = _to_list(data)
    return {
        f"lag_{lag}": {
            "coefficient": (r := autocorrelation(data, lag)),
            "status": "PASS" if abs(r) < 0.05 else "FAIL",
        }
        for lag in lags
    }


# --- 4. Kolmogorov-Smirnov (discret) ---
# D = max|F_n(k) - F(k)| aux 256 points, F(k) = (k+1)/256

def kolmogorov_smirnov(data):
    """Statistique D de KS pour octets vs uniforme discrete."""
    data = _to_list(data)
    n = len(data)
    if n == 0:
        return 0.0
    freq = Counter(data)
    D, cumul = 0.0, 0
    for k in range(256):
        cumul += freq.get(k, 0)
        D = max(D, abs(cumul / n - (k + 1) / 256))
    return D


def test_kolmogorov_smirnov(data):
    """PASS si D < 1.36/sqrt(n)."""
    data = _to_list(data)
    n = len(data)
    if n == 0:
        return {"D": 0.0, "critical_value": 0.0, "n": 0, "status": "FAIL"}
    D = kolmogorov_smirnov(data)
    D_crit = 1.36 / math.sqrt(n)
    return {
        "D": D, "critical_value": D_crit, "n": n,
        "status": "PASS" if D < D_crit else "FAIL",
    }


# --- Rapport complet ---

def run_all_tests(data):
    """Execute les 4 tests, retourne dict avec resultats + verdict."""
    data = _to_list(data)
    res = {
        "n": len(data),
        "shannon": test_shannon(data),
        "chi2": test_chi_squared(data),
        "autocorrelation": test_autocorrelation(data),
        "ks": test_kolmogorov_smirnov(data),
    }
    ac_pass = all(v["status"] == "PASS" for v in res["autocorrelation"].values())
    passed = sum([
        res["shannon"]["status"] == "PASS",
        res["chi2"]["status"] == "PASS",
        ac_pass,
        res["ks"]["status"] == "PASS",
    ])
    res["verdict"] = {"passed": passed, "total": 4,
                      "status": "PASS" if passed >= 3 else "FAIL"}
    return res


def print_report(res):
    """Affiche un rapport lisible."""
    s, c, k, v = res["shannon"], res["chi2"], res["ks"], res["verdict"]
    print(f"Taille echantillon : {res['n']} octets\n")
    print(f"1. SHANNON    H = {s['entropy']:.4f} bits/octet ({s['percentage']:.2f}%)  -> {s['status']}")
    print(f"2. CHI-CARRE  X2 = {c['chi2']:.2f} (critique={c['critical_value']:.2f})  -> {c['status']}")
    print("3. AUTOCORRELATION")
    for name, r in res["autocorrelation"].items():
        print(f"   {name} : r = {r['coefficient']:+.6f}  [{r['status']}]")
    print(f"4. KS         D = {k['D']:.6f} (critique={k['critical_value']:.6f})  -> {k['status']}")
    print(f"\nVERDICT : {v['passed']}/{v['total']} -> {v['status']}")
    print("-" * 50)


# --- Visualisations ---

def _make_grid(n_gen):
    """Cree une grille de subplots adaptee au nombre de generateurs."""
    import matplotlib.pyplot as plt
    n_cols = 3
    n_rows = (n_gen + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5 * n_rows))
    if n_rows == 1:
        axes = [axes] if n_gen == 1 else list(axes)
    else:
        axes = axes.flatten()
    return fig, axes


def plot_all_tests(data_dict, output_dir="."):
    """Genere 4 figures PNG (une par test) pour tous les generateurs."""
    import matplotlib.pyplot as plt
    import os

    names = list(data_dict.keys())
    all_data = {n: _to_list(d) for n, d in data_dict.items()}
    all_results = {n: run_all_tests(d) for n, d in all_data.items()}

    def _hide_unused(axes, n_used):
        for i in range(n_used, len(axes)):
            axes[i].set_visible(False)

    def _save(filename):
        plt.tight_layout()
        path = os.path.join(output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  -> {path}")

    # 1. Shannon : distribution des frequences d'octets
    fig, axes = _make_grid(len(names))
    for idx, name in enumerate(names):
        ax, d = axes[idx], all_data[name]
        freq = Counter(d)
        ax.bar(range(256), [freq.get(k, 0) for k in range(256)],
               color=f"C{idx}", alpha=0.7, width=1.0)
        ax.axhline(y=len(d) / 256, color="red", ls="--", lw=1.5,
                    label=f"Attendu ({len(d) / 256:.0f})")
        H = all_results[name]["shannon"]
        color = "green" if H["status"] == "PASS" else "red"
        ax.set_title(f"{name}\nH = {H['entropy']:.4f} bits/octet  [{H['status']}]",
                     fontsize=10, fontweight="bold", color=color)
        ax.set_xlabel("Valeur octet")
        ax.set_ylabel("Frequence")
        ax.set_xlim(0, 255)
        ax.legend(fontsize=8)
    _hide_unused(axes, len(names))
    plt.suptitle("Test 1 : Entropie de Shannon", fontsize=14, fontweight="bold")
    _save("shannon_entropy.png")

    # 2. Chi-carre : barres comparatives
    fig, ax = plt.subplots(figsize=(12, 6))
    vals = [all_results[n]["chi2"]["chi2"] for n in names]
    colors = ["green" if v < 293.25 else "red" for v in vals]
    bars = ax.bar(names, vals, color=colors, alpha=0.8, edgecolor="black")
    ax.axhline(y=293.25, color="red", ls="--", lw=1.5, label="Seuil critique (293.25)")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f"{val:.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Statistique X2")
    ax.set_title("Test 2 : Chi-carre (uniformite des octets)", fontweight="bold")
    ax.legend()
    plt.xticks(rotation=15, ha="right")
    _save("chi_squared.png")

    # 3. Autocorrelation : coefficients par lag
    lags = list(range(1, 33))
    fig, axes = _make_grid(len(names))
    for idx, name in enumerate(names):
        ax, d = axes[idx], all_data[name]
        coeffs = [autocorrelation(d, lag=k) for k in lags]
        seuil = 2 / math.sqrt(len(d))
        ax.bar(lags, coeffs, color=f"C{idx}", alpha=0.7)
        ax.axhline(y=+seuil, color="red", ls="--", lw=1, label=f"seuil +/-{seuil:.4f}")
        ax.axhline(y=-seuil, color="red", ls="--", lw=1)
        ax.axhline(y=0, color="black", lw=0.5)
        ax.set_title(name, fontweight="bold")
        ax.set_xlabel("Lag k")
        ax.set_ylabel("r(k)")
        ax.legend(fontsize=8)
    _hide_unused(axes, len(names))
    plt.suptitle("Test 3 : Autocorrelation par lag", fontsize=14, fontweight="bold")
    _save("autocorrelation.png")

    # 4. KS : CDF empirique vs theorique
    fig, axes = _make_grid(len(names))
    theo_y = [(k + 1) / 256 for k in range(256)]
    for idx, name in enumerate(names):
        ax, d = axes[idx], all_data[name]
        freq, n = Counter(d), len(d)
        ecdf_y, cumul = [], 0
        for k in range(256):
            cumul += freq.get(k, 0)
            ecdf_y.append(cumul / n)
        ax.step(range(256), theo_y, "r-", lw=2, where="post", label="$F(k)=(k+1)/256$")
        ax.step(range(256), ecdf_y, color=f"C{idx}", lw=1.5, where="post", label="$F_n(k)$ empirique")
        ks = all_results[name]["ks"]
        color = "green" if ks["status"] == "PASS" else "red"
        ax.set_title(f"{name}\nD={ks['D']:.6f} (seuil={ks['critical_value']:.6f}) [{ks['status']}]",
                     fontsize=10, fontweight="bold", color=color)
        ax.set_xlabel("Valeur octet k")
        ax.set_ylabel("Probabilite cumulee")
        ax.legend(fontsize=8, loc="lower right")
        ax.set_xlim(0, 255)
        ax.set_ylim(0, 1)
    _hide_unused(axes, len(names))
    plt.suptitle("Test 4 : Kolmogorov-Smirnov", fontsize=14, fontweight="bold")
    _save("kolmogorov_smirnov.png")

    return all_results


# --- Main ---

if __name__ == "__main__":
    import sys, os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from GENERATORS.PRNG_non_cryptographics.lcg import lcg, PARAMS_GLIBC
    from GENERATORS.PRNG_non_cryptographics.mersenne_twister import generate as mt_generate
    from GENERATORS.CSPRNG.bbs import bbs_generate_bytes
    from GENERATORS.CSPRNG.hash_drbg import drbg_generate_bytes
    from GENERATORS.CSPRNG.os_random import os_generate_bytes
    from GENERATORS.Non_deterministic_and_hybrid_generators.xor_nrbg import xor_nrbg

    N, SEED = 100_000, 42
    a, c, m = PARAMS_GLIBC["a"], PARAMS_GLIBC["c"], PARAMS_GLIBC["m"]
    lcg_gen = lambda seed, n: lcg(seed, a, c, m, n)

    print("Generation des donnees...")
    data = {
        "LCG": bytes([x % 256 for x in lcg(SEED, a, c, m, N)]),
        "Mersenne Twister": bytes([x % 256 for x in mt_generate(SEED, N)]),
        "Hash_DRBG": drbg_generate_bytes(N, entropy=b"A" * 55, nonce=b"B" * 28),
        "Blum-Blum-Shub": bbs_generate_bytes(N, seed=12345),
        "os.urandom": os_generate_bytes(N),
        "XOR NRBG": bytes([x % 256 for x in xor_nrbg([lcg_gen, mt_generate], [SEED, SEED + 1], N)]),
    }

    # Tests + rapport
    results = {}
    for name, d in data.items():
        print(f"\n{'=' * 55}\n  {name}\n{'=' * 55}")
        results[name] = run_all_tests(d)
        print_report(results[name])

    # Tableau comparatif
    print(f"\n{'Generateur':<20} {'Shannon':>8} {'Chi2':>6} {'AC':>6} {'KS':>6} {'Score':>7}")
    print("-" * 58)
    for name, res in results.items():
        sh, c2, ks = res["shannon"]["status"], res["chi2"]["status"], res["ks"]["status"]
        ac = "PASS" if all(v["status"] == "PASS" for v in res["autocorrelation"].values()) else "FAIL"
        score = sum(s == "PASS" for s in [sh, c2, ac, ks])
        print(f"{name:<20} {sh:>8} {c2:>6} {ac:>6} {ks:>6} {score:>5}/4")

    # Courbes
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "figures"))
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nGeneration des courbes dans {output_dir}...")
    plot_all_tests(data, output_dir=output_dir)
    print("\nTermine.")
