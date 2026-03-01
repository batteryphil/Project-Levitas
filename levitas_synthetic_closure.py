import collections, random

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
OUT_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/synthetic_levitas_corpus.txt"
import re

def tokenize_v101(text):
    tokens = []
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'): continue
        body = re.sub(r'<[^>]*>', '', line)
        for ch in body:
            if ch.isalnum(): tokens.append(ch)
            elif ch in '.,':
                if tokens and tokens[-1] != ' ': tokens.append(' ')
    return tokens

def build_markov_rules(tokens):
    # P(T_{i+2} | T_i, T_{i+1})
    tri = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(len(tokens)-2):
        tri[(tokens[i], tokens[i+1])][tokens[i+2]] += 1
        
    # Convert to probabilities
    rules = {}
    for state, succs in tri.items():
        tot = sum(succs.values())
        norm = {k: v/tot for k, v in succs.items()}
        rules[state] = norm
    return rules

def generate_synthetic_corpus(rules, N=193960):
    # Start with a highly common seed
    state = ('9', ' ')
    corpus = list(state)
    
    for _ in range(N - 2):
        if state not in rules:
            # If we hit an unmapped state (should be rare/impossible in a closed loop), 
            # jump back to a common one
            state = ('9', ' ')
            
        succs = rules[state]
        choices = list(succs.keys())
        weights = list(succs.values())
        
        nxt = random.choices(choices, weights=weights)[0]
        corpus.append(nxt)
        state = (state[1], nxt)
        
    return corpus

def phase20_regeneration(real_tokens):
    # Strictly the same test from levitas_phase20_regeneration
    N = len(real_tokens)
    
    tri = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(N - 2):
        tri[(real_tokens[i], real_tokens[i+1])][real_tokens[i+2]] += 1

    # Strict argmax — no probability
    rules = {gram: max(succs, key=succs.get) for gram, succs in tri.items()}
    
    seed = (real_tokens[0], real_tokens[1])
    generated = [seed[0], seed[1]]

    drift_point = None

    for pos in range(2, N):
        gram = (generated[-2], generated[-1])
        if gram in rules:
            generated.append(rules[gram])
        else:
            drift_point = pos
            break
            
    compare_len = min(len(generated), N)
    exact_matches = sum(1 for i in range(compare_len) if generated[i] == real_tokens[i])
    match_rate = exact_matches / compare_len
    
    return match_rate, drift_point

if __name__ == "__main__":
    print(f"Reading Voynich corpus to extract transition rules...")
    with open(VOY_PATH) as f:
        v_tok = tokenize_v101(f.read())
        
    print(f"Building probabilistic engine...")
    rules = build_markov_rules(v_tok)
    
    print(f"Generating synthetic 193,960-token proxy corpus...")
    syn_corpus = generate_synthetic_corpus(rules)
    
    with open(OUT_PATH, "w") as f:
        f.write("".join(syn_corpus))
        
    print(f"Running Phase 20 Strict Deterministic Regeneration on the Synthetic Corpus...")
    match_rate, drift = phase20_regeneration(syn_corpus)
    
    print("=" * 60)
    print("RESULTS:")
    print(f"  Exact Match Rate: {match_rate:.2%}")
    if drift:
        print(f"  Drift Point: {drift:,} (Engine halted)")
    else:
        print(f"  Drift Point: NONE (Engine survived to end of corpus)")
