import collections
import re
import math
import numpy as np

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"

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

def split_into_folios(tokens):
    folios = collections.defaultdict(list)
    for t in tokens:
        folios[t['folio']].append(t)
    return folios

def train_2d_matrix(train_tokens):
    counts = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(len(train_tokens) - 1):
        t_curr = train_tokens[i]
        t_next = train_tokens[i+1]
        state = (t_curr['char'], t_curr['line'], t_curr['pos'])
        counts[state][t_next['char']] += 1
        
    rules = {state: max(succs, key=succs.get) for state, succs in counts.items()}
    return rules

def test_determinism(rules, test_tokens):
    if not test_tokens:
        return 0.0
        
    N = len(test_tokens)
    generated = [test_tokens[0]['char']]
    
    for i in range(1, N):
        target_token = test_tokens[i]
        prev_token_char = generated[-1]
        state = (prev_token_char, target_token['line'], target_token['pos'])
        
        if state in rules:
            generated.append(rules[state])
        else:
            generated.append(' ')
            
    matches = sum(1 for i in range(N) if generated[i] == test_tokens[i]['char'])
    return matches / N

def detect_gear_swaps(folio_dict, window_size=5):
    print(f"Detecting Gear-Swaps (Window Size = {window_size} folios)")
    print("-" * 60)
    
    swaps = []
    baseline_acc = []
    
    # Sort folios to iterate chronologically
    sorted_folio_nums = sorted(folio_dict.keys())
    
    accumulated_accs = []
    
    for i in range(len(sorted_folio_nums) - window_size):
        window_folios = sorted_folio_nums[i : i + window_size]
        next_folio_num = sorted_folio_nums[i + window_size]
        
        # Gather tokens for the training window
        train_tokens = []
        for f in window_folios:
            train_tokens.extend(folio_dict[f])
            
        # Gather tokens for testing the immediate next folio
        test_tokens = folio_dict[next_folio_num]
        
        # Skip empty or exceedingly short folios
        if len(test_tokens) < 50:
            continue
            
        model = train_2d_matrix(train_tokens)
        accuracy = test_determinism(model, test_tokens)
        
        # Establish a rolling baseline (mean of last 3 valid predictions)
        if len(accumulated_accs) >= 3:
            baseline = np.mean(accumulated_accs[-3:])
            threshold = baseline * 0.75 # 25% drop is a significant 'swap'
            
            status = ""
            if accuracy < threshold:
                swaps.append((next_folio_num, accuracy, baseline))
                status = f"<<< GEAR SWAP DETECTED >>>"
                # Reset baseline slightly to avoid cascading
                accumulated_accs = [accuracy]
            else:
                accumulated_accs.append(accuracy)
                
            print(f"Folios {window_folios[0]:>3}-{window_folios[-1]:>3} -> Predict Folio {next_folio_num:>3} | Acc: {accuracy:>6.2%} | Base: {baseline:>6.2%} {status}")
        else:
            accumulated_accs.append(accuracy)
            print(f"Folios {window_folios[0]:>3}-{window_folios[-1]:>3} -> Predict Folio {next_folio_num:>3} | Acc: {accuracy:>6.2%} | (Initializing Base)")

    return swaps

if __name__ == "__main__":
    print("Reading Voynich corpus...")
    with open(VOY_PATH) as f:
        tokens = parse_with_2d_context(f.read())
        
    print("=" * 60)
    print("EXPERIMENT 9: Local-Window Gear-Swap Detection")
    folio_dict = split_into_folios(tokens)
    
    swaps = detect_gear_swaps(folio_dict, window_size=5)
    
    print("=" * 60)
    print("MAJOR MECHANISM DRIFT BOUNDARIES (The 'Gear Swaps'):")
    for f_num, acc, base in swaps:
        print(f"  Folio {f_num:>3}: Accuracy collapsed from {base:.2%} to {acc:.2%} ({(acc-base)/base:.1%} drop)")
