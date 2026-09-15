#!/usr/bin/env python3
"""
PRIME-Net Comprehensive Swarm Cryptanalysis: Project-Levitas (Voynich MS 408)
=============================================================================
Runs an exhaustive 6-battery diagnostic test suite using the 8-island cooperative
symbolic regression swarm across 24 CPU cores.

Batteries:
  1. Currier Hand / Dialect Split (Currier A vs Currier B recurrence & discriminant)
  2. Line-Position Dynamics & Scribe Reset Laws (gallows vs suffixes across line position)
  3. Word-Level Dynamics & The "Stuttering" Recurrence (w_t = f(w_{t-1}, w_{t-2}))
  4. Long-Range Auto-Correlation Decay C(tau) = f(tau) (fractal memory vs Markov)
  5. Polar Coordinate Harmonic Symmetries on Astronomical Folios (f67-f68)
  6. Morphological Slot-Grammar Mutual Dependency (Prefix-Suffix coupling)
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
# SWARM SEARCH ENGINE
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
def load_voynich_data():
    with open(DATA_DIR / "voynich_full_corpus.txt") as f:
        lines = f.readlines()
    tokens = []
    line_tokens = collections.defaultdict(list)
    folio_tokens = collections.defaultdict(list)

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
        current_line_toks = []
        for ch in body:
            if ch.isalnum():
                tok = {'char': ch, 'folio': folio, 'line': line_num, 'pos': char_pos}
                tokens.append(tok)
                current_line_toks.append(tok)
                char_pos += 1
            elif ch in '.,':
                if tokens and tokens[-1]['char'] != ' ':
                    tok = {'char': ' ', 'folio': folio, 'line': line_num, 'pos': char_pos}
                    tokens.append(tok)
                    current_line_toks.append(tok)
                    char_pos += 1
        if current_line_toks:
            line_key = (folio, line_num)
            line_tokens[line_key].extend(current_line_toks)
            folio_tokens[folio].extend(current_line_toks)

    return tokens, line_tokens, folio_tokens

def load_control_latin(max_chars=200000):
    with open(DATA_DIR / "latin_control_large.txt") as f:
        text = f.read(max_chars)
    tokens = [c.lower() for c in text if c.isalpha() or c == ' ']
    return tokens

# ----------------------------------------------------------------------
# MAIN BATTERY EXECUTION
# ----------------------------------------------------------------------
def main():
    print("=" * 115)
    print("      COMPREHENSIVE PRIME-NET SWARM CRYPTANALYSIS BATTERY: VOYNICH MS 408")
    print("=" * 115)

    tokens, line_tokens, folio_tokens = load_voynich_data()
    latin_tokens = load_control_latin()

    print(f"[*] Parsed Voynich Corpus:")
    print(f"    - Total Tokens:     {len(tokens):,}")
    print(f"    - Unique Folios:    {len(folio_tokens)}")
    print(f"    - Parsed Lines:     {len(line_tokens):,}")
    print(f"    - Latin Control:    {len(latin_tokens):,} chars")

    all_findings = []

    # ==================================================================
    # BATTERY 1: Currier Hand / Dialect Split Invariants
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [BATTERY 1] Currier Hand Split Invariants (Currier A vs Currier B)")
    print(" Goal: Test if Hand A (Botanical) and Hand B (Biological/Recipes) possess distinct dynamical laws.")
    print("=" * 115)

    # Currier A: folios 1 to 66; Currier B: folios 75 to 84 and 103 to 116
    currier_a = [t for t in tokens if 1 <= t['folio'] <= 66]
    currier_b = [t for t in tokens if (75 <= t['folio'] <= 84) or (103 <= t['folio'] <= 116)]

    print(f"[*] Currier A Tokens: {len(currier_a):,} | Currier B Tokens: {len(currier_b):,}")

    for name, subset in [("Currier Hand A (Herbal f1-66)", currier_a), ("Currier Hand B (Bio/Recipes f75-84,103-116)", currier_b)]:
        chars = np.array([ord(t['char']) for t in subset[:3000]], dtype=np.float64)
        L = len(chars)
        X = np.column_stack([
            chars[2:-1],
            chars[1:-2],
            chars[0:-3],
            np.linspace(0, 1, L - 3)
        ])
        y = chars[3:]

        res = run_swarm_search(X, y, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
        res["battery"] = "Battery 1: Currier Hand Split"
        res["target"] = name
        all_findings.append(res)

        print(f"[{name}]")
        print(f"  R^2:      {res['train_r2']:+.5f}  |  MSE: {res['train_mse']:10.2f}")
        print(f"  Formula:  {res['formula']}")
        print(f"  Latency:  {res['latency_sec']:.2f}s\n")

    # Folio-level Hand Discriminant: Can a simple invariant separate Hand A folios from Hand B folios?
    # Extract mean token value, word length variance, and trigram repetition per folio
    folio_features = []
    folio_labels = [] # 0 for A, 1 for B
    for f_id in sorted(folio_tokens.keys()):
        if 1 <= f_id <= 66: label = 0
        elif (75 <= f_id <= 84) or (103 <= f_id <= 116): label = 1
        else: continue

        f_toks = folio_tokens[f_id]
        if len(f_toks) < 100: continue

        chars = [t['char'] for t in f_toks if t['char'] != ' ']
        # F1: fraction of 'q'/'4' prefix
        f1 = sum(1 for c in chars if c in '4q') / len(chars)
        # F2: fraction of '9'/'y' suffix
        f2 = sum(1 for c in chars if c in '9y') / len(chars)
        # F3: fraction of 'e'/'7' core
        f3 = sum(1 for c in chars if c in '7e') / len(chars)

        folio_features.append([f1, f2, f3])
        folio_labels.append(label)

    X_disc = np.array(folio_features, dtype=np.float64)
    y_disc = np.array(folio_labels, dtype=np.float64)

    res_disc = run_swarm_search(X_disc, y_disc, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
    res_disc["battery"] = "Battery 1: Currier Hand Split"
    res_disc["target"] = "Folio Hand Discriminant D(q, y, e)"
    all_findings.append(res_disc)
    print(f"[Folio Hand Discriminant: Hand A (0) vs Hand B (1)]")
    print(f"  R^2:      {res_disc['train_r2']:+.5f}  |  MSE: {res_disc['train_mse']:10.4f}")
    print(f"  Formula:  {res_disc['formula']}")
    print(f"  Latency:  {res_disc['latency_sec']:.2f}s\n")

    # ==================================================================
    # BATTERY 2: Line-Position Dynamics & Scribe Reset Laws
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [BATTERY 2] Line-Position Dynamics & Scribe Reset Laws")
    print(" Goal: Mine the closed-form density function governing glyph selection as a function of intra-line position.")
    print("=" * 115)

    # Gallows characters in v101: 'k', 't', 'p', 'f' (and their uppercase equivalents)
    gallows = set("ktpfKTPF")
    suffixes = set("98am")

    # Divide line into 10 position bins: p in [0, 0.1), [0.1, 0.2), ...
    pos_bins = 10
    gallows_counts = np.zeros(pos_bins)
    suffix_counts = np.zeros(pos_bins)
    total_counts = np.zeros(pos_bins)

    for line_key, l_toks in line_tokens.items():
        L_line = len(l_toks)
        if L_line < 5: continue
        for idx, t in enumerate(l_toks):
            bin_idx = min(int((idx / L_line) * pos_bins), pos_bins - 1)
            total_counts[bin_idx] += 1
            if t['char'] in gallows:
                gallows_counts[bin_idx] += 1
            if t['char'] in suffixes:
                suffix_counts[bin_idx] += 1

    p_gallows = gallows_counts / np.maximum(total_counts, 1)
    p_suffixes = suffix_counts / np.maximum(total_counts, 1)
    p_norm = np.linspace(0.05, 0.95, pos_bins)

    X_pos = np.column_stack([
        p_norm,
        p_norm**2,
        np.exp(-3 * p_norm),
        np.exp(3 * (p_norm - 1)),
    ])

    for name, p_curve in [("Gallows Distribution P(gallows | p)", p_gallows), ("Suffix Distribution P(suffix | p)", p_suffixes)]:
        res = run_swarm_search(X_pos, p_curve, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
        res["battery"] = "Battery 2: Line-Position Dynamics"
        res["target"] = name
        all_findings.append(res)

        print(f"[{name}]")
        print(f"  Empirical Values across Line: {[round(x, 4) for x in p_curve]}")
        print(f"  R^2:      {res['train_r2']:+.5f}  |  MSE: {res['train_mse']:10.6f}")
        print(f"  Formula:  {res['formula']}")
        print(f"  Latency:  {res['latency_sec']:.2f}s\n")

    # ==================================================================
    # BATTERY 3: Word-Level Dynamics & The "Stuttering" Recurrence
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [BATTERY 3] Word-Level Recurrence & 'Stuttering' Dynamics")
    print(" Goal: Test whether consecutive word transitions exhibit grammatical dynamics or immediate self-repetition.")
    print("=" * 115)

    with open(DATA_DIR / "voynich_full_corpus.txt") as f:
        v_raw = re.sub(r'<[^>]*>', '', f.read()).replace('.', ' ').replace(',', ' ')
    v_words = [w for w in v_raw.split() if w]

    # Map words to rank IDs
    word_counts = collections.Counter(v_words)
    vocab = {w: i+1 for i, (w, _) in enumerate(word_counts.most_common())}
    v_word_ids = np.array([vocab[w] for w in v_words[:3000]], dtype=np.float64)

    # Word-level autoregression: w_t = f(w_{t-1}, w_{t-2}, t)
    L_w = len(v_word_ids)
    X_word = np.column_stack([
        v_word_ids[2:-1],
        v_word_ids[1:-2],
        np.linspace(0, 1, L_w - 3)
    ])
    y_word = v_word_ids[3:]

    # Calculate exact immediate consecutive word repetition rate: w_t == w_{t-1}
    exact_stutter_v = sum(1 for i in range(1, len(v_words)) if v_words[i] == v_words[i-1]) / len(v_words)

    # Latin control word repetition rate:
    with open(DATA_DIR / "latin_control_large.txt") as f:
        l_words = f.read(300000).split()
    exact_stutter_l = sum(1 for i in range(1, len(l_words)) if l_words[i] == l_words[i-1]) / len(l_words)

    res_word = run_swarm_search(X_word, y_word, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
    res_word["battery"] = "Battery 3: Word-Level Recurrence"
    res_word["target"] = "Voynich Word Sequence Recurrence w_t = f(w_{t-1}, w_{t-2})"
    all_findings.append(res_word)

    print("[Word-Level Recurrence: w_t = f(w_{t-1}, w_{t-2}, t)]")
    print(f"  Voynich Consecutive Word Stutter Rate: {exact_stutter_v:.4%} ({sum(1 for i in range(1, len(v_words)) if v_words[i] == v_words[i-1])} occurrences)")
    print(f"  Latin Consecutive Word Stutter Rate:   {exact_stutter_l:.4%} ({sum(1 for i in range(1, len(l_words)) if l_words[i] == l_words[i-1])} occurrences)")
    print(f"  Stutter Ratio: Voynich is {exact_stutter_v / max(exact_stutter_l, 1e-6):.1f}x MORE REPETITIVE than Latin!")
    print(f"  R^2:      {res_word['train_r2']:+.5f}  |  MSE: {res_word['train_mse']:10.2f}")
    print(f"  Formula:  {res_word['formula']}")
    print(f"  Latency:  {res_word['latency_sec']:.2f}s\n")

    # ==================================================================
    # BATTERY 4: Long-Range Auto-Correlation Decay C(tau) = f(tau)
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [BATTERY 4] Long-Range Auto-Correlation Decay: C(tau) = f(tau)")
    print(" Goal: Fit the exact mathematical decay curve (Power-Law vs Exponential) to test for fractal linguistic memory.")
    print("=" * 115)

    def compute_autocorr(series, max_lag=50):
        s = np.array(series, dtype=np.float64)
        s -= np.mean(s)
        var = np.var(s)
        if var == 0: return np.zeros(max_lag)
        autocorr = []
        for tau in range(1, max_lag + 1):
            c = np.mean(s[:-tau] * s[tau:]) / var
            autocorr.append(c)
        return np.array(autocorr, dtype=np.float64)

    v_chars = [ord(t['char']) for t in tokens[:10000]]
    l_chars = [ord(c) for c in latin_tokens[:10000]]

    max_lags = 30
    c_voynich = compute_autocorr(v_chars, max_lag=max_lags)
    c_latin = compute_autocorr(l_chars, max_lag=max_lags)

    taus = np.arange(1, max_lags + 1, dtype=np.float64)
    X_tau = np.column_stack([
        taus,
        np.log(taus),
        1.0 / taus,
        np.exp(-taus / 5.0)
    ])

    for name, ac_curve in [("Voynich Long-Range Auto-Correlation C(tau)", c_voynich), ("Latin Long-Range Auto-Correlation C(tau)", c_latin)]:
        res = run_swarm_search(X_tau, ac_curve, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
        res["battery"] = "Battery 4: Auto-Correlation Decay"
        res["target"] = name
        all_findings.append(res)

        print(f"[{name}]")
        print(f"  C(1)={ac_curve[0]:.4f}, C(5)={ac_curve[4]:.4f}, C(10)={ac_curve[9]:.4f}, C(20)={ac_curve[19]:.4f}")
        print(f"  R^2:      {res['train_r2']:+.5f}  |  MSE: {res['train_mse']:10.6f}")
        print(f"  Formula:  {res['formula']}")
        print(f"  Latency:  {res['latency_sec']:.2f}s\n")

    # ==================================================================
    # BATTERY 5: Polar Coordinate Harmonic Symmetries on Astronomical Folios (f67-f68)
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [BATTERY 5] Polar Coordinate Harmonic Symmetries on Astronomical Folios (f67-f68)")
    print(" Goal: Test if text inscribed along concentric rings exhibits discrete rotational harmonic symmetry.")
    print("=" * 115)

    f67_lines = [l_toks for key, l_toks in line_tokens.items() if key[0] == 67]
    f67_ring_chars = []
    f67_ring_angles = []
    f67_ring_radii = []

    for r_idx, r_toks in enumerate(f67_lines):
        N_r = len(r_toks)
        if N_r < 10: continue
        for idx, t in enumerate(r_toks):
            theta = 2 * np.pi * (idx / N_r)
            f67_ring_chars.append(ord(t['char']))
            f67_ring_angles.append(theta)
            f67_ring_radii.append(r_idx + 1)

    y_polar = np.array(f67_ring_chars, dtype=np.float64)
    theta_arr = np.array(f67_ring_angles, dtype=np.float64)
    r_arr = np.array(f67_ring_radii, dtype=np.float64)

    # Test rotational harmonics: k = 12 (zodiac), 16, 24, 28 (lunar), 36 (decans)
    X_polar = np.column_stack([
        r_arr,
        np.sin(12 * theta_arr),
        np.cos(12 * theta_arr),
        np.sin(28 * theta_arr),
        np.cos(28 * theta_arr),
    ])

    res_polar = run_swarm_search(X_polar, y_polar, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
    res_polar["battery"] = "Battery 5: Polar Symmetry"
    res_polar["target"] = "Folio 67 Concentric Wheel Polar Harmonics (k=12 Zodiac, k=28 Lunar)"
    all_findings.append(res_polar)

    print(f"[Folio 67 Concentric Rings: k=12 Zodiac & k=28 Lunar Harmonics]")
    print(f"  R^2:      {res_polar['train_r2']:+.5f}  |  MSE: {res_polar['train_mse']:10.2f}")
    print(f"  Formula:  {res_polar['formula']}")
    print(f"  Latency:  {res_polar['latency_sec']:.2f}s\n")

    # ==================================================================
    # BATTERY 6: Morphological Slot-Grammar Mutual Dependency
    # ==================================================================
    print("\n" + "=" * 115)
    print(" [BATTERY 6] Morphological Slot-Grammar Mutual Dependency")
    print(" Goal: Test whether Prefixes and Suffixes are statistically independent (Slot Machine) or grammatically coupled.")
    print("=" * 115)

    # Segment words into prefix, core, suffix
    # Standard EVA/v101 prefixes: '4o' (qo), '1c' (ch), '2c' (sh), 'o'
    # Suffixes: '89' (ain), '9' (y), 'am', 's'
    prefixes = ['4o', '1c', '2c', 'o', 'd', 's']
    suffixes_list = ['89', '9', 'am', 's', 'ay', 'ey']

    prefix_counts = collections.Counter()
    suffix_counts = collections.Counter()
    joint_counts = collections.defaultdict(int)
    total_segmented = 0

    for w in v_words:
        p_match = None
        for p in prefixes:
            if w.startswith(p):
                p_match = p
                break
        s_match = None
        for s in suffixes_list:
            if w.endswith(s):
                s_match = s
                break
        if p_match and s_match and len(w) >= len(p_match) + len(s_match):
            prefix_counts[p_match] += 1
            suffix_counts[s_match] += 1
            joint_counts[(p_match, s_match)] += 1
            total_segmented += 1

    print(f"[*] Successfully segmented {total_segmented:,} words into (Prefix, Suffix) pairs.")

    # Compute Joint vs Independent Distribution: P(p, s) vs P(p)*P(s)
    pairs = []
    p_joint = []
    p_indep = []
    for p in prefixes:
        for s in suffixes_list:
            prob_j = joint_counts[(p, s)] / max(total_segmented, 1)
            prob_i = (prefix_counts[p] / max(total_segmented, 1)) * (suffix_counts[s] / max(total_segmented, 1))
            pairs.append((p, s))
            p_joint.append(prob_j)
            p_indep.append(prob_i)

    y_joint = np.array(p_joint, dtype=np.float64)
    X_slot = np.column_stack([
        np.array(p_indep, dtype=np.float64),
        np.array(p_indep, dtype=np.float64)**2,
        np.sqrt(np.maximum(p_indep, 0)),
    ])

    res_slot = run_swarm_search(X_slot, y_joint, num_islands=8, island_pop=64, max_gens=60, timeout_sec=15.0)
    res_slot["battery"] = "Battery 6: Slot-Grammar Dependency"
    res_slot["target"] = "Prefix-Suffix Joint Probability P(p, s) vs Independent Product P(p)*P(s)"
    all_findings.append(res_slot)

    print(f"[Prefix-Suffix Slot-Machine Coupling]")
    print(f"  R^2:      {res_slot['train_r2']:+.5f} (1.0 = Pure Independent Slot Machine)")
    print(f"  Formula:  {res_slot['formula']}")
    print(f"  Latency:  {res_slot['latency_sec']:.2f}s\n")

    # ==================================================================
    # CSV EXPORT & WRAPUP
    # ==================================================================
    df = pd.DataFrame(all_findings)
    out_csv = ROOT_DIR / "levitas_comprehensive_findings.csv"
    df.to_csv(out_csv, index=False)
    print("=" * 115)
    print(f"[+] All 6 Batteries Complete! Results saved to: {out_csv}")
    print("=" * 115)

if __name__ == "__main__":
    main()
