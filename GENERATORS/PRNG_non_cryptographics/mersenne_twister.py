"""
Mersenne Twister MT19937
PRNG with period 2^19937 - 1
Not cryptographically secure
https://en.wikipedia.org/wiki/Mersenne_Twister
"""

W, N, M, R = 32, 624, 397, 31
A = 0x9908B0DF
F = 1812433253
U, D = 11, 0xFFFFFFFF
S, B = 7, 0x9D2C5680
T, C = 15, 0xEFC60000
L = 18

def init(seed):
    """Initialises the internal state"""
    state = [seed & 0xFFFFFFFF]
    for i in range(1, N):
        prev = state[i - 1]
        state.append((F * (prev ^ (prev >> 30)) + i) & 0xFFFFFFFF)
    return state

def twist(state):
    """Twist transformation"""
    for i in range(N):
        # Extract bit 31 from state[i] and bits 0-30 from state[i+1]
        upper_bit = state[i] & 0x80000000
        lower_bits = state[(i + 1) % N] & 0x7FFFFFFF
        x = upper_bit | lower_bits
        x_shifted = x >> 1
        if x & 1:  # Least significant bit = 1
            x_shifted ^= A
        state[i] = state[(i + M) % N] ^ x_shifted
    return state

def temper(y):
    """Tempering to improve distribution"""
    y ^= (y >> U) & D
    y ^= (y << S) & B
    y ^= (y << T) & C
    y ^= y >> L
    return y & 0xFFFFFFFF

def generate(seed, n):
    """Generates n 32-bit numbers"""
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
