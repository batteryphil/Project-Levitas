import collections
import re
import math
import os

FILES = {
    "V101": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt",
    "ZL": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_ZL.txt",
    "Interlinear": "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_interlinear_full.txt"
}

def parse_corpus(path):
    tokens = []
    if not os.path.exists(path) or os.path.getsize(path) < 100: return []
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith('#'): continue
            # Basic parsing: extract alpha characters grouped by folio metadata if present
            body = re.sub(r'<[^>]*>', '', line)
            for ch in body:
                if ch.isalnum():
                    tokens.append(ch)
                elif ch in '.,':
                    if tokens and tokens[-1] != ' ':
                        tokens.append(' ')
    return tokens

def compute_metrics(tokens):
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

def run_check():
    print("=" * 70)
    print("PHASE 9: CROSS-TRANSCRIPTION VALIDATION")
    print("-" * 70)
    print(f"{'Source':<15} | {'BE':<10} | {'Det@95':<10} | {'Tokens'}")
    print("-" * 70)
    for name, path in FILES.items():
        tokens = parse_corpus(path)
        if not tokens:
            print(f"{name:<15} | {'MISSING':<10} | {'N/A':<10} | 0")
            continue
        be, det = compute_metrics(tokens)
        print(f"{name:<15} | {be:<10.3f} | {det:<10.2f} | {len(tokens)}")

if __name__ == "__main__":
    run_check()
