import collections
import math
import re
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
    
    # H(Z|X) = H(Z,X) - H(X)
    h_zx = entropy(joint_counts)
    h_x = entropy(conditioner_counts)
    return h_zx - h_x

def calculate_synergy(lines):
    """
    Synergy S = I(X, Y; Z) - I(X; Z) - I(Y; Z)
    Z = current char
    X = prev char
    Y = (line_idx % 4, char_pos % 2) or similar positional context
    """
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
            # We use a 4x2 grid as the hypothetical mechanical anchor
            y = (line_idx % 4, i % 2)
            
            z_counts[z] += 1
            x_counts[x] += 1
            y_counts[y] += 1
            xy_counts[(x, y)] += 1
            
            zx_counts[(z, x)] += 1
            zy_counts[(z, y)] += 1
            zxy_counts[(z, x, y)] += 1
            total_samples += 1

    if total_samples == 0: return 0, 0, 0, 0

    h_z = entropy(z_counts)
    h_z_x = conditional_entropy(zx_counts, x_counts)
    h_z_y = conditional_entropy(zy_counts, y_counts)
    h_z_xy = conditional_entropy(zxy_counts, xy_counts)
    
    i_xz = h_z - h_z_x
    i_yz = h_z - h_z_y
    i_xy_z = h_z - h_z_xy
    
    synergy = i_xy_z - (i_xz + i_yz)
    return synergy, i_xz, i_yz, i_xy_z

def process_text_to_lines(text):
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        tokens = [{'char': c} for c in line if c.isalnum() or c == ' ']
        if tokens: lines.append(tokens)
    return lines

def run_benchmark(corpora_paths):
    print("=" * 80)
    print(f"{'Corpus':<20} | {'Synergy':<10} | {'I(X;Z)':<10} | {'I(Y;Z)':<10} | {'Total I':<10}")
    print("-" * 80)
    
    for name, path in corpora_paths.items():
        if not os.path.exists(path):
            print(f"{name:<20} | MISSING FILE")
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        
        lines = process_text_to_lines(text)
        syn, i_xz, i_yz, i_total = calculate_synergy(lines)
        
        print(f"{name:<20} | {syn:<10.4f} | {i_xz:<10.4f} | {i_yz:<10.4f} | {i_total:<10.4f}")

def calculate_synergy_with_grid(lines, grid_obj=None):
    """
    If grid_obj is provided, use its state mapping instead of generic (r%4, c%2).
    """
    total_samples = 0
    z_counts = collections.Counter()
    x_counts = collections.Counter()
    y_counts = collections.Counter()
    
    zx_counts = collections.Counter()
    zy_counts = collections.Counter()
    zxy_counts = collections.Counter()
    xy_counts = collections.Counter()

    for line_idx, tokens in enumerate(lines):
        line_chars = "".join([t['char'] for t in tokens])
        for i, t in enumerate(tokens):
            if i == 0: continue
            
            z = t['char']
            x = tokens[i-1]['char']
            
            if grid_obj:
                # Optimized grid state (JSON keys are "(r, c)")
                y_key = f"({line_idx % 4}, {i % 2})"
                y = y_key if y_key in grid_obj else (line_idx % 4, i % 2)
            else:
                # Generic grid state
                y = (line_idx % 4, i % 2)
            
            z_counts[z] += 1
            x_counts[x] += 1
            y_counts[y] += 1
            xy_counts[(x, y)] += 1
            
            zx_counts[(z, x)] += 1
            zy_counts[(z, y)] += 1
            zxy_counts[(z, x, y)] += 1
            total_samples += 1

    if total_samples == 0: return 0, 0, 0, 0

    h_z = entropy(z_counts)
    h_z_x = conditional_entropy(zx_counts, x_counts)
    h_z_y = conditional_entropy(zy_counts, y_counts)
    h_z_xy = conditional_entropy(zxy_counts, xy_counts)
    
    i_xz = h_z - h_z_x
    i_yz = h_z - h_z_y
    i_xy_z = h_z - h_z_xy
    
    synergy = i_xy_z - (i_xz + i_yz)
    return synergy, i_xz, i_yz, i_xy_z

if __name__ == "__main__":
    # Define paths
    paths = {
        "Voynich (Generic)": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt",
        "Latin (Vulgate)": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/vulgate_latin.txt",
        "MHG (Sample)": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/mhg_parzival.txt",
        "Hebrew (Sample)": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/hebrew_genesis.txt",
        "Synthetic (Grid-Reset)": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/synthetic_grid_reset.txt"
    }
    
    run_benchmark(paths)
    
    # Run Voynich with the OPTIMIZED grid
    print("\n" + "-" * 80)
    print("VOYNICH OPTIMIZED GRID CHECK")
    if os.path.exists("rosetta_grid_f67.json"):
        with open("rosetta_grid_f67.json") as f:
            grid_data = json.load(f)
        with open(paths["Voynich (Generic)"], "r") as f:
            text = f.read()
            lines = process_text_to_lines(text)
            syn, i_xz, i_yz, i_total = calculate_synergy_with_grid(lines, grid_data)
            print(f"{'Voynich (Opt Grid)':<20} | {syn:<10.4f} | {i_xz:<10.4f} | {i_yz:<10.4f} | {i_total:<10.4f}")
