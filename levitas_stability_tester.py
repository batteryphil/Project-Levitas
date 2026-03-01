import collections
import re
import math
import os
import sys
import json

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/vulgate_latin.txt"

def load_trigram_model():
    with open(LATIN_PATH) as f:
        text = f.read().lower()
        chars = [c if c.isalnum() or c == ' ' else ' ' for c in text]
        text = "".join(chars)
        words = text.split()
    
    trigrams = collections.defaultdict(int)
    total = 0
    for word in words:
        w = ' ' + word + ' '
        for i in range(len(w)-2):
            trigrams[(w[i], w[i+1], w[i+2])] += 1
            total += 1
            
    # Smoothing
    vocab = set(c for t in trigrams.keys() for c in t)
    total_trigrams = total + len(vocab)**3
    model = collections.defaultdict(lambda: math.log10(1/total_trigrams))
    for k, v in trigrams.items():
        model[k] = math.log10((v + 1) / total_trigrams)
    return model

def parse_voynich_folio(target_folio):
    lines = []
    with open(VOY_PATH) as f:
        for line_raw in f:
            match = re.search(r'<(\d+)[^>]*>', line_raw)
            if match and int(match.group(1)) == target_folio:
                body = re.sub(r'<[^>]*>', '', line_raw).strip()
                tokens = []
                c_idx = 0
                for ch in body:
                    if ch.isalnum():
                        tokens.append({'char': ch, 'pos': c_idx})
                        c_idx += 1
                    elif ch in '.,':
                        if tokens and tokens[-1]['char'] != ' ':
                            tokens.append({'char': ' ', 'pos': c_idx})
                            c_idx += 1
                if tokens: lines.append(tokens)
    return lines

def load_grid(path):
    with open(path) as f:
        raw_grid = json.load(f)
    # Convert keys back to tuples
    return {eval(k): v for k, v in raw_grid.items()}

def run_stability_test(grid_path, folios):
    grid = load_grid(grid_path)
    model = load_trigram_model()
    print("=" * 70)
    print("FIXED-PARAMETER STABILITY TEST (PHASE 10)")
    print("-" * 70)
    print(f"{'Folio':<10} | {'Log-Prob':<15} | {'Snippet'}")
    print("-" * 70)
    
    for folio_num in folios:
        lines = parse_voynich_folio(folio_num)
        total_log_prob = 0
        tokens_count = 0
        decoded_all = []
        
        for tokens in lines:
            decoded_line = ""
            for i, t in enumerate(tokens):
                # FIXED H=4, W=2 (8 cells)
                # We use the previous line count as height if available, else 0
                cell_id = (0, t['pos'] % 2) # Simplified 2x1 for this test to match stability logic
                char = t['char']
                
                # Apply Fixed Grid
                if cell_id in grid and char in grid[cell_id]:
                    decoded_line += grid[cell_id][char]
                else:
                    decoded_line += char # Pass-through
            
            decoded_all.append(decoded_line)
            # Score line
            w = ' ' + decoded_line + ' '
            for j in range(len(w)-2):
                total_log_prob += model[(w[j], w[j+1], w[j+2])]
                tokens_count += 1
        
        avg_lp = total_log_prob / tokens_count if tokens_count > 0 else -100
        snippet = " ".join(decoded_all[0].split()[:5]) if decoded_all else "N/A"
        print(f"{folio_num:<10} | {avg_lp:<15.4f} | {snippet}")

# Dummy/Simulated Grid from Folio 67 convergence (Simplified)
FIXED_GRID = {
    (0, 0): {'o': 'a', '8': 's', '9': 'm', 'a': 'e', 'p': 'i', 's': 'n', 't': 'u'},
    (0, 1): {'o': 'e', '8': 'r', '9': 'a', 'a': 'i', 'p': 'o', 's': 't', 't': 'l'}
}

if __name__ == "__main__":
    run_stability_test("rosetta_grid_f67.json", [67, 68, 69, 70])
