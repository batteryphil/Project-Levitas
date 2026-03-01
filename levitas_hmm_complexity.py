import numpy as np
from hmmlearn import hmm
import collections
import re
import math
import os
import sys

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"

def parse_corpus(path):
    tokens = []
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith('#'): continue
            body = re.sub(r'<[^>]*>', '', line)
            for ch in body:
                if ch.isalnum():
                    tokens.append(ch)
                elif ch in '.,':
                    if tokens and tokens[-1] != ' ':
                        tokens.append(' ')
    return tokens

def compute_metrics(tokens):
    """Computes BE and Det@95."""
    if not tokens: return 0, 0
    bigrams = collections.defaultdict(list)
    for i in range(len(tokens)-1):
        bigrams[tokens[i]].append(tokens[i+1])
    
    entropies = []
    total_det = 0
    for char, next_chars in bigrams.items():
        counts = collections.Counter(next_chars)
        total = sum(counts.values())
        probs = [c/total for c in counts.values()]
        e = -sum(p * math.log2(p) for p in probs if p > 0)
        entropies.append(e)
        
        # Det@95
        sorted_probs = sorted(probs, reverse=True)
        acc = 0
        for i, p in enumerate(sorted_probs):
            acc += p
            if acc >= 0.95:
                total_det += (i + 1)
                break
                
    avg_be = sum(entropies) / len(entropies) if entropies else 0
    avg_det = total_det / len(bigrams) if bigrams else 0
    return avg_be, avg_det

def run_hmm_complexity():
    print("=" * 70)
    print("PHASE 9: HMM STATE COMPLEXITY MAPPING")
    print("-" * 70)
    
    tokens = parse_corpus(VOY_PATH)
    vocab = sorted(list(set(tokens)))
    char_to_idx = {c: i for i, c in enumerate(vocab)}
    idx_to_char = {i: c for i, c in enumerate(vocab)}
    
    encoded = np.array([char_to_idx[t] for t in tokens]).reshape(-1, 1)
    
    voy_be, voy_det = compute_metrics(tokens)
    print(f"VOYNICH BASELINE | BE: {voy_be:.3f} | Det@95: {voy_det:.2f}")
    print("-" * 70)
    print(f"{'K (States)':<10} | {'BE':<10} | {'Det@95':<10} | {'Error Delta'}")
    print("-" * 70)
    
    for K in [1, 2, 5, 10, 20]:
        # Train HMM
        model = hmm.CategoricalHMM(n_components=K, n_iter=100, random_state=42)
        model.fit(encoded)
        
        # Generate sequence of same length
        gen_indices, _ = model.sample(len(tokens))
        gen_tokens = [idx_to_char[i] for i in gen_indices.flatten()]
        
        gen_be, gen_det = compute_metrics(gen_tokens)
        delta = abs(gen_be - voy_be) + abs(gen_det - voy_det) / 10.0 # Weighted delta
        
        print(f"{K:<10} | {gen_be:<10.3f} | {gen_det:<10.2f} | {delta:.4f}")
        
if __name__ == "__main__":
    run_hmm_complexity()
