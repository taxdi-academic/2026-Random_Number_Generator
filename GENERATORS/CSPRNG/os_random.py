"""
System generator (os.urandom)

Interface provided by the operating system, relying on hardware and
software entropy sources (/dev/urandom on Linux, CryptGenRandom on Windows).

Commonly used as the reference cryptographically secure generator in practice.
"""

import os


def os_generate_bytes(n):
    """Generates n truly random bytes via the OS."""
    return os.urandom(n)


def os_next_int32():
    """Returns a random 32-bit integer."""
    return int.from_bytes(os.urandom(4), "big")


def os_next_float():
    """Returns a random float in [0, 1)."""
    return os_next_int32() / (2**32)


if __name__ == "__main__":
    print("os.urandom - 10 random 32-bit numbers:")
    for _ in range(10):
        print(f"  {os_next_int32()}")
    data = os_generate_bytes(16)
    print(f"\n16 bytes: {data.hex()}")
