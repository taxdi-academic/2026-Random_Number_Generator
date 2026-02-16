"""
Construction XOR NRBG (Non-deterministic Random Bit Generator)
Combine plusieurs sources d'entropie via XOR pour robustesse
https://fr.wikipedia.org/wiki/Fonction_OU_exclusif
"""

def xor_combine_bits(sources):
    """
    Combine sources de bits via XOR bit-a-bit
    Principe: Si >=1 source aleatoire et independante,
        sortie reste aleatoire (robustesse defaillance)
    Parametres:
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
    Combine sources d'octets via XOR octet-par-octet
    Parametres:
        sources: liste de bytes (meme longueur)
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
    Generateur hybride combinant plusieurs PRNGs via XOR
    Avantage: Si un generateur compromis, sortie reste imprevisible
        si autres generateurs sains
    Parametres:
        generators: [gen1, gen2, ...] avec signature gen(seed, n)
        seeds: [seed1, seed2, ...]
        n: nombre de valeurs
    """
    if len(generators) != len(seeds):
        raise ValueError("Nombre generateurs != nombre graines")

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

    print("\nXOR generateurs")
    gen1 = lambda seed, n: [(seed + i) % 256 for i in range(n)]
    gen2 = lambda seed, n: [(seed * 2 + i) % 256 for i in range(n)]
    result = xor_nrbg([gen1, gen2], [42, 17], 5)
    print(f"XOR(gen1, gen2): {result}")
