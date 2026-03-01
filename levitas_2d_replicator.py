import collections
import re
import math

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"

def parse_with_2d_context(text):
    """
    Parses the text and returns a list of dictionaries.
    Each dictionary represents a token with its context:
    { 'char': 'g', 'folio': 1, 'line': 5, 'pos': 12 }
    """
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

def build_2d_model(train_tokens):
    """
    Builds the deterministic transition matrix:
    P(T_next | T_prev, Line_Modulo, Pos, Pos_Modulo)
    
    We use modulo on line and pos to simulate a repeating physical grid or wheel.
    """
    # State = (T_prev, Line % L_MOD, Pos)
    # We'll use L_MOD = 4 (e.g., a 4-line repeating grid) or we can just use the absolute line number
    # Let's try absolute line number first, as pages might be static grids
    
    counts = collections.defaultdict(lambda: collections.defaultdict(int))
    
    for i in range(len(train_tokens) - 1):
        t_curr = train_tokens[i]
        t_next = train_tokens[i+1]
        
        # We model the state as depending on: 
        # 1. The previous character
        # 2. The absolute line number on the folio
        # 3. The absolute horizontal position
        state = (t_curr['char'], t_curr['line'], t_curr['pos'])
        
        counts[state][t_next['char']] += 1
        
    # Convert to deterministic rules (argmax)
    rules = {}
    for state, succs in counts.items():
        # strict argmax
        best_char = max(succs, key=succs.get)
        rules[state] = best_char
        
    return rules

def test_2d_regeneration(test_tokens, rules):
    """
    Tests open-loop deterministic regeneration on the holdout set using the 2D rules.
    """
    if not test_tokens:
        return 0.0, 0
        
    N = len(test_tokens)
    
    # We must seed the first character to start the chain
    generated = [test_tokens[0]['char']]
    
    for i in range(1, N):
        # The context representing the "mechanical machine's" current position
        # depends on the true physical location of the text we are trying to generate
        target_token = test_tokens[i]
        prev_token_char = generated[-1] # Open-loop feedback
        
        state = (prev_token_char, target_token['line'], target_token['pos'])
        
        if state in rules:
            generated.append(rules[state])
        else:
            # If the state was never seen in training, default to a space (most common)
            # This represents the machine hitting an unmapped gear position.
            generated.append(' ')
            
    # Calculate match rate
    exact_matches = sum(1 for i in range(N) if generated[i] == test_tokens[i]['char'])
    match_rate = exact_matches / N
    
    return match_rate, N

if __name__ == "__main__":
    print(f"Reading Voynich corpus for 2D Spatial Analysis...")
    with open(VOY_PATH) as f:
        tokens = parse_with_2d_context(f.read())
        
    # Split into Train (Folios < 100) and Test (Folios >= 100) to ensure strict hold-out
    # We use folio 100 as the split to guarantee plenty of training data for the grid
    train_tokens = [t for t in tokens if t['folio'] < 100]
    test_tokens = [t for t in tokens if t['folio'] >= 100]
    
    print("=" * 70)
    print("EXPERIMENT 8: 2D Transition Matrix Generator (The Perfect Replicator)")
    print(f"Training Tokens (Folios < 100) : {len(train_tokens):,}")
    print(f"Hold-Out Tokens (Folios >= 100): {len(test_tokens):,}")
    print("-" * 70)
    
    # Baseline 1D Markov (T_next | T_prev) for comparison on the SAME split
    print("Training 1D Baseline Model...")
    counts_1d = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(len(train_tokens) - 1):
        counts_1d[train_tokens[i]['char']][train_tokens[i+1]['char']] += 1
    rules_1d = {s: max(c, key=c.get) for s, c in counts_1d.items()}
    
    gen_1d = [test_tokens[0]['char']]
    for i in range(1, len(test_tokens)):
        state = gen_1d[-1]
        gen_1d.append(rules_1d.get(state, ' '))
    match_1d = sum(1 for i in range(len(test_tokens)) if gen_1d[i] == test_tokens[i]['char']) / len(test_tokens)
    
    # Train and Test the 2D Model
    print("Training 2D Spatial Model...")
    rules_2d = build_2d_model(train_tokens)
    print(f"Total 2D Mechanical States Mapped: {len(rules_2d):,}")
    
    match_2d, test_n = test_2d_regeneration(test_tokens, rules_2d)
    
    print("-" * 70)
    print("OPEN-LOOP REGENERATION RESULTS (HOLD-OUT SET):")
    print(f"  1D Markov Baseline Match Rate: {match_1d:>6.2%}")
    print(f"  2D Spatial Matrix Match Rate : {match_2d:>6.2%}")
    print(f"  => Determinism Jump: {match_2d - match_1d:>+.2%}")
