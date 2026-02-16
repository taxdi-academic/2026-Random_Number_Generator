"""
Mersenne Twister MT19937
PRNG de periode 2^19937 - 1
Non cryptographiquement securise
https://fr.wikipedia.org/wiki/Mersenne_Twister
"""

W, N, M, R = 32, 624, 397, 31
A = 0x9908B0DF
F = 1812433253
U, D = 11, 0xFFFFFFFF
S, B = 7, 0x9D2C5680
T, C = 15, 0xEFC60000
L = 18

def init(seed):
    """Initialise l'etat interne"""
    state = [seed & 0xFFFFFFFF]
    for i in range(1, N):
        prev = state[i - 1]
        state.append((F * (prev ^ (prev >> 30)) + i) & 0xFFFFFFFF)
    return state

def twist(state):
    """Transformation twist"""
    for i in range(N):
        # Extraire bit 31 de state[i] et bits 0-30 de state[i+1]
        bit_haut = state[i] & 0x80000000
        bits_bas = state[(i + 1) % N] & 0x7FFFFFFF
        x = bit_haut | bits_bas
        x_shifted = x >> 1
        if x & 1:  # Bit de poids faible = 1
            x_shifted ^= A
        state[i] = state[(i + M) % N] ^ x_shifted
    return state

def temper(y):
    """Tempering pour ameliorer distribution"""
    y ^= (y >> U) & D
    y ^= (y << S) & B
    y ^= (y << T) & C
    y ^= y >> L
    return y & 0xFFFFFFFF

def generate(seed, n):
    """Genere n nombres 32-bits"""
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
