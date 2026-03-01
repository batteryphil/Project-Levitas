import numpy as np
import collections
import re
import os

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/latin_control_large.txt"

def get_words(path):
    if not os.path.exists(path): return []
    with open(path) as f:
        text = f.read()
        # Remove metadata tags
        text = re.sub(r'<[^>]*>', '', text)
        # Tokenize by whitespace and non-alphanumerics
        words = re.findall(r'\b\w+\b', text.lower())
    return words

def heaps_analysis(words, step=1000):
    n_tokens = []
    n_vocab = []
    vocab = set()
    for i in range(0, len(words), step):
        batch = words[i:i+step]
        vocab.update(batch)
        n_tokens.append(i + len(batch))
        n_vocab.append(len(vocab))
    
    # Fit Heaps' Law: V = K * N^beta  => log(V) = log(K) + beta * log(N)
    log_N = np.log(n_tokens)
    log_V = np.log(n_vocab)
    beta, log_K = np.polyfit(log_N, log_V, 1)
    return n_tokens, n_vocab, beta, np.exp(log_K)

def run_heaps():
    print("=" * 70)
    print("PHASE 9: HEAPS' LAW & COMPLEXITY SCALING")
    print("-" * 70)
    
    voy_words = get_words(VOY_PATH)
    lat_words = get_words(LATIN_PATH)
    
    print(f"Voynich: {len(voy_words)} words")
    print(f"Latin:   {len(lat_words)} words")
    print("-" * 70)
    
    # Analyze Voynich
    v_n, v_v, v_beta, v_K = heaps_analysis(voy_words)
    print(f"VOYNICH | Beta (Scaling): {v_beta:.4f} | K: {v_K:.2f}")
    
    # Analyze Latin
    l_n, l_v, l_beta, l_K = heaps_analysis(lat_words)
    print(f"LATIN   | Beta (Scaling): {l_beta:.4f} | K: {l_K:.2f}")
    
    # Random Baseline (Shuffle Voynich words)
    shuffled_voy = list(voy_words)
    np.random.shuffle(shuffled_voy)
    s_n, s_v, s_beta, s_K = heaps_analysis(shuffled_voy)
    print(f"SHUFFLE | Beta (Scaling): {s_beta:.4f} | K: {s_K:.2f}")
    
    print("-" * 70)
    if v_beta < l_beta:
        print(">>> RESULT: LOWER SCALING RATE DETECTED <<<")
        print("Voynich vocabulary saturates faster than Latin, suggesting a more constrained")
        print("generative process or a limited lexicon (typical of cipher or mechanical devices).")
    else:
        print(">>> RESULT: NORMAL OR HIGHER SCALING RATE <<<")
        print("Voynich vocabulary scaling is similar to or higher than natural language.")

if __name__ == "__main__":
    run_heaps()
