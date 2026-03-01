import numpy as np
import collections
import re
import math
import os
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from sklearn.preprocessing import StandardScaler

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/homophonic_latin.txt"

def parse_corpus(path, clean=True):
    tokens = []
    if not os.path.exists(path): return []
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith('#'): continue
            body = re.sub(r'<[^>]*>', '', line)
            for ch in body:
                if ch.isalnum():
                    tokens.append(ch.lower())
                elif ch in '.,':
                    if tokens and tokens[-1] != ' ':
                        tokens.append(' ')
    return tokens

def extract_features(tokens):
    """Extracts structural features from a token stream."""
    if len(tokens) < 100: return None
    
    # 1. Unigram Entropy
    counts = collections.Counter(tokens)
    total = sum(counts.values())
    probs = [c/total for c in counts.values()]
    u_ent = -sum(p * math.log2(p) for p in probs if p > 0)
    
    # 2. Branching Entropy (BE)
    bigrams = collections.defaultdict(list)
    for i in range(len(tokens)-1):
        bigrams[tokens[i]].append(tokens[i+1])
    
    entropies = []
    total_det = 0
    for char, next_chars in bigrams.items():
        c_counts = collections.Counter(next_chars)
        c_total = sum(c_counts.values())
        c_probs = [c/c_total for c in c_counts.values()]
        e = -sum(p * math.log2(p) for p in c_probs if p > 0)
        entropies.append(e)
        
        # Det@95
        sorted_probs = sorted(c_probs, reverse=True)
        acc = 0
        for i, p in enumerate(sorted_probs):
            acc += p
            if acc >= 0.95:
                total_det += (i + 1)
                break
    
    avg_be = sum(entropies) / len(entropies) if entropies else 0
    avg_det = total_det / len(bigrams) if bigrams else 0
    
    # 3. Zipf slope (log-frequency vs log-rank)
    freqs = sorted(counts.values(), reverse=True)
    if len(freqs) > 10:
        x = np.log(np.arange(1, len(freqs) + 1))
        y = np.log(freqs)
        slope, _ = np.polyfit(x, y, 1)
    else:
        slope = 0
        
    return [u_ent, avg_be, avg_det, slope, len(counts) / len(tokens)]

def build_dataset(window_size=2000):
    X = []
    y = []
    
    # Voynich
    voy_tokens = parse_corpus(VOY_PATH)
    for i in range(0, len(voy_tokens) - window_size, window_size // 2):
        feat = extract_features(voy_tokens[i:i+window_size])
        if feat:
            X.append(feat)
            y.append(0) # Voynich
            
    # Latin
    latin_tokens = parse_corpus(LATIN_PATH)
    for i in range(0, len(latin_tokens) - window_size, window_size // 2):
        feat = extract_features(latin_tokens[i:i+window_size])
        if feat:
            X.append(feat)
            y.append(1) # Latin
            
    return np.array(X), np.array(y)

def run_classification():
    print("=" * 70)
    print("PHASE 9: DISCRIMINATIVE CLASSIFICATION (Voynich vs Latin)")
    print("-" * 70)
    
    X, y = build_dataset()
    if len(X) == 0:
        print("Error: Dataset empty.")
        return
        
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)
    
    clf = LogisticRegression()
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    f1 = f1_score(y_test, y_pred)
    
    print(f"Dataset Size: {len(X)} samples")
    print(f"F1-Score: {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Voynich", "Latin"]))
    
    # Feature Importance
    print("\nFeature Importance (Coefficients):")
    feature_names = ["Unigram Ent", "Branching Ent", "Det@95", "Zipf Slope", "Type/Token Ratio"]
    for name, coef in zip(feature_names, clf.coef_[0]):
        print(f"  {name:<20}: {coef:>8.4f}")
        
    if f1 > 0.95:
        print("\n>>> RESULT: FORMAL SEPARABILITY DETECTED <<<")
        print("The manuscript sits in a distinct statistical cluster from natural Latin.")
    else:
        print("\n>>> RESULT: WEAK SEPARABILITY <<<")
        print("The manuscript overlaps significantly with Latin statistical profiles.")

if __name__ == "__main__":
    run_classification()
