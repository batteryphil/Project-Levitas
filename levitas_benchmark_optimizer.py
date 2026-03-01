import collections
import math
import random
import json
import os

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

def calculate_synergy(lines, grid):
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
            y = grid[line_idx % 4][i % 2]
            
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

def optimize_synergy(lines, iterations=500):
    # Initial random grid (4x2, state assignments 0-7)
    # Each cell points to a state index
    grid = [[random.randint(0, 7) for _ in range(2)] for _ in range(4)]
    best_syn = calculate_synergy(lines, grid)
    
    for _ in range(iterations):
        # Mutate one cell
        r, c = random.randint(0, 3), random.randint(0, 1)
        old_val = grid[r][c]
        grid[r][c] = random.randint(0, 7)
        new_syn = calculate_synergy(lines, grid)
        
        if new_syn > best_syn:
            best_syn = new_syn
        else:
            grid[r][c] = old_val
            
    return best_syn, grid

if __name__ == "__main__":
    latin_path = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/vulgate_latin.txt"
    voy_path = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
    
    print("=" * 60)
    print("SYNERGY OPTIMIZATION TEST (FALSIFICATION CHECK)")
    print("-" * 60)
    
    for name, path in [("Latin (Vulgate)", latin_path), ("Voynich (Full)", voy_path)]:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        lines = process_text_to_lines(text)
        
        print(f"Optimizing Grid for {name}...")
        best_syn, grid = optimize_synergy(lines)
        print(f"Best Synergy Found: {best_syn:.4f} bits")
        print(f"Optimized Grid: {grid}")
        print("-" * 60)
