# Generateurs de Nombres Pseudo-Aleatoires : Implementation, Tests et Attaques

## Introduction

Ce document presente l'etude de deux generateurs de nombres pseudo-aleatoires (PRNG), deux tests statistiques pour evaluer leur qualite, et deux attaques demontrant leurs faiblesses cryptographiques. L'objectif est de comprendre pourquoi ces PRNG, bien qu'utiles en simulation, sont **inadaptes a tout usage cryptographique**.

---

## 1. Generateurs

### 1.1 Linear Congruential Generator (LCG)

#### Principe

Le LCG est l'un des plus anciens et des plus simples PRNG. Il repose sur une relation de recurrence lineaire :

```
X_{n+1} = (a * X_n + c) mod m
```

ou :
- `X_0` est la **graine** (seed), valeur initiale secrete
- `a` est le **multiplicateur**
- `c` est l'**increment**
- `m` est le **module** (definit la periode maximale)

La suite est entierement deterministe : connaissant `X_0`, `a`, `c` et `m`, on peut reproduire toute la sequence.

#### Implementation

```python
def lcg(seed, a, c, m, n):
    x = seed
    results = []
    for _ in range(n):
        x = (a * x + c) % m
        results.append(x)
    return results
```

La fonction prend une graine, les parametres `(a, c, m)` et le nombre de valeurs `n` a generer. Elle retourne une liste d'entiers dans `[0, m-1]`.

#### Parametres standards

| Nom | a | c | m | Source |
|-----|---|---|---|--------|
| glibc | 1 103 515 245 | 12 345 | 2^31 | Bibliotheque standard C |
| RANDU | 65 539 | 0 | 2^31 | IBM (1960s, mauvais) |
| MMIX (Knuth) | 6 364 136 223 846 793 005 | 1 442 695 040 888 963 407 | 2^64 | The Art of Computer Programming |

#### Proprietes

- **Periode maximale** : `m` (atteinte si `pgcd(c, m) = 1`, `a - 1` divisible par tous les facteurs premiers de `m`, et `a - 1` divisible par 4 si `m` l'est)
- **Avantage** : extremement rapide (une multiplication, une addition, un modulo)
- **Faiblesse principale** : les valeurs successives sont correlees lineairement. Un scatter plot de `(X_n, X_{n+1})` revele des structures en hyperplans (theoreme de Marsaglia)

---

### 1.2 Mersenne Twister (MT19937)

#### Principe

Le Mersenne Twister est le PRNG le plus utilise dans les langages de programmation (`random` en Python, `rand()` en C++, etc.). Il est base sur une recurrence matricielle lineaire sur le corps `GF(2)` (corps de Galois a 2 elements).

Son nom vient du fait que sa periode est le nombre premier de Mersenne `2^19937 - 1`, soit environ `4.3 * 10^6001`.

L'algorithme se decompose en 3 phases :

1. **Initialisation** : a partir d'une graine de 32 bits, on construit un etat interne de 624 mots de 32 bits
2. **Twist** : transformation de l'etat qui melange les 624 valeurs entre elles
3. **Tempering** : transformation de sortie qui ameliore la distribution statistique

#### Implementation

**Constantes MT19937** :
```
W=32, N=624, M=397, R=31
A=0x9908B0DF, F=1812433253
U=11, D=0xFFFFFFFF, S=7, B=0x9D2C5680
T=15, C=0xEFC60000, L=18
```

**Initialisation** : Construction de l'etat a partir de la graine

```python
def init(seed):
    state = [seed & 0xFFFFFFFF]
    for i in range(1, N):
        prev = state[i - 1]
        state.append((F * (prev ^ (prev >> 30)) + i) & 0xFFFFFFFF)
    return state
```

Chaque valeur de l'etat depend de la precedente via une relation non-lineaire impliquant le facteur `F = 1812433253`.

**Twist** : Melange de l'etat interne

```python
def twist(state):
    for i in range(N):
        bit_haut = state[i] & 0x80000000        # bit 31
        bits_bas = state[(i + 1) % N] & 0x7FFFFFFF  # bits 0-30
        x = bit_haut | bits_bas
        x_shifted = x >> 1
        if x & 1:
            x_shifted ^= A
        state[i] = state[(i + M) % N] ^ x_shifted
    return state
```

Pour chaque position `i`, on combine le bit de poids fort de `state[i]` avec les 31 bits de poids faible de `state[i+1]`, puis on XOR le resultat avec `state[i+397]`. Si le bit de poids faible est 1, on applique en plus un XOR avec la matrice `A`.

**Tempering** : Amelioration de la distribution en sortie

```python
def temper(y):
    y ^= (y >> U) & D    # Decalage droite 11 bits, masque 0xFFFFFFFF
    y ^= (y << S) & B    # Decalage gauche 7 bits, masque 0x9D2C5680
    y ^= (y << T) & C    # Decalage gauche 15 bits, masque 0xEFC60000
    y ^= y >> L           # Decalage droite 18 bits
    return y & 0xFFFFFFFF
```

Le tempering est une suite d'operations XOR avec des decalages et des masques. Cette transformation est **inversible** (point crucial pour l'attaque, cf. section 3.2).

