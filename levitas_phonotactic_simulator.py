import random
import collections
import math
import numpy as np

# Latin-esque Syllable Components
CONSONANTS = "bcdfgklmnprstvx"
VOWELS = "aeiouy"

def generate_syllable():
    # CV or CVC
    if random.random() > 0.3:
        return random.choice(CONSONANTS) + random.choice(VOWELS)
    else:
        return random.choice(CONSONANTS) + random.choice(VOWELS) + random.choice(CONSONANTS)

def generate_word(min_len=3, max_len=10):
    length = random.randint(min_len, max_len)
    word = ""
    while len(word) < length:
        word += generate_syllable()
    return word[:length]

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

def run_simulation(target_tokens=50000, homophone_count=3):
    print("=" * 70)
    print("PHASE 9: PHONOTACTIC LATIN-LIKE SIMULATOR")
    print(f"Goal: Reproduce Voynich signature (BE ~1.05, Det@95 ~4-5)")
    print("-" * 70)
    
    # 1. Base Latin Plaintext
    raw_latin = []
    while len("".join(raw_latin)) < target_tokens:
        raw_latin.append(generate_word())
    
    latin_text = " ".join(raw_latin)[:target_tokens]
    latin_tokens = list(latin_text)
    
    l_be, l_det = compute_metrics(latin_tokens)
    print(f"LATIN BASELINE     | BE: {l_be:.3f} | Det@95: {l_det:.2f}")
    
    # 2. Homophonic Substitution
    # Each character in the alphabet is mapped to multiple symbols
    alphabet = sorted(list(set(latin_tokens)))
    symbols = [f"s{i:02}" for i in range(len(alphabet) * homophone_count)]
    
    mapping = {char: symbols[i*homophone_count : (i+1)*homophone_count] for i, char in enumerate(alphabet)}
    
    cipher_tokens = []
    for char in latin_tokens:
        # Choose a homophone based on some "mechanical" logic
        # For now, just random or cycling
        cipher_tokens.append(random.choice(mapping[char]))
        
    c_be, c_det = compute_metrics(cipher_tokens)
    print(f"HOMOPHONIC CIPHER  | BE: {c_be:.3f} | Det@95: {c_det:.2f}")
    
    # 3. Constrained Homophonic (Position-Dependent)
    # This simulates a "grille" or "stencil" where the available symbol 
    # for a character depends on its position.
    p_cipher_tokens = []
    for i, char in enumerate(latin_tokens):
        # Constraint: Choose homophone based on (i % 8) to simulate the 8-state model
        h_idx = i % homophone_count
        p_cipher_tokens.append(mapping[char][h_idx])
        
    p_be, p_det = compute_metrics(p_cipher_tokens)
    print(f"GRID-CONSTRAINED   | BE: {p_be:.3f} | Det@95: {p_det:.2f}")
    
    print("-" * 70)
    print("VOYNICH TARGET     | BE: ~1.05 | Det@95: ~4-5")
    print("-" * 70)
    print("Conclusion: If GRID-CONSTRAINED matches Voynich, the hypothesis is verified.")

if __name__ == "__main__":
    run_simulation()
