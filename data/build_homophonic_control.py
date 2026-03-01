"""
build_homophonic_control.py  (v3)
----------------------------------
Reads latin_control_large.txt, applies a 70-symbol homophonic cipher,
writes homophonic_latin.txt. Uses Largest Remainder Method with no
iterative trim — O(n log n) allocation, numpy-vectorized encryption.
"""

import numpy as np
from collections import Counter
from pathlib import Path

DATA_DIR    = Path(__file__).parent
INPUT_FILE  = DATA_DIR / "latin_control_large.txt"
OUTPUT_FILE = DATA_DIR / "homophonic_latin.txt"
TARGET      = 70
SEED        = 42


def allocate_shares(freq: dict, target: int) -> dict:
    """
    Largest Remainder Method — distributes ``target`` symbols exactly.

    Never requires a trim loop: computes quotas, takes floors, then awards
    remaining seats to the largest remainders. Minimum 1 is enforced before
    running LRM so the floor is never zero.

    Args:
        freq: {char: count} for each character in the vocabulary.
        target: Total symbols to distribute.

    Returns:
        {char: num_symbols} with sum == target.

    Raises:
        ValueError: If vocab size exceeds target (can't give everyone ≥ 1).
    """
    chars = list(freq.keys())
    n = len(chars)
    if n > target:
        raise ValueError(
            f"Vocabulary size {n} exceeds target_symbols={target}. "
            "Reduce your character set or increase target_symbols."
        )

    total  = sum(freq.values())
    quotas = {c: (freq[c] / total) * target for c in chars}

    # Floor, then award remaining seats to the largest remainders
    floors = {c: max(1, int(quotas[c])) for c in chars}
    used   = sum(floors.values())
    seats  = target - used

    if seats < 0:
        # Floors exceed target — reduce the chars with the smallest fractional
        # gains iteratively (rare: only when n is large and quotas ~ 1.x)
        by_frac = sorted(chars, key=lambda c: quotas[c] - int(quotas[c]))
        for c in by_frac:
            if seats >= 0:
                break
            if floors[c] > 1:
                floors[c] -= 1
                seats += 1
    else:
        # Normal case: award remaining seats to largest remainders
        by_remainder = sorted(
            chars,
            key=lambda c: quotas[c] - int(quotas[c]),
            reverse=True,
        )
        for c in by_remainder[:seats]:
            floors[c] += 1

    assert sum(floors.values()) == target, "Allocation mismatch"
    return floors


def build_cipher(text: str, target: int = 70, seed: int = 42) -> tuple:
    """
    Build cipher map and encrypt ``text`` using numpy vectorization.

    Args:
        text: Raw corpus string.
        target: Number of cipher symbols (default 70).
        seed: RNG seed for reproducibility.

    Returns:
        Tuple of (ciphertext_str, cipher_map_dict).
    """
    # Strip to lowercase a-z ONLY (exclude accented / extended chars)
    clean = ''.join(c for c in text.lower() if 'a' <= c <= 'z')
    counts = Counter(clean)

    pool = [chr(i) for i in range(33, 127)][:target]
    shares = allocate_shares(counts, target)

    # Assign symbol blocks most-frequent first
    cipher_map: dict = {}
    for ch, _ in counts.most_common():
        k = shares[ch]
        cipher_map[ch] = pool[:k]
        pool = pool[k:]

    # Vectorized: build lookup tables indexed by ord()
    max_w = max(len(v) for v in cipher_map.values())
    lookup = np.zeros((128, max_w), dtype=np.uint8)
    widths  = np.zeros(128,         dtype=np.uint8)
    for ch, syms in cipher_map.items():
        o = ord(ch)
        lookup[o, :len(syms)] = [ord(s) for s in syms]
        widths[o] = len(syms)

    arr  = np.frombuffer(clean.encode('ascii'), dtype=np.uint8)
    rng  = np.random.default_rng(seed)
    # rand in [0,1) * width → slot index
    slots = (rng.random(len(arr)) * widths[arr]).astype(np.uint8)
    out   = lookup[arr, slots]
    return out.tobytes().decode('ascii'), cipher_map


def main() -> None:
    """Entry point: read, cipher, write, report."""
    print(f"Reading {INPUT_FILE} ...")
    raw = INPUT_FILE.read_text(encoding="utf-8", errors="ignore")
    print(f"  Raw chars: {len(raw):,}")

    print("Building cipher & encrypting ...")
    ciphertext, cipher_map = build_cipher(raw, TARGET, SEED)
    print(f"  Ciphertext: {len(ciphertext):,} chars")

    OUTPUT_FILE.write_text(ciphertext, encoding="utf-8")
    print(f"  Saved -> {OUTPUT_FILE}")

    # Sanity check frequency table
    plain_alpha = ''.join(c for c in raw.lower() if c.isalpha())
    pfreq = Counter(plain_alpha)
    cfreq = Counter(ciphertext)
    tp, tc = len(plain_alpha), len(ciphertext)

    print(f"\n{'Char':<6}{'Syms':>5}  {'Plain%':>7}  {'Cipher%':>8}")
    print("-" * 35)
    for ch, n in pfreq.most_common(15):
        syms = cipher_map.get(ch, [])
        sc   = sum(cfreq.get(s, 0) for s in syms)
        print(f"  {ch!r:<4}{len(syms):>5}  {n/tp*100:>6.2f}%  {sc/tc*100:>7.2f}%")

    total_syms = sum(len(v) for v in cipher_map.values())
    print(f"\nAllocated: {total_syms}/{TARGET} symbols. Done.")


if __name__ == "__main__":
    main()
