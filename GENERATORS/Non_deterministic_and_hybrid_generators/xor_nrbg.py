# generators/xor_nrbg.py

"""
XOR NRBG (Non-deterministic Random Bit Generator) construction
Combines multiple entropy sources via XOR for robustness
https://en.wikipedia.org/wiki/Exclusive_or
"""

def xor_combine_bits(sources):
    """
    Combines bit sources via bitwise XOR
    Principle: if at least 1 source is random and independent,
        the output remains random (fault tolerance)
    Parameters:
        sources: [[1,0,1], [0,1,1], [1,1,0]]
    """
    if not sources:
        return []

    n = len(sources[0])
    result = []
    for i in range(n):
        bit = 0
        for source in sources:
            bit ^= source[i]
        result.append(bit)
    return result

def xor_combine_bytes(sources):
    """
    Combines byte sources via byte-wise XOR
    Parameters:
        sources: list of bytes (same length)
    """
    if not sources:
        return b''

    n = len(sources[0])
    result = bytearray(n)
    for i in range(n):
        xor_val = 0
        for source in sources:
            xor_val ^= source[i]
        result[i] = xor_val
    return bytes(result)

def xor_nrbg(generators, seeds, n):
    """
    Hybrid generator combining multiple PRNGs via XOR
    Advantage: if one generator is compromised, the output remains
        unpredictable as long as the other generators are healthy
    Parameters:
        generators: [gen1, gen2, ...] with signature gen(seed, n)
        seeds: [seed1, seed2, ...]
        n: number of values to generate
    """
    if len(generators) != len(seeds):
        raise ValueError("Number of generators != number of seeds")

    outputs = [gen(seed, n) for gen, seed in zip(generators, seeds)]

    result = []
    for i in range(n):
        xor_val = 0
        for output in outputs:
            xor_val ^= output[i]
        result.append(xor_val)
    return result

# Tests
if __name__ == "__main__":
    print("XOR bits")
    src_bits = [[1, 0, 1, 1], [0, 1, 1, 0], [1, 1, 0, 1]]
    print(f"Sources: {src_bits}")
    print(f"XOR: {xor_combine_bits(src_bits)}")

    print("\nXOR bytes")
    src_bytes = [b'\xAA\xBB', b'\x55\x44', b'\xFF\x00']
    print(f"Sources: {[s.hex() for s in src_bytes]}")
    print(f"XOR: {xor_combine_bytes(src_bytes).hex()}")

    print("\nXOR generators")
    gen1 = lambda seed, n: [(seed + i) % 256 for i in range(n)]
    gen2 = lambda seed, n: [(seed * 2 + i) % 256 for i in range(n)]
    result = xor_nrbg([gen1, gen2], [42, 17], 5)
    print(f"XOR(gen1, gen2): {result}")
