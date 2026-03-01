import collections
import re
import os
import random
import math
import numpy as np
import sys
import json

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/vulgate_latin.txt"
DICT_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/latin_dictionary.txt"

TARGET_FOLIO = 67
H_MOD, W_MOD = 4, 2 # 8 physical cells
ALPHABET = "abcdefghijklmnopqrstuvwxyz"

import levitas_lexical_filter

def parse_lines_with_2d_context(text):
    lines_data = []
    for line_raw in text.splitlines():
        if not line_raw.strip() or line_raw.startswith('#'): continue
        match = re.search(r'<(\d+)[^.]*\.([^>]+)>', line_raw)
        if match:
            folio_num = int(match.group(1))
            line_str = match.group(2)
            line_num = int(line_str) if line_str.isdigit() else sum(ord(c) for c in line_str)
        else:
            folio_num, line_num, line_str = 0, 0, "0"
            
        body = re.sub(r'<[^>]*>', '', line_raw)
        char_idx = 0
        tokens = []
        for ch in body:
            if ch.isalnum(): 
                tokens.append({'char': ch, 'line': line_num, 'pos': char_idx})
                char_idx += 1
            elif ch in '.,':
                if tokens and tokens[-1]['char'] != ' ':
                    tokens.append({'char': ' ', 'line': line_num, 'pos': char_idx})
                    char_idx += 1
        if tokens:
            lines_data.append(tokens)
    return lines_data

def load_ngrams():
    with open(LATIN_PATH) as f:
        text = f.read().lower()
        chars = [c if c.isalnum() or c == ' ' else ' ' for c in text]
        text = "".join(chars)
        words = text.split()
    
    bigrams = collections.defaultdict(lambda: collections.defaultdict(int))
    trigrams = collections.defaultdict(lambda: collections.defaultdict(int))
    
    for word in words:
        w = ' ' + word + ' '
        for i in range(len(w)-1):
            bigrams[w[i]][w[i+1]] += 1
        for i in range(len(w)-2):
            trigrams[(w[i], w[i+1])][w[i+2]] += 1
            
    bi_probs = {k: {nk: math.log10(nv/sum(v.values())) for nk, nv in v.items()} for k, v in bigrams.items()}
    tri_probs = {k: {nk: math.log10(nv/sum(v.values())) for nk, nv in v.items()} for k, v in trigrams.items()}
    
    # Load Dictionary
    with open(DICT_PATH) as f:
        dictionary = set(line.strip() for line in f if len(line.strip()) >= 3)
        
    return bi_probs, tri_probs, dictionary

bi_probs, tri_probs, latin_dict = load_ngrams()

class RosettaIndividual:
    def __init__(self, glyphs_per_cell, mapping=None):
        self.glyphs_per_cell = glyphs_per_cell
        if mapping:
            self.mapping = mapping
        else:
            self.mapping = self._random_init()
        self.fitness = -float('inf')

    def _random_init(self):
        m = {}
        for cell_id, glyphs in self.glyphs_per_cell.items():
            cell_map = {}
            latin_shuffled = list(ALPHABET)
            random.shuffle(latin_shuffled)
            glyphs_list = list(glyphs)
            for i, g in enumerate(glyphs_list):
                cell_map[g] = latin_shuffled[i % len(latin_shuffled)]
            
            if cell_id == (0, 0) and 'o' in cell_map:
                cell_map['o'] = random.choice('aeiou')
            if '9' in cell_map:
                cell_map['9'] = random.choice('sma')
                
            m[cell_id] = cell_map
        return m

    def mutate(self):
        cell_id = random.choice(list(self.mapping.keys()))
        if not self.mapping[cell_id]: return
        glyph = random.choice(list(self.mapping[cell_id].keys()))
        
        if cell_id == (0, 0) and glyph == 'o':
            self.mapping[cell_id][glyph] = random.choice('aeiou')
        elif glyph == '9':
            self.mapping[cell_id][glyph] = random.choice('sma')
        else:
            self.mapping[cell_id][glyph] = random.choice(ALPHABET)

    def decrypt(self, lines):
        decrypted_lines = []
        for line in lines:
            dec_chars = []
            for t in line:
                if t['char'] == ' ':
                    dec_chars.append(' ')
                    continue
                cell = (t['line'] % H_MOD, t['pos'] % W_MOD)
                m = self.mapping.get(cell, {})
                char = m.get(t['char'], '?')
                dec_chars.append(char)
            decrypted_lines.append("".join(dec_chars))
        return decrypted_lines

    def calculate_fitness(self, lines):
        total_log_prob = 0
        dec_lines = self.decrypt(lines)
        
        # 1. Trigram Penalty/Prob
        for line_str in dec_lines:
            seq = '  ' + line_str + '  '
            for i in range(len(seq)-2):
                p2, p1, c = seq[i], seq[i+1], seq[i+2]
                if c == ' ' and p1 == ' ': continue
                score = tri_probs.get((p2, p1), {}).get(c, -4.0)
                total_log_prob += score
        
        # 2. Dictionary Bonus
        for line_str in dec_lines:
            words = line_str.split()
            for w in words:
                if w in latin_dict:
                    total_log_prob += 15.0 # High reward for dictionary hits
                    
        self.fitness = total_log_prob
        return total_log_prob