**Generation** :

```python
def generate(seed, n):
    state = init(seed)
    index = N
    results = []
    for _ in range(n):
        if index >= N:
            twist(state)
            index = 0
        results.append(temper(state[index]))
        index += 1
    return results
```

On parcourt l'etat sequentiellement. Toutes les 624 extractions, un twist regenere l'etat complet.

#### Proprietes

- **Periode** : `2^19937 - 1` (incomparablement plus longue que le LCG)
- **Equidistribution** : 623-distribuee sur 32 bits (excellentes proprietes statistiques)
- **Avantage** : passe la majorite des tests statistiques standards
- **Faiblesse principale** : l'etat interne est entierement reconstructible a partir de 624 sorties consecutives (cf. section 3.2)

---

## 2. Tests statistiques

### 2.1 Autocorrelation

#### Principe

L'autocorrelation mesure la dependance lineaire entre une sequence et une version decalee d'elle-meme. Pour un generateur ideal, les valeurs successives doivent etre **independantes**, donc le coefficient d'autocorrelation doit etre proche de 0 pour tout decalage (lag).

Le coefficient d'autocorrelation pour un decalage `k` est :

```
r(k) = Cov(X_i, X_{i+k}) / Var(X)
```

soit, en pratique :

```
r(k) = [ sum_{i=0}^{n-k-1} (X_i - mu)(X_{i+k} - mu) ] / [ sum_{i=0}^{n-1} (X_i - mu)^2 ]
```

ou `mu` est la moyenne empirique de la sequence.

#### Interpretation

| Valeur de r(k) | Interpretation |
|-----------------|---------------|
| r(k) ~ 0 | Pas de correlation (attendu pour un bon PRNG) |
| \|r(k)\| > seuil | Correlation detectee (defaut du generateur) |

Le seuil de significativite est generalement `+/- 2/sqrt(n)` pour un echantillon de taille `n` (intervalle de confiance a 95%).

#### Implementation

```python
def autocorrelation(data, lag=1):
    n = len(data) - lag
    moy = sum(data) / len(data)
    variance = sum((x - moy)**2 for x in data)
    if variance == 0:
        return 0.0
    covariance = sum((data[i] - moy) * (data[i + lag] - moy) for i in range(n))
    r = covariance / variance
    return r
```

On teste plusieurs decalages (lags 1, 8, 16, 32). Le test passe si `|r(k)| < 0.05` pour tous les lags.

#### Application aux generateurs

Le LCG presente des autocorrelations significatives pour les petits lags, ce qui confirme la correlation lineaire entre valeurs consecutives. Le Mersenne Twister, malgre ses bonnes proprietes statistiques apparentes, montre egalement des correlations detectables sur les octets de poids faible. Les CSPRNG (Hash_DRBG, os.urandom) restent dans les limites acceptables.

---

### 2.2 Test de Kolmogorov-Smirnov (KS)

#### Principe

Le test de Kolmogorov-Smirnov compare la **distribution empirique** des donnees a une distribution theorique de reference (ici, la distribution uniforme sur `[0, 255]`).

L'idee est de mesurer la distance maximale entre la fonction de repartition empirique `F_n(x)` et la fonction de repartition theorique `F(x)` :

```
D_n = max |F_n(x) - F(x)|
```

ou :
- `F_n(x) = (nombre de valeurs <= x) / n` (empirique)
- `F(x) = x / 255` (uniforme theorique sur [0, 255], normalisee dans [0, 1])

#### Hypotheses

- **H_0** : les donnees suivent la distribution uniforme
- **H_1** : les donnees ne suivent pas la distribution uniforme

On rejette H_0 si `D_n > D_critique`.

#### Valeur critique

Pour un niveau de signification `alpha = 0.05` et un echantillon de grande taille `n` :

```
D_critique = 1.36 / sqrt(n)
```

Cette approximation est valide pour `n > 35`. Pour `n = 100 000`, le seuil est `D_critique ~ 0.0043`.

#### Implementation

