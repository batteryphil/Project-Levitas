import collections
import re
import numpy as np
from itertools import combinations

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"

# The 6 gear swap boundaries we found in Exp 9.
# We'll define the continuous "Mechanism Blocks" based on these.
SWAP_FOLIOS = [19, 36, 45, 52, 57, 69]

def parse_with_2d_context(text):
    tokens = []
    for line_raw in text.splitlines():
        if not line_raw.strip() or line_raw.startswith('#'): continue
        
        match = re.search(r'<(\d+)[rvA-Z]*\.(\d+)>', line_raw)
        if match:
            folio_num = int(match.group(1))
            line_num = int(match.group(2))
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

def extract_mechanism_blocks(tokens, boundaries):
    """
    Groups the tokens into continuous 'blocks' separated by the gear swaps.
    """
    blocks = collections.defaultdict(list)
    b_idx = 0
    next_boundary = boundaries[b_idx] if b_idx < len(boundaries) else float('inf')
    
    for t in tokens:
        if t['folio'] >= next_boundary:
            b_idx += 1
            next_boundary = boundaries[b_idx] if b_idx < len(boundaries) else float('inf')
            
        # Naming the blocks: Block 0 (f1-18), Block 1 (f19-35), etc.
        blocks[b_idx].append(t)
        
    return blocks

def build_2d_transition_rules(block_tokens):
    """
    Builds the deterministic ruleset for a specific hardware block.
    Returns a dict of state -> next_char
    """
    counts = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(len(block_tokens) - 1):
        t_curr = block_tokens[i]
        t_next = block_tokens[i+1]
        
        # We model the state (T_prev, Line, Pos)
        state = (t_curr['char'], t_curr['line'], t_curr['pos'])
        counts[state][t_next['char']] += 1
        
    rules = {state: max(succs, key=succs.get) for state, succs in counts.items()}
    return rules

def jaccard_similarity(rules_a, rules_b):
    """
    Measures how identical two 2D mechanisms are.
    A match means: Same context (Char, Line, Pos) predicting the EXACT same next Character.
    """
    set_a = set(rules_a.items())
    set_b = set(rules_b.items())
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a) + len(set_b) - intersection
    
    if union == 0: return 0.0
    return intersection / union

if __name__ == "__main__":
    print("Reading Voynich corpus...")
    with open(VOY_PATH) as f:
        tokens = parse_with_2d_context(f.read())
        
    print("=" * 70)
    print("EXPERIMENT 10: Clustering 2D Mechanisms (Plate Reuse Detection)")
    
    blocks = extract_mechanism_blocks(tokens, SWAP_FOLIOS)
    
    # Define the block ranges for display
    block_names = []
    prev = 1
    for b_idx in range(len(SWAP_FOLIOS) + 1):
        end = SWAP_FOLIOS[b_idx] - 1 if b_idx < len(SWAP_FOLIOS) else tokens[-1]['folio']
        name = f"Block {b_idx} (f{prev}-{end})"
        block_names.append(name)
        prev = end + 1

    print("Extracting physical 2D rulesets for continuous blocks:")
    block_rules = {}
    for b_idx, name in enumerate(block_names):
        b_toks = blocks[b_idx]
        if not b_toks: continue
        rules = build_2d_transition_rules(b_toks)
        block_rules[b_idx] = rules
        print(f"  {name}: {len(rules):>5} unique mechanical states mapped")
        
    print("-" * 70)
    print("Pairwise Jaccard Similarity (Hardware Plate Comparison):")
    
    similarities = []
    
    for (i, rules_i), (j, rules_j) in combinations(block_rules.items(), 2):
        sim = jaccard_similarity(rules_i, rules_j)
        similarities.append((sim, i, j))
        
    # Sort by highest similarity
    similarities.sort(reverse=True)
    
    for sim, i, j in similarities:
        # Flag unusually high similarities
        status = "<<< HARDWARE REUSE DETECTED >>>" if sim > 0.15 else ""
        print(f"  {block_names[i]:<18} <-> {block_names[j]:<19} | Overlap: {sim:>6.2%} {status}")
