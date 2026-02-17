"""
Tests statistiques pour evaluer la qualite des generateurs de nombres aleatoires.

4 tests implementes :
    1. Entropie de Shannon par octet
    2. Test du chi-carre (X²) pour l'uniformite des octets
    3. Autocorrelation (lags 1, 8, 16, 32)
    4. Test de Kolmogorov-Smirnov (KS)

Aucune dependance externe (pas de scipy, numpy).
"""

import math
from collections import Counter


# ─────────────────────────────────────────────────────────────────────────────
# 1. Entropie de Shannon
#    https://fr.wikipedia.org/wiki/Entropie_de_Shannon
#
#    H = - somme( p_i * log2(p_i) )
#
#    Pour des octets (256 symboles possibles) :
#        H_max = log2(256) = 8 bits/octet
#        H = 8   → parfaitement aleatoire
#        H < 8   → presence de motifs, predictibilite
# ─────────────────────────────────────────────────────────────────────────────

def shannon_entropy(data):
    """
    Calcule l'entropie de Shannon en bits par octet.

    Parametres:
        data : bytes, bytearray ou liste d'entiers [0-255]

    Retourne:
        float : entropie en bits/octet (entre 0 et 8)
    """
    if isinstance(data, (bytes, bytearray)):
        data = list(data)

    n = len(data)
    if n == 0:
        return 0.0

    freq = Counter(data)
    entropy = 0.0
    for count in freq.values():
        p = count / n
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def test_shannon(data):
    """
    Test d'entropie de Shannon.

    PASS si H > 7.9 bits/octet (seuil classique pour donnees aleatoires).

    Retourne:
        dict avec 'entropy', 'max_entropy', 'percentage', 'status'
    """
    H = shannon_entropy(data)
    H_max = 8.0

    return {
        "entropy": H,
        "max_entropy": H_max,
        "percentage": (H / H_max) * 100,
        "status": "PASS" if H > 7.9 else "FAIL",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Test du chi-carre (X²)
#    https://fr.wikipedia.org/wiki/Test_du_χ²
#
#    On teste H0 : "les 256 valeurs d'octets sont equiprobables"
#
#    X² = somme( (O_i - E_i)² / E_i )
#
#    avec O_i = occurrences observees, E_i = n / 256 (attendu uniforme)
#    Degres de liberte : df = 256 - 1 = 255
#    Valeur critique a alpha=0.05 : X²_crit ≈ 293.25
#
#    Si X² < X²_crit → on ne rejette pas H0 (distribution uniforme plausible)
#    Si X² > X²_crit → on rejette H0 (biais detecte)
# ─────────────────────────────────────────────────────────────────────────────

def chi_squared(data):
    """
    Calcule la statistique X² pour l'uniformite des octets.

    Parametres:
        data : bytes, bytearray ou liste d'entiers [0-255]

    Retourne:
        float : valeur de X²
    """
    if isinstance(data, (bytes, bytearray)):
        data = list(data)

    n = len(data)
    if n == 0:
        return 0.0

    freq = Counter(data)
    expected = n / 256

    chi2 = 0.0
    for i in range(256):
        observed = freq.get(i, 0)
        chi2 += ((observed - expected) ** 2) / expected

    return chi2


def test_chi_squared(data, alpha=0.05):
    """
    Test du chi-carre pour uniformite des octets.

    Parametres:
        data  : bytes, bytearray ou liste d'entiers [0-255]
        alpha : seuil de signification (defaut 0.05)

    Retourne:
        dict avec 'chi2', 'df', 'critical_value', 'p_approx', 'status'
    """
    chi2 = chi_squared(data)
    df = 255
    critical_value = 293.25  # X²_crit pour df=255, alpha=0.05

    return {
        "chi2": chi2,
        "df": df,
        "critical_value": critical_value,
        "p_approx": "< 0.05" if chi2 > critical_value else "> 0.05",
        "status": "PASS" if chi2 < critical_value else "FAIL",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Autocorrelation
#    https://fr.wikipedia.org/wiki/Autocorrélation
#
#    r(k) = Cov(X_i, X_{i+k}) / Var(X)
#
#    Pour un generateur ideal : r(k) ≈ 0 pour tout k > 0
#    Seuil de significativite a 95% : |r(k)| < 2 / sqrt(n)
#    Seuil pratique utilise ici : |r(k)| < 0.05
# ─────────────────────────────────────────────────────────────────────────────

def autocorrelation(data, lag=1):
    """
    Calcule le coefficient d'autocorrelation pour un decalage k.

    r(k) = [ sum (X_i - mu)(X_{i+k} - mu) ] / [ sum (X_i - mu)² ]

    Parametres:
        data : liste de valeurs numeriques
        lag  : decalage k (1 = valeurs consecutives)

    Retourne:
        float : coefficient r(k) dans [-1, 1]
    """
    if isinstance(data, (bytes, bytearray)):
        data = list(data)

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
    """
    Test d'autocorrelation pour plusieurs decalages.

    PASS si |r(k)| < 0.05 pour chaque lag.

    Parametres:
        data : bytes, bytearray ou liste d'entiers
        lags : tuple de decalages a tester

    Retourne:
        dict par lag, chacun avec 'coefficient' et 'status'
    """
    if isinstance(data, (bytes, bytearray)):
        data = list(data)

    seuil = 0.05
    results = {}

    for lag in lags:
        r = autocorrelation(data, lag)
        results[f"lag_{lag}"] = {
            "coefficient": r,
            "status": "PASS" if abs(r) < seuil else "FAIL",
        }

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 4. Test de Kolmogorov-Smirnov (KS)
#    https://fr.wikipedia.org/wiki/Test_de_Kolmogorov-Smirnov
#
#    Compare la CDF empirique F_n(x) a la CDF theorique F(x) = x (uniforme)
#
#    D_n = max | F_n(x_i) - F(x_i) |
#
#    avec F_n(x_i) = i/n  et  F(x_i) = x_i  (apres normalisation dans [0,1])
#
#    Valeur critique pour alpha=0.05 :  D_crit = 1.36 / sqrt(n)
#    (approximation valide pour n > 35)
#
#    Si D_n < D_crit → PASS (distribution uniforme plausible)
#    Si D_n > D_crit → FAIL (ecart significatif)
# ─────────────────────────────────────────────────────────────────────────────

def kolmogorov_smirnov(data):
    """
    Calcule la statistique D de Kolmogorov-Smirnov.

    Compare la distribution empirique des octets a la loi uniforme discrete
    sur {0, 1, ..., 255}.

    CDF theorique discrete : F(k) = (k + 1) / 256
    (et non F(x) = x qui suppose une uniforme continue)

    Parametres:
        data : bytes, bytearray ou liste d'entiers [0-255]

    Retourne:
        float : statistique D (distance maximale)
    """
    if isinstance(data, (bytes, bytearray)):
        data = list(data)

    n = len(data)
    if n == 0:
        return 0.0

    sorted_data = sorted(data)

    D = 0.0
    for i, value in enumerate(sorted_data):
        F_n = (i + 1) / n            # CDF empirique
        F = (value + 1) / 256        # CDF theorique uniforme discrete
        D = max(D, abs(F_n - F))

    return D


def test_kolmogorov_smirnov(data):
    """
    Test de Kolmogorov-Smirnov pour uniformite des octets.

    Parametres:
        data : bytes, bytearray ou liste d'entiers [0-255]

    Retourne:
        dict avec 'D', 'critical_value', 'n', 'status'
    """
    if isinstance(data, (bytes, bytearray)):
        data = list(data)

    n = len(data)
    if n == 0:
        return {"D": 0.0, "critical_value": 0.0, "n": 0, "status": "FAIL"}

    D = kolmogorov_smirnov(data)
    D_crit = 1.36 / math.sqrt(n)

    return {
        "D": D,
        "critical_value": D_crit,
        "n": n,
        "status": "PASS" if D < D_crit else "FAIL",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rapport complet
# ─────────────────────────────────────────────────────────────────────────────

def run_all_tests(data):
    """
    Execute les 4 tests sur un jeu de donnees.

    Parametres:
        data : bytes, bytearray ou liste d'entiers [0-255]

    Retourne:
        dict avec les resultats de chaque test + verdict global
    """
    if isinstance(data, (bytes, bytearray)):
        data = list(data)

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

    res["verdict"] = {
        "passed": passed,
        "total": 4,
        "status": "PASS" if passed >= 3 else "FAIL",
    }

    return res


def print_report(res):
    """Affiche un rapport lisible des resultats."""

    print(f"Taille echantillon : {res['n']} octets\n")

    # Shannon
    s = res["shannon"]
    print("1. ENTROPIE DE SHANNON")
    print(f"   H = {s['entropy']:.4f} bits/octet  (max = {s['max_entropy']:.1f})")
    print(f"   {s['percentage']:.2f}% du maximum")
    print(f"   → {s['status']}\n")

    # Chi2
    c = res["chi2"]
    print("2. TEST DU CHI-CARRE")
    print(f"   X² = {c['chi2']:.2f}  (critique = {c['critical_value']:.2f}, df = {c['df']})")
    print(f"   p {c['p_approx']}")
    print(f"   → {c['status']}\n")

    # Autocorrelation
    print("3. AUTOCORRELATION")
    for name, r in res["autocorrelation"].items():
        lag_num = name.split("_")[1]
        print(f"   lag {lag_num:>2} : r = {r['coefficient']:+.6f}  [{r['status']}]")
    print()

    # KS
    k = res["ks"]
    print("4. TEST DE KOLMOGOROV-SMIRNOV")
    print(f"   D = {k['D']:.6f}  (critique = {k['critical_value']:.6f})")
    print(f"   → {k['status']}\n")

    # Verdict
    v = res["verdict"]
    print(f"VERDICT : {v['passed']}/{v['total']} tests reussis → {v['status']}")
    print("-" * 50)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os

    print("=== Test 1 : os.urandom (reference) ===\n")
    res1 = run_all_tests(os.urandom(10_000))
    print_report(res1)

    print("\n=== Test 2 : donnees biaisees (motif 0,1,2 repete) ===\n")
    res2 = run_all_tests(bytes([0, 1, 2] * 1000))
    print_report(res2)

    print("\n=== Test 3 : donnees constantes (0x42) ===\n")
    res3 = run_all_tests(bytes([0x42] * 1000))
    print_report(res3)
