#!/usr/bin/env python3
"""
PRIME-Net Swarm Invariant Mining: Project-Levitas (Voynich MS 408)
=================================================================
Deploys an 8-island cooperative PRIME-Net symbolic regression swarm to
discover analytical invariants, dynamical recurrences, spatial coordinate
dependencies, and linguistic scaling laws across the Voynich Manuscript
and adversarial controls.

Experiments:
  1. Autoregressive Recurrence Mining: c_t = f(c_{t-1}, c_{t-2}, c_{t-3}, t/L)
  2. 2D Spatial Coordinate Invariants: c_i = f(X, Y, X*Y, ...)
  3. Heaps' Law / State Growth Equations: S(N) = f(N)
  4. Word-Length Distribution Invariants: P(L) = f(L)
"""

import os
import re
import time
import collections
import concurrent.futures
import numpy as np
import pandas as pd
from pathlib import Path

from prime_core import run_prime_engine, _compute_r2

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"

# ----------------------------------------------------------------------
# SWARM WORKER
# ----------------------------------------------------------------------
def _swarm_worker(args):
    X_in, y_in, pop, gens, to, seed = args
    return run_prime_engine(
        X_in, y_in,
        pop_size=pop,
        seq_len=63,
        macro_seq_len=15,
        max_generations=gens,
        timeout_sec=to,
        enable_affine=True,
        lambda_penalty=0.005,
        seed=seed,
    )

def run_swarm_search(X, y, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0):
    seeds = [42 + i * 101 for i in range(num_islands)]
    tasks = [(X, y, island_pop, max_gens, timeout_sec, s) for s in seeds]

    t0 = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_islands) as executor:
        results = list(executor.map(_swarm_worker, tasks))
    elapsed = time.perf_counter() - t0

    valid = [r for r in results if r["best_sympy"] is not None and r["train_r2"] > -100]
    best = min(valid, key=lambda r: r["train_mse"]) if valid else results[0]
    unique_formulas = len(set(str(r["best_sympy"]) for r in results))

    return {
        "train_r2": best["train_r2"],
        "train_mse": best["train_mse"],
        "formula": str(best["best_sympy"]),
        "discovery_gen": best["discovery_gen"],
        "latency_sec": elapsed,
        "unique_explorations": unique_formulas,
    }

# ----------------------------------------------------------------------
# DATA LOADERS
# ----------------------------------------------------------------------
def load_voynich_tokens():
    with open(DATA_DIR / "voynich_full_corpus.txt") as f:
        lines = f.readlines()
    tokens = []
    for line_raw in lines:
        if not line_raw.strip() or line_raw.startswith('#'): continue
        m = re.search(r'<(\d+)[^.]*\.([^>]+)>', line_raw)
        if m:
            folio = int(m.group(1))
            line_str = m.group(2)
            line_num = int(line_str) if line_str.isdigit() else sum(ord(c) for c in line_str)
        else:
            folio, line_num = 0, 0
        body = re.sub(r'<[^>]*>', '', line_raw)
        char_pos = 0
        for ch in body:
            if ch.isalnum():
                tokens.append({'char': ch, 'folio': folio, 'line': line_num, 'pos': char_pos})
                char_pos += 1
            elif ch in '.,':
                if tokens and tokens[-1]['char'] != ' ':
                    tokens.append({'char': ' ', 'folio': folio, 'line': line_num, 'pos': char_pos})
                    char_pos += 1
    return tokens

def load_cracked_cipher():
    with open(ROOT_DIR / "cracked_cipher_input.txt") as f:
        lines = f.readlines()
    tokens = []
    for line_raw in lines:
        m = re.search(r'<(\d+)\.([^>]+)>', line_raw)
        line_num = int(m.group(2)) if m else 0
        body = re.sub(r'<[^>]*>', '', line_raw).strip()
        for pos, ch in enumerate(body):
            tokens.append({'char': ch, 'line': line_num, 'pos': pos})
    return tokens