def run_evolution(lines, glyphs_per_cell, generations=500, pop_size=100):
    population = [RosettaIndividual(glyphs_per_cell) for _ in range(pop_size)]
    
    best_ever = None
    best_fitness = -float('inf')
    
    for gen in range(generations):
        for ind in population:
            ind.calculate_fitness(lines)
        
        population.sort(key=lambda x: x.fitness, reverse=True)
        best = population[0]
        
        if best.fitness > best_fitness:
            best_fitness = best.fitness
            best_ever = RosettaIndividual(glyphs_per_cell, {k: v.copy() for k, v in best.mapping.items()})
            best_ever.fitness = best_fitness
        
        if gen % 20 == 0:
            snippet = best.decrypt(lines[:1])[0][:60]
            print(f"Gen {gen:03} | Fit: {best.fitness:10.1f} | Snippet: {snippet}")
            # Identify dictionary matches in snippet
            matches = [w for w in snippet.split() if w in latin_dict]
            if matches: print(f"  Matches: {matches}")

        parents = population[:pop_size//2]
        new_pop = parents[:5] # Elitism
        
        while len(new_pop) < pop_size:
            p1, p2 = random.sample(parents, 2)
            cells_list = list(glyphs_per_cell.keys())
            pivot = random.randint(1, len(cells_list)-1)
            
            child_map = {}
            for i, cell in enumerate(cells_list):
                if i < pivot:
                    child_map[cell] = p1.mapping[cell].copy()
                else:
                    child_map[cell] = p2.mapping[cell].copy()
            
            child = RosettaIndividual(glyphs_per_cell, child_map)
            if random.random() < 0.4:
                child.mutate()
            if random.random() < 0.1:
                child.mutate()
                
            new_pop.append(child)
        population = new_pop

    return best_ever

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rosetta Grid Genetic Optimization")
    parser.add_argument("--folio", type=int, default=TARGET_FOLIO)
    parser.add_argument("--h", type=int, default=H_MOD)
    parser.add_argument("--w", type=int, default=W_MOD)
    parser.add_argument("--gen", type=int, default=500)
    args = parser.parse_args()

    # Override defaults
    TARGET_FOLIO = args.folio
    H_MOD = args.h
    W_MOD = args.w

    print("=" * 70)
    print(f"PHASE 17: ROSETTA GRID GENETIC OPTIMIZATION (Target: Folio {TARGET_FOLIO})")
    print(f"Aperture: {W_MOD}x{H_MOD} | Dictionary: {len(latin_dict)} words")
    print("-" * 70)
    
    with open(VOY_PATH) as f:
        raw_text = f.read()
    
    f_lines_raw = []
    for line in raw_text.splitlines():
        if f'<{TARGET_FOLIO}' in line:
            f_lines_raw.append(line)
    
    if not f_lines_raw:
        print(f"Error: Folio {TARGET_FOLIO} not found.")
        sys.exit(1)

    v_lines = parse_lines_with_2d_context("\n".join(f_lines_raw))
    
    glyphs_per_cell = collections.defaultdict(set)
    for line in v_lines:
        for t in line:
            if t['char'] != ' ':
                cell = (t['line'] % H_MOD, t['pos'] % W_MOD)
                glyphs_per_cell[cell].add(t['char'])
    
    print(f"Loaded {len(v_lines)} lines. Initiating evolution...")
    best_grid = run_evolution(v_lines, glyphs_per_cell, generations=args.gen)
    
    # Save Grid for Stability Testing
    grid_export = {str(k): v for k, v in best_grid.mapping.items()}
    with open("rosetta_grid_f67.json", "w") as f:
        json.dump(grid_export, f, indent=2)
    print(f"\n[SYSTEM] Rosetta Grid exported to rosetta_grid_f67.json")
    
    print("\n" + "=" * 70)
    print("OPTIMIZATION COMPLETE")
    print("-" * 70)
    print("Final Decryption Pass (Raw Syllables):")
    final_dec = best_grid.decrypt(v_lines)
    for i, line in enumerate(final_dec[:15]):
        print(f"L{i+1:02} (Raw): {line}")
        
    print("\n" + "-" * 70)
    print("Final Decryption Pass (Lexical Filter Applied):")
    all_clean_text = []
    for i, line in enumerate(final_dec):
        clean_line = levitas_lexical_filter.lexical_anchor_filter(line)
        all_clean_text.append(clean_line)
        if i < 15:
            print(f"L{i+1:02} (Clean): {clean_line}")
    
    # Export for audit
    with open("folio_67_full_decryption.txt", "w") as f:
        f.write("\n".join(all_clean_text))
    
    # CROSS-FOLIO TEST
    print("\n" + "=" * 70)
    print("CROSS-FOLIO STABILITY DECODING (Folios 68, 69, 70)")
    print("-" * 70)
    for f_num in [68, 69, 70]:
        f_lines_raw = [line for line in raw_text.splitlines() if f'<{f_num}' in line]
        if f_lines_raw:
            v_lines_cf = parse_lines_with_2d_context("\n".join(f_lines_raw))
            cf_dec = best_grid.decrypt(v_lines_cf)
            cf_clean = [levitas_lexical_filter.lexical_anchor_filter(l) for l in cf_dec]
            with open(f"folio_{f_num}_decryption_stable.txt", "w") as f:
                f.write("\n".join(cf_clean))
            print(f"Folio {f_num}: Decoded {len(cf_dec)} lines. Exported to stable text.")
