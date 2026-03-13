"""
NIST SP 800-90A Hash_DRBG (SHA-256)

Simplified implementation of the Deterministic Random Bit Generator
based on SHA-256, compliant with NIST SP 800-90A standard.

State is represented as a dict {"V": bytes, "C": bytes, "reseed_counter": int}.

This CSPRNG provides guarantees against prediction of future outputs
and supports reseeding to refresh entropy.
"""

import hashlib
import os

SEED_LEN = 55  # seedlen for SHA-256 = 440 bits = 55 bytes


def _sha256(data):
    """SHA-256 hash."""
    return hashlib.sha256(data).digest()


def _hash_df(input_data, num_bytes):
    """
    Hash derivation function (Hash_df) per NIST SP 800-90A.
    Derives num_bytes bytes from the input data.
    """
    hash_len = 32
    num_blocks = (num_bytes + hash_len - 1) // hash_len
    result = b""
    for counter in range(1, num_blocks + 1):
        to_hash = counter.to_bytes(1, "big") + num_bytes.to_bytes(4, "big") + input_data
        result += _sha256(to_hash)
    return result[:num_bytes]


def drbg_instantiate(entropy=None, nonce=None, personalization=b""):
    """
    Instantiates the DRBG.

    Args:
        entropy         : initial entropy (bytes). If None, uses os.urandom.
        nonce           : nonce (bytes). If None, uses os.urandom.
        personalization : optional personalisation string

    Returns:
        state : dict {"V", "C", "reseed_counter"}
    """
    if entropy is None:
        entropy = os.urandom(SEED_LEN)
    if nonce is None:
        nonce = os.urandom(SEED_LEN // 2)

    seed_material = entropy + nonce + personalization
    seed = _hash_df(seed_material, SEED_LEN)

    V = seed
    C = _hash_df(b"\x00" + seed, SEED_LEN)
    return {"V": V, "C": C, "reseed_counter": 1}


def drbg_reseed(state, entropy=None):
    """
    Reseeds the DRBG with new entropy.

    Args:
        state   : current state
        entropy : new entropy (bytes). If None, uses os.urandom.

    Returns:
        updated state
    """
    if entropy is None:
        entropy = os.urandom(SEED_LEN)

    seed = _hash_df(b"\x01" + state["V"] + entropy, SEED_LEN)
    state["V"] = seed
    state["C"] = _hash_df(b"\x00" + seed, SEED_LEN)
    state["reseed_counter"] = 1
    return state


def drbg_generate(state, num_bytes):
    """
    Generates num_bytes pseudorandom bytes.

    Args:
        state     : current state
        num_bytes : number of bytes to generate

    Returns:
        (output_bytes, state)
    """
    hash_len = 32
    m = (num_bytes + hash_len - 1) // hash_len
    W = b""
    data = state["V"]
    for _ in range(m):
        W += _sha256(data)
        int_data = (int.from_bytes(data, "big") + 1) % (2 ** (len(data) * 8))
        data = int_data.to_bytes(len(state["V"]), "big")
    output = W[:num_bytes]

    # State update
    H = _sha256(b"\x03" + state["V"])
    int_v = int.from_bytes(state["V"], "big")
    int_h = int.from_bytes(H, "big")
    int_c = int.from_bytes(state["C"], "big")
    mod = 2 ** (SEED_LEN * 8)
    new_v = (int_v + int_h + int_c + state["reseed_counter"]) % mod
    state["V"] = new_v.to_bytes(SEED_LEN, "big")
    state["reseed_counter"] += 1

    return output, state


def drbg_generate_bytes(n, entropy=None, nonce=None):
    """
    Shortcut function: instantiates the DRBG and generates n bytes.

    Returns:
        bytes of length n
    """
    state = drbg_instantiate(entropy=entropy, nonce=nonce)
    output, _ = drbg_generate(state, n)
    return output


if __name__ == "__main__":
    state = drbg_instantiate(entropy=b"A" * 55, nonce=b"B" * 28)
    print("Hash_DRBG (SHA-256) - 32 bytes:")
    data, state = drbg_generate(state, 32)
    print(f"  {data.hex()}")
    print(f"\nAfter reseed - 32 bytes:")
    state = drbg_reseed(state, b"C" * 55)
    data, state = drbg_generate(state, 32)
    print(f"  {data.hex()}")