def load_latin_large(max_chars=100000):
    with open(DATA_DIR / "latin_control_large.txt") as f:
        text = f.read(max_chars)
    tokens = []
    pos = 0
    line = 0
    for ch in text:
        if ch.isalpha():
            tokens.append({'char': ch.lower(), 'line': line, 'pos': pos})
            pos += 1
            if pos >= 60:
                pos = 0
                line += 1
    return tokens

def load_homophonic_latin(max_chars=100000):
    with open(DATA_DIR / "homophonic_latin.txt") as f:
        text = f.read(max_chars)
    tokens = []
    pos = 0
    line = 0
    for ch in text:
        if ch.isalnum():
            tokens.append({'char': ch, 'line': line, 'pos': pos})
            pos += 1
            if pos >= 60:
                pos = 0
                line += 1
    return tokens

def load_synthetic_markov(max_chars=100000):
    with open(ROOT_DIR / "synthetic_levitas_corpus.txt") as f:
        text = f.read(max_chars)
    tokens = []
    pos = 0
    line = 0
    for ch in text:
        if ch.isalnum():
            tokens.append({'char': ch, 'line': line, 'pos': pos})
            pos += 1
            if pos >= 60:
                pos = 0
                line += 1
    return tokens

# ----------------------------------------------------------------------
# MAIN EXPERIMENT RUNNER
# ----------------------------------------------------------------------
def main():
    print("=" * 115)
    print("       PRIME-NET SWARM INVARIANT MINING: PROJECT-LEVITAS (VOYNICH MS 408)")
    print("=" * 115)

    all_records = []

    print("[*] Loading datasets...")
    v_tokens = load_voynich_tokens()
    cracked_tokens = load_cracked_cipher()
    latin_tokens = load_latin_large()
    homo_tokens = load_homophonic_latin()
    markov_tokens = load_synthetic_markov()

    v_f67 = [t for t in v_tokens if t['folio'] == 67]
    v_astro = [t for t in v_tokens if 67 <= t['folio'] <= 73]
    v_bio = [t for t in v_tokens if 75 <= t['folio'] <= 84]

    print(f"[*] Datasets Loaded:")
    print(f"    - Voynich Full Corpus:    {len(v_tokens):,} tokens")
    print(f"    - Voynich Folio 67:       {len(v_f67):,} tokens")
    print(f"    - Voynich Astronomical:   {len(v_astro):,} tokens (Folios 67-73)")
    print(f"    - Voynich Biological:     {len(v_bio):,} tokens (Folios 75-84)")
    print(f"    - Cracked Mechanical GT:  {len(cracked_tokens):,} tokens (Ground Truth 3x2 Grille)")
    print(f"    - Classical Latin Large:  {len(latin_tokens):,} tokens")
    print(f"    - Homophonic Latin:       {len(homo_tokens):,} tokens")
    print(f"    - Synthetic Markov Voy:   {len(markov_tokens):,} tokens")

    # ==================================================================
    # EXPERIMENT 1: Dynamical Recurrence Mining
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [EXPERIMENT 1] Autoregressive Recurrence Law Discovery: c_t = f(c_{t-1}, c_{t-2}, c_{t-3}, t/L)")
    print(" Goal: Test whether glyph sequences exhibit non-linear dynamical recurrences or collapse to stochastic noise.")
    print("=" * 115)

    recurrence_targets = [
        ("Voynich Full Corpus", [ord(t['char']) for t in v_tokens[:2500]]),
        ("Voynich Astronomical (f67-73)", [ord(t['char']) for t in v_astro[:2500]]),
        ("Voynich Biological (f75-84)", [ord(t['char']) for t in v_bio[:2500]]),
        ("Classical Latin (Perseus)", [ord(t['char']) for t in latin_tokens[:2500]]),
        ("Homophonic Latin Cipher", [ord(t['char']) for t in homo_tokens[:2500]]),
        ("Mechanical 3x2 Grille (GT)", [ord(t['char']) for t in cracked_tokens[:2500]]),
        ("Synthetic Markov Voynich", [ord(t['char']) for t in markov_tokens[:2500]]),
    ]

    for name, series in recurrence_targets:
        s = np.array(series, dtype=np.float64)
        L = len(s)
        X = np.column_stack([
            s[2:-1],            # c_{t-1}
            s[1:-2],            # c_{t-2}
            s[0:-3],            # c_{t-3}
            np.linspace(0, 1, L - 3) # t / L
        ])
        y = s[3:]

        res = run_swarm_search(X, y, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
        res["experiment"] = "Autoregressive Recurrence"
        res["target"] = name
        all_records.append(res)

        print(f"[{name}]")
        print(f"  R^2:      {res['train_r2']:+.5f}  |  MSE: {res['train_mse']:10.2f}")
        print(f"  Formula:  {res['formula']}")
        print(f"  Latency:  {res['latency_sec']:.2f}s across 8 islands ({res['unique_explorations']} distinct formulas)\n")

    # ==================================================================
    # EXPERIMENT 2: 2D Spatial Coordinate Invariants (c = f(X, Y))
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [EXPERIMENT 2] 2D Spatial / Volvelle Coordinate Invariant Discovery: c = f(X, Y, X*Y, ...)")
    print(" Goal: Test if character identity is a deterministic function of physical 2D coordinates on the page.")
    print("=" * 115)

    spatial_targets = [
        ("Mechanical 3x2 Grille (GT)", cracked_tokens[:2500]),
        ("Voynich Folio 67 (Wheel/Rosette)", v_f67[:2000]),
        ("Voynich Astronomical (f67-73)", v_astro[:2500]),
        ("Voynich Biological (f75)", [t for t in v_bio if t['folio'] == 75][:2000]),
        ("Classical Latin Grid Control", latin_tokens[:2500]),
    ]

    for name, toks in spatial_targets:
        chars = np.array([ord(t['char']) for t in toks], dtype=np.float64)
        X_pos = np.array([t['pos'] for t in toks], dtype=np.float64)
        Y_line = np.array([t['line'] for t in toks], dtype=np.float64)

        # Feature matrix: X, Y, X*Y, sin/cos periodicity candidate
        X_feat = np.column_stack([
            X_pos,
            Y_line,
            X_pos * Y_line,
            np.sin(2 * np.pi * X_pos / 3.0),  # Grille frequency test
            np.cos(np.pi * Y_line),            # Grille line parity test
        ])
        y = chars

        res = run_swarm_search(X_feat, y, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
        res["experiment"] = "Spatial Coordinate Invariant"
        res["target"] = name
        all_records.append(res)

        print(f"[{name}]")
        print(f"  R^2:      {res['train_r2']:+.5f}  |  MSE: {res['train_mse']:10.2f}")
        print(f"  Formula:  {res['formula']}")
        print(f"  Latency:  {res['latency_sec']:.2f}s across 8 islands\n")

    # ==================================================================
    # EXPERIMENT 3: Heaps' Law & Vocabulary Growth Equations (S(N) = f(N))
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [EXPERIMENT 3] Heaps' Law & Bigram State Growth Symbolic Derivation: S(N) = f(N)")
    print(" Goal: Mine the exact mathematical growth function governing state discovery (Power-Law vs Saturation).")
    print("=" * 115)

    sample_Ns = [500, 1000, 2000, 5000, 10000, 20000, 35000, 50000, 75000, 100000, 150000, 193960]

    def compute_state_growth(char_list, N_steps):
        states = []
        for n in N_steps:
            sub = char_list[:n]
            bigrams = set(zip(sub[:-1], sub[1:]))
            states.append(len(bigrams))
        return np.array(states, dtype=np.float64)

    v_chars = [t['char'] for t in v_tokens]
    with open(DATA_DIR / "latin_control_large.txt") as f:
        lat_full = [c.lower() for c in f.read(250000) if c.isalpha()]
    with open(DATA_DIR / "homophonic_latin.txt") as f:
        homo_full = [c for c in f.read(250000) if c.isalnum()]

    N_arr = np.array(sample_Ns, dtype=np.float64)
    N_norm = N_arr / 10000.0  # Normalize N in units of 10k tokens

    heaps_targets = [
        ("Voynich Full Corpus (v101)", compute_state_growth(v_chars, sample_Ns)),
        ("Classical Latin (Perseus)", compute_state_growth(lat_full, sample_Ns)),
        ("Homophonic Latin Cipher", compute_state_growth(homo_full, sample_Ns)),
    ]

    for name, S_arr in heaps_targets:
        X_heaps = np.column_stack([
            N_norm,
            np.log(N_norm + 0.01),
            np.sqrt(N_norm),
            1.0 / (N_norm + 0.1)
        ])
        y = S_arr

        res = run_swarm_search(X_heaps, y, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
        res["experiment"] = "Heaps Law Growth Equation"
        res["target"] = name
        all_records.append(res)

        print(f"[{name}]")
        print(f"  Empirical S(N): {list(zip(sample_Ns[::2], S_arr[::2].astype(int)))}")
        print(f"  R^2:      {res['train_r2']:+.5f}  |  MSE: {res['train_mse']:10.2f}")
        print(f"  Formula:  {res['formula']}")
        print(f"  Latency:  {res['latency_sec']:.2f}s\n")

    # ==================================================================
    # EXPERIMENT 4: Word-Length Distribution Invariant (P(L) = f(L))
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [EXPERIMENT 4] Word-Length Probability Invariant Discovery: P(L) = f(L)")
    print(" Goal: Mine the closed-form density function governing word length distributions in Voynich vs Latin.")
    print("=" * 115)

    def extract_word_lengths(text):
        words = text.split()
        lens = [len(w) for w in words if len(w) > 0 and len(w) <= 20]
        c = collections.Counter(lens)
        tot = sum(c.values())
        return np.array([c.get(l, 0) / tot for l in range(1, 16)], dtype=np.float64)

    with open(DATA_DIR / "voynich_full_corpus.txt") as f:
        v_raw_text = re.sub(r'<[^>]*>', '', f.read()).replace('.', ' ').replace(',', ' ')
    with open(DATA_DIR / "latin_control_large.txt") as f:
        l_raw_text = f.read(500000)

    v_p_len = extract_word_lengths(v_raw_text)
    l_p_len = extract_word_lengths(l_raw_text)

    L_vals = np.arange(1, 16, dtype=np.float64)
    X_len = np.column_stack([
        L_vals,
        L_vals**2,
        np.log(L_vals),
        np.exp(-L_vals / 4.0),
    ])

    for name, p_dist in [("Voynich Word Length P(L)", v_p_len), ("Latin Word Length P(L)", l_p_len)]:
        res = run_swarm_search(X_len, p_dist, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
        res["experiment"] = "Word-Length Distribution"
        res["target"] = name
        all_records.append(res)

        print(f"[{name}]")
        print(f"  Empirical Peak: L={np.argmax(p_dist)+1} with P={np.max(p_dist):.3f}")
        print(f"  R^2:      {res['train_r2']:+.5f}  |  MSE: {res['train_mse']:10.6f}")
        print(f"  Formula:  {res['formula']}")
        print(f"  Latency:  {res['latency_sec']:.2f}s\n")

    # ==================================================================
    # SUMMARY REPORT
    # ==================================================================
    df = pd.DataFrame(all_records)
    out_csv = ROOT_DIR / "levitas_swarm_findings.csv"
    df.to_csv(out_csv, index=False)
    print("=" * 115)
    print(f"[+] All Experiments Complete! Summary saved to: {out_csv}")
    print("=" * 115)

if __name__ == "__main__":
    main()
