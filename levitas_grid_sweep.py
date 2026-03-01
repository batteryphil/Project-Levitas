import collections
import math
import os
import json

def entropy(counts):
    total = sum(counts.values())
    if total == 0: return 0
    ent = 0
    for v in counts.values():
        p = v / total
        ent -= p * math.log2(p)
    return ent

def conditional_entropy(joint_counts, conditioner_counts):
    total = sum(joint_counts.values())
    if total == 0: return 0
    h_zx = entropy(joint_counts)
    h_x = entropy(conditioner_counts)
    return h_zx - h_x

def calculate_synergy(lines, h, w):
    total_samples = 0
    z_counts = collections.Counter()
    x_counts = collections.Counter()
    y_counts = collections.Counter()
    zx_counts = collections.Counter()
    zy_counts = collections.Counter()
    zxy_counts = collections.Counter()
    xy_counts = collections.Counter()

    for line_idx, tokens in enumerate(lines):
        for i, t in enumerate(tokens):
            if i == 0: continue
            z = t['char']
            x = tokens[i-1]['char']
            y = (line_idx % h, i % w)
            
            z_counts[z] += 1
            x_counts[x] += 1
            y_counts[y] += 1
            xy_counts[(x, y)] += 1
            zx_counts[(z, x)] += 1
            zy_counts[(z, y)] += 1
            zxy_counts[(z, x, y)] += 1
            total_samples += 1

    if total_samples == 0: return 0
    h_z = entropy(z_counts)
    h_z_x = conditional_entropy(zx_counts, x_counts)
    h_z_y = conditional_entropy(zy_counts, y_counts)
    h_z_xy = conditional_entropy(zxy_counts, xy_counts)
    
    i_xz = h_z - h_z_x
    i_yz = h_z - h_z_y
    i_xy_z = h_z - h_z_xy
    return i_xy_z - (i_xz + i_yz)

def process_text_to_lines(text):
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        tokens = [{'char': c} for c in line if c.isalnum() or c == ' ']
        if tokens: lines.append(tokens)
    return lines

def run_sweep(name, path):
    if not os.path.exists(path): return
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = process_text_to_lines(text)
    
    print(f"\n[SWEEP: {name}]")
    print(f"{'H':<3} | {'W':<3} | {'Synergy'}")
    print("-" * 20)
    
    results = []
    for h in range(1, 6):
        for w in range(1, 6):
            if h == 1 and w == 1: continue
            syn = calculate_synergy(lines, h, w)
            results.append((h, w, syn))
            if syn > 0.01: # Threshold for display
                 print(f"{h:<3} | {w:<3} | {syn:.4f}")
    
    best = max(results, key=lambda x: x[2])
    print(f"PEAK RESONANCE: H={best[0]}, W={best[1]} (Syn={best[2]:.4f})")

if __name__ == "__main__":
    corpora = {
        "Voynich": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt",
        "Latin": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/vulgate_latin.txt",
        "MHG": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/mhg_parzival.txt",
        "Hebrew": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/hebrew_genesis.txt"
    }
    for name, path in corpora.items():
        run_sweep(name, path)