```python
def kolmogorov_smirnov_test(data):
    normalized = sorted([x / 255.0 for x in data])
    n = len(normalized)
    max_diff = 0.0
    for i, value in enumerate(normalized):
        empi = (i + 1) / n          # F_n(x)
        theo = value                 # F(x) = x (apres normalisation)
        diff = abs(empi - theo)
        max_diff = max(max_diff, diff)
    critical_value = 1.36 / math.sqrt(n)
    return {
        'D': max_diff,
        'critical_value': critical_value,
        'n': n,
        'status': 'PASS' if max_diff < critical_value else 'FAIL'
    }
```

#### Avantages du test KS

- **Non-parametrique** : ne suppose pas de forme particuliere pour la distribution
- **Sensible** : detecte aussi bien les ecarts de position que de forme
- **Pas de regroupement** : contrairement au chi-carre, travaille directement sur les valeurs individuelles

---

## 3. Attaques

### 3.1 Recuperation de la graine LCG

#### Modele de menace

L'attaquant observe quelques sorties consecutives du LCG et connait (ou devine) les parametres publics `(a, c, m)`. Son objectif est de retrouver la graine `X_0` pour predire toutes les sorties futures.

Trois methodes sont implementees :

#### Methode 1 : Resolution algebrique

C'est la methode la plus efficace. Sachant que :

```
X_1 = (a * X_0 + c) mod m
```

On inverse pour obtenir :

```
X_0 = (X_1 - c) * a^{-1} mod m
```

ou `a^{-1}` est l'inverse modulaire de `a` modulo `m`, calcule via `pow(a, -1, m)` (algorithme d'Euclide etendu, complexite `O(log m)`).

```python
def recover_seed_algebrique(x1, x2, x3, a, c, m):
    a_inv = pow(a, -1, m)
    x0 = ((x1 - c) * a_inv) % m
    return x0
```

**Resultat** : la graine est recuperee en une seule operation a partir de la premiere sortie observee. La prediction des sorties futures est alors parfaite a 100%.

#### Methode 2 : Force brute

Si l'espace des graines est restreint (ex: graine derivee d'un timestamp, d'un PID, ou d'un compteur), on peut tester toutes les graines possibles :

```python
def recover_seed_bruteforce(outputs, a, c, m, seed_max=1000000):
    for candidate in range(seed_max):
        generated = lcg(candidate, a, c, m, len(outputs))
        if generated == outputs:
            return candidate
    return None
```

**Complexite** : `O(seed_max * len(outputs))`. Pour un espace de 100 000 graines, l'attaque prend moins d'une seconde.

#### Methode 3 : Known-plaintext (chiffrement XOR)

Si le LCG est utilise comme generateur de flux pour un chiffrement XOR :

```
C = P xor LCG_keystream
```

et que l'attaquant connait un couple `(P, C)`, il recupere le keystream :

```
K = P xor C
```

puis recherche la graine par force brute sur les octets du keystream.

```python
def recover_seed_from_xor(plaintext, ciphertext, a, c, m, seed_max=100000):
    keystream = xor_bytes(plaintext, ciphertext)
    keystream_ints = list(keystream)
    for candidate in range(seed_max):
        generated = lcg(candidate, a, c, m, len(keystream))
        generated_bytes = [x % 256 for x in generated]
        if generated_bytes == keystream_ints:
            return candidate
    return None
```

#### Conclusion sur le LCG

Le LCG est **totalement compromis** des que l'attaquant observe une seule sortie (methode algebrique) ou quelques sorties (force brute). Il ne doit **jamais** etre utilise pour generer des cles, nonces, IV ou tout materiel cryptographique.

---

### 3.2 Reconstruction d'etat du Mersenne Twister (MT19937)

#### Modele de menace

L'attaquant observe **624 sorties consecutives** de 32 bits du Mersenne Twister. Son objectif est de reconstruire l'etat interne complet pour predire toutes les sorties futures.

#### Principe de l'attaque

L'attaque repose sur l'**inversion du tempering**. Chaque sortie du MT est :

```
sortie = temper(state[i])
```

Le tempering est une suite de 4 operations XOR avec decalages et masques :

```
y ^= (y >> 11) & 0xFFFFFFFF
y ^= (y <<  7) & 0x9D2C5680
y ^= (y << 15) & 0xEFC60000
y ^= y >> 18
```

Chacune de ces operations est **inversible** bit a bit.

#### Inversion du tempering

Pour inverser `y ^= (y >> shift)`, on reconstruit les bits de gauche a droite : les `shift` bits de poids fort ne sont pas modifies, et chaque bit suivant est retrouve en XOR avec le bit deja reconstruit `shift` positions plus haut :

