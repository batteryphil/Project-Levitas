import collections
import re
import os
import math
import numpy as np

import sys

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/homophonic_latin.txt"
if not os.path.exists(LATIN_PATH):
    LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/homophonic_latin_193k.txt"

# Default params
TARGET_FOLIO = 67
RAIL_COLS = {0, 76, 92}

def parse_with_2d_context(text):
    tokens = []
    for line_raw in text.splitlines():
        if not line_raw.strip() or line_raw.startswith('#'): continue
        
        match = re.search(r'<(\d+)[^.]*\.([^>]+)>', line_raw)
        if match:
            folio_num = int(match.group(1))
            line_str = match.group(2)
            if line_str.isdigit():
                line_num = int(line_str)
            else:
                line_num = sum(ord(c) for c in line_str)
        else:
            folio_num, line_num = 0, 0
            
        body = re.sub(r'<[^>]*>', '', line_raw)
        char_idx = 0
        for ch in body:
            if ch.isalnum(): 
                tokens.append({'char': ch, 'folio': folio_num, 'line': line_num, 'pos': char_idx})
                char_idx += 1
            elif ch in '.,':
                if tokens and tokens[-1]['char'] != ' ': 
                    tokens.append({'char': ' ', 'folio': folio_num, 'line': line_num, 'pos': char_idx})
                    char_idx += 1
    return tokens

def shannon_entropy(p_dist):
    """Calculates Shannon Entropy of a distribution. Lower and spikier is better."""
    entropy = 0.0
    for p in p_dist.values():
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def extract_latin_distribution():
    with open(LATIN_PATH) as f:
        latin_text = f.read().replace(' ', '').lower()
        latin_chars = [c for c in latin_text if c.isalnum()]
        counts = collections.Counter(latin_chars)
        total = sum(counts.values())
        return {k: v / total for k, v in counts.items()}

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Levitas 2D Aperture Brute-Force")
    parser.add_argument("input_file", nargs="?", default=VOY_PATH)
    parser.add_argument("--start-folio", type=int, default=None)
    parser.add_argument("--end-folio", type=int, default=None)
    parser.add_argument("--folio", type=int, default=None)
    args = parser.parse_args()

    input_file = args.input_file
    is_voynich = (input_file == VOY_PATH)
    
    start_folio = args.start_folio
    end_folio = args.end_folio
    if args.folio:
        start_folio = end_folio = args.folio
    elif is_voynich and start_folio is None:
        start_folio = end_folio = TARGET_FOLIO

    print(f"Loading input: {input_file}")
    if is_voynich:
        print(f"Filtering Folios: {start_folio} to {end_folio}")

    with open(input_file) as f:
        tokens = parse_with_2d_context(f.read())
        
    if is_voynich:
        folio_tokens = [t for t in tokens if start_folio <= t['folio'] <= end_folio]
        cleaned_tokens = [t for t in folio_tokens if t['pos'] not in RAIL_COLS and t['char'] != ' ']
    else:
        cleaned_tokens = [t for t in tokens if t['char'] != ' ']
    
    if not cleaned_tokens:
        print("Error: No tokens found for specified range.")
        sys.exit(1)

    latin_dist = extract_latin_distribution()
    
    print("=" * 70)
    print(f"EXPERIMENT 14: 2D Dimensional Brute-Force 'Aperture Search'")
    print(f"Data size: {len(cleaned_tokens)} tokens")
    print("-" * 70)
    
    results = []
    
    # Brute force H and W
    for H in range(1, 10):
        for W in range(1, 10):
            cells = collections.defaultdict(list)
            for t in cleaned_tokens:
                coord = (t['line'] % H, t['pos'] % W)
                cells[coord].append(t['char'])
                
            total_intensity = 0.0
            valid_cells = 0
            for coord, chars in cells.items():
                if len(chars) < 50: continue 
                
                sample_size = 500
                test_chars = chars[:sample_size]
                
                counts = collections.Counter(test_chars)
                actual_size = len(test_chars)
                max_prob = max(counts.values()) / actual_size
                
                total_intensity += max_prob
                valid_cells += 1
                
            if valid_cells > 0:
                avg_max_p = total_intensity / valid_cells
                results.append((avg_max_p, H, W, valid_cells))
            
    results.sort(key=lambda x: x[0], reverse=True)
    
    print(f"{'H':<4} | {'W':<4} | {'Avg Max-Char Prob':<20} | {'Valid Cells'}")
    print("-" * 70)
    for i in range(min(len(results), 20)):
        max_p, h, w, cells = results[i]
        print(f"  {h:<2} |  {w:<2} |  {max_p:>15.5f}       |  {cells}")
        
    best_h, best_w = results[0][1], results[0][2]
    print(f"\n>>> 2D DIMENSIONAL RESONANCE DETECTED AT: (H={best_h}, W={best_w}) <<<")
    print(f"    This suggests physical dimensions of {best_w}x{best_h} for this section.")
