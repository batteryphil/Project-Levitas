import collections
import re
import math
import numpy as np
import os

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"

def parse_with_metadata(path):
    tokens = []
    with open(path) as f:
        for line_raw in f:
            if not line_raw.strip() or line_raw.startswith('#'): continue
            
            match = re.search(r'<(\d+)[^.]*\.([^>]+)>', line_raw)
            if match:
                folio = int(match.group(1))
                line_str = match.group(2)
                line_num = int(line_str) if line_str.isdigit() else sum(ord(c) for c in line_str)
            else:
                folio, line_num = 0, 0
            
            body = re.sub(r'<[^>]*>', '', line_raw)
            char_idx = 0
            for ch in body:
                if ch.isalnum():
                    tokens.append({'char': ch.lower(), 'folio': folio, 'line': line_num, 'pos': char_idx})
                    char_idx += 1
                elif ch in '.,':
                    if tokens and tokens[-1]['char'] != ' ':
                        tokens.append({'char': ' ', 'folio': folio, 'line': line_num, 'pos': char_idx})
                        char_idx += 1
    return tokens

def conditional_entropy(tokens, conditioners):
    """Computes H(Char | Conditioner1, Conditioner2, ...)"""
    counts = collections.defaultdict(collections.Counter)
    for i in range(1, len(tokens)):
        key_list = []
        for c in conditioners:
            if c == 'prev':
                key_list.append(tokens[i-1]['char'])
            else:
                key_list.append(tokens[i][c])
        key = tuple(key_list)
        counts[key][tokens[i]['char']] += 1
    
    total_samples = len(tokens) - 1
    cond_h = 0
    for key, counter in counts.items():
        sub_total = sum(counter.values())
        prob_key = sub_total / total_samples
        sub_probs = [c/sub_total for c in counter.values()]
        sub_h = -sum(p * math.log2(p) for p in sub_probs if p > 0)
        cond_h += prob_key * sub_h
    return cond_h

def run_decomposition():
    print("=" * 70)
    print("PHASE 9: PARTIAL INFORMATION DECOMPOSITION (PROXY)")
    print("-" * 70)
    
    tokens = parse_with_metadata(VOY_PATH)
    if not tokens:
        print("Error: No tokens parsed.")
        return
    
    # Baseline Unigram Entropy
    all_chars = [t['char'] for t in tokens]
    c_counts = collections.Counter(all_chars)
    p_all = [c/len(all_chars) for c in c_counts.values()]
    h_base = -sum(p * math.log2(p) for p in p_all if p > 0)
    
    print(f"Base Unigram Entropy H(C)         : {h_base:.4f} bits")
    print("-" * 70)
    
    # 1. Bigram: H(C_next | C_prev)
    h_markov = conditional_entropy(tokens, ['prev'])
    ig_markov = h_base - h_markov
    
    # 2. Line: H(C_next | Line)
    h_line = conditional_entropy(tokens, ['line'])
    ig_line = h_base - h_line
    
    # 3. Position: H(C_next | Pos)
    h_pos = conditional_entropy(tokens, ['pos'])
    ig_pos = h_base - h_pos
    
    # 4. Joint: H(C_next | C_prev, Line, Pos)
    h_joint = conditional_entropy(tokens, ['prev', 'line', 'pos'])
    ig_joint = h_base - h_joint
    
    print(f"{'Source of Information (Conditioner)':<40} | {'Cond Entropy':<12} | {'Info Gain'}")
    print("-" * 70)
    print(f"{'Previous Token (Markov)':<40} | {h_markov:<12.4f} | {ig_markov:.4f}")
    print(f"{'Vertical Index (Line)':<40} | {h_line:<12.4f} | {ig_line:.4f}")
    print(f"{'Horizontal Index (Pos)':<40} | {h_pos:<12.4f} | {ig_pos:.4f}")
    print(f"{'Joint (Markov + Line + Pos)':<40} | {h_joint:<12.4f} | {ig_joint:.4f}")
    
    print("-" * 70)
    synergy = ig_joint - (ig_markov + ig_line + ig_pos)
    print(f"Synergistic/Redundant Info Delta : {synergy:+.4f} bits")
    if synergy > 0:
        print(">>> RESULT: POSITIVE SYNERGY DETECTED <<<")
        print("The combination of state indices provides more information than the sum of parts.")
        print("This points towards a structured generative device (template/machine).")
    else:
        print(">>> RESULT: REDUNDANCY DOMINATES <<<")
        print("The features overlap in predictive power, suggesting a single unified process.")

if __name__ == "__main__":
    run_decomposition()