```python
def invert_right_shift_xor(y, shift):
    result = 0
    for i in range(32):
        bit_pos = 31 - i
        if i < shift:
            bit = (y >> bit_pos) & 1
        else:
            prev_bit = (result >> (bit_pos + shift)) & 1
            current_bit = (y >> bit_pos) & 1
            bit = current_bit ^ prev_bit
        result |= (bit << bit_pos)
    return result
```

Pour inverser `y ^= (y << shift) & mask`, meme principe mais de droite a gauche, en tenant compte du masque :

```python
def invert_left_shift_xor_mask(y, shift, mask):
    result = 0
    for i in range(32):
        if i < shift:
            bit = (y >> i) & 1
        else:
            prev_bit = (result >> (i - shift)) & 1
            mask_bit = (mask >> i) & 1
            current_bit = (y >> i) & 1
            bit = current_bit ^ (prev_bit & mask_bit)
        result |= (bit << i)
    return result
```

La fonction `untemper` inverse les 4 etapes **dans l'ordre inverse** :

```python
def untemper(y):
    y = invert_right_shift_xor(y, 18)      # inverse y ^= y >> L
    y = invert_left_shift_xor_mask(y, 15, 0xEFC60000)  # inverse y ^= (y << T) & C
    y = invert_left_shift_xor_mask(y, 7, 0x9D2C5680)   # inverse y ^= (y << S) & B
    y = invert_right_shift_xor(y, 11)      # inverse y ^= (y >> U) & D
    return y
```

#### Reconstruction et prediction

1. **Reconstruction** : appliquer `untemper` sur chacune des 624 sorties observees pour obtenir l'etat interne

```python
def recover_state(outputs):
    state = []
    for i in range(624):
        state.append(untemper(outputs[i]))
    return state
```

2. **Prediction** : appliquer `twist` sur l'etat reconstruit, puis `temper` pour generer les sorties futures

```python
def predict_next(state, n):
    state = state.copy()
    index = N  # Force un twist au premier appel
    predictions = []
    for _ in range(n):
        if index >= N:
            state = twist(state)
            index = 0
        predictions.append(temper(state[index]))
        index += 1
    return predictions
```

Le `index = N` force un twist des le premier appel car l'etat reconstruit correspond aux valeurs **avant** le prochain twist. Les 624 sorties observees ont ete extraites de cet etat ; les suivantes proviendront de l'etat apres twist.

#### Resultats

L'attaque produit une **prediction parfaite a 100%** des sorties futures. Apres avoir observe 624 nombres (soit 2496 octets), l'attaquant peut predire toute la suite indefiniment.

**Complexite** : `O(624)` inversions de tempering, soit moins d'une milliseconde.

#### Conclusion sur le Mersenne Twister

Malgre ses excellentes proprietes statistiques (periode de `2^19937 - 1`, equidistribution 623-dimensionnelle), le MT19937 est **totalement previsible** apres 624 observations. Il ne doit **jamais** etre utilise en cryptographie.

---

## 4. Recommandations

| Usage | Generateur recommande | Justification |
|-------|----------------------|---------------|
| Simulation, jeux | LCG, Mersenne Twister | Rapides, bonnes proprietes statistiques |
| Cryptographie | `os.urandom`, `secrets` (Python) | Sources d'entropie systeme, resistantes aux attaques |
| Standard NIST | Hash_DRBG (SP 800-90A) | Certifie, audite, base sur SHA-256 |

**Regles fondamentales** :
1. Ne jamais utiliser un PRNG non cryptographique pour generer des cles, nonces ou IV
2. Toujours utiliser des nonces/IV uniques et imprevisibles en AES-CTR/CBC
3. Privilegier `os.urandom` ou le module `secrets` de Python pour tout besoin de securite

---

## Bibliographie

- Knuth, D. E. *The Art of Computer Programming, Volume 2: Seminumerical Algorithms*. Addison-Wesley, 1997.
- Matsumoto, M., Nishimura, T. "Mersenne Twister: A 623-dimensionally equidistributed uniform pseudorandom number generator". *ACM Transactions on Modeling and Computer Simulation*, 1998.
- NIST SP 800-90A Rev. 1. "Recommendation for Random Number Generation Using Deterministic Random Bit Generators". 2015.
- Marsaglia, G. "Random numbers fall mainly in the planes". *Proceedings of the National Academy of Sciences*, 1968.
- Kolmogorov, A. N. "Sulla determinazione empirica di una legge di distribuzione". *Giornale dell'Istituto Italiano degli Attuari*, 1933.
