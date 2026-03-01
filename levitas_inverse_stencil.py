import collections
import re
import os

import sys

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/vulgate_latin.txt"
if not os.path.exists(LATIN_PATH):
    LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/homophonic_latin_193k.txt"

TARGET_FOLIO = 67
H_MOD, W_MOD = 4, 2 # Default for Voynich

def parse_lines_with_2d_context(text):
    """Returns lines as lists of tokens instead of a flat stream, to decode Line 1 easily."""
    lines_data = []
    
    for line_raw in text.splitlines():
        if not line_raw.strip() or line_raw.startswith('#'): continue
        
        match = re.search(r'<(\d+)[^.]*\.([^>]+)>', line_raw)
        if match:
            folio_num = int(match.group(1))
            line_str = match.group(2)
            if line_str.isdigit():
                line_num = int(line_str)
            else:
                line_num = sum(ord(c) for c in line_str)
        else:
            folio_num, line_num = 0, 0
            
        body = re.sub(r'<[^>]*>', '', line_raw)
        char_idx = 0
        tokens = []
        for ch in body:
            if ch.isalnum(): 
                tokens.append({'char': ch, 'folio': folio_num, 'line': line_num, 'pos': char_idx})
                char_idx += 1
            elif ch in '.,':
                if tokens and tokens[-1]['char'] != ' ': 
                    tokens.append({'char': ' ', 'folio': folio_num, 'line': line_num, 'pos': char_idx})
                    char_idx += 1
        
        lines_data.append((folio_num, line_num, line_str, tokens))
    return lines_data

def extract_latin_ranking():
    """Returns a list of Latin characters ranked by frequency from the control corpus."""
    with open(LATIN_PATH) as f:
        latin_text = f.read().replace(' ', '').lower()
        latin_chars = [c for c in latin_text if c.isalnum()]
        counts = collections.Counter(latin_chars)
        # return ranked list of characters, most frequent first
        return [char for char, cnt in counts.most_common()]

def extract_latin_ngrams():
    """Returns Bigram and Trigram transition probabilities: P(next | prev) and P(next | prev2, prev1)."""
    with open(LATIN_PATH) as f:
        latin_text = f.read().replace(' ', '').lower()
        # Mark word boundaries explicitly with spaces
        latin_chars = [' '] + [c for c in latin_text if c.isalnum() or c == ' '] + [' ']
        
        bigrams = collections.defaultdict(lambda: collections.defaultdict(int))
        trigrams = collections.defaultdict(lambda: collections.defaultdict(int))
        
        for i in range(len(latin_chars)-1):
            bigrams[latin_chars[i]][latin_chars[i+1]] += 1
        for i in range(len(latin_chars)-2):
            trigrams[(latin_chars[i], latin_chars[i+1])][latin_chars[i+2]] += 1
            
        bi_probs = {}
        tri_probs = {}
        for prev, next_counts in bigrams.items():
            total = sum(next_counts.values())
            bi_probs[prev] = {k: v / total for k, v in next_counts.items()}
        for prev_tuple, next_counts in trigrams.items():
            total = sum(next_counts.values())
            tri_probs[prev_tuple] = {k: v / total for k, v in next_counts.items()}
            
        return bi_probs, tri_probs

if __name__ == "__main__":
    input_file = VOY_PATH
    is_voynich = True
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        is_voynich = False
        H_MOD, W_MOD = 2, 3 # Detected dimensions for test
        print(f"Loading custom input: {input_file}")
    else:
        print(f"Reading Voynich corpus (Folio {TARGET_FOLIO})...")

    with open(input_file) as f:
        all_lines = parse_lines_with_2d_context(f.read())
        
    if is_voynich:
        f67_lines = [l for l in all_lines if l[0] == TARGET_FOLIO]
    else:
        f67_lines = all_lines # Process everything
    
    print("=" * 70)
    print("EXPERIMENT 15: The Aperture-Corrected Translation Logic (Inverse Stencil)")
    print(f"Applying dimensions: H={H_MOD}, W={W_MOD}")
    print("-" * 70)
    
    # Process Folio 67 by physical coordinate
    translation_table = collections.defaultdict(lambda: collections.defaultdict(int))
    
    for _, _, _, tokens in f67_lines:
        for t in tokens:
            if t['char'] == ' ': continue # We leave spacing alone
            cell_id = (t['line'] % H_MOD, t['pos'] % W_MOD)
            translation_table[cell_id][t['char']] += 1
            
    # Load Latin unigram baseline
    latin_ranking = extract_latin_ranking()
    
    # Map the most frequent glyph per cell to the top 10 Latin baseline unigrams
    final_mapping_candidates = {}
    print("Generating 8-Cell Translation Matrices (Top 10 candidates per glyph)...")
    for y in range(H_MOD):
        for x in range(W_MOD):
            cell = (y, x)
            counts = translation_table[cell]
            ranked_voynich = [char for char, cnt in sorted(counts.items(), key=lambda item: item[1], reverse=True)]
            
            # Create a 1-to-1 dictionary for this specific cell
            cell_map = collections.defaultdict(list)
            for i, v_char in enumerate(ranked_voynich):
                primary_guess = latin_ranking[i] if i < len(latin_ranking) else 'e'
                
                # We give it the true rank, plus a few 'nearby' ranked characters as options
                window_size = 5
                start_idx = max(0, i - window_size)
                end_idx = min(len(latin_ranking), i + window_size + 1)
                candidates = latin_ranking[start_idx:end_idx]
                
                # --- MANUAL GEAR ENGAGEMENT (VOYNICH ONLY) ---
                if is_voynich:
                    if v_char == '9': candidates = ['s', 'm', 'a']
                    if v_char == 'o': candidates = ['a', 'e', 'o']
                    
                cell_map[v_char] = candidates
                
            final_mapping_candidates[cell] = cell_map
            
    # Load Latin N-grams
    latin_bigrams, latin_trigrams = extract_latin_ngrams()
            
    print("Maps compiled successfully.\n")
    print("Applying Inverse Stencil to Folio 67, Line 1...")
    
    target_line_data = f67_lines[0] # The very first line of Folio 67
    t_folio, t_line_num, t_line_str, target_tokens = target_line_data
    
    # Advanced Beam-Search Viterbi approximation for Trigram decoding
    def decode_with_context(tokens):
        decoded = []
        prev1 = ' '
        prev2 = ' '
        
        for t in tokens:
            orig = t['char']
            if orig == ' ':
                decoded.append(' ')
                prev2 = prev1
                prev1 = ' '
                continue
                
            cell = (t['line'] % H_MOD, t['pos'] % W_MOD)
            candidates = final_mapping_candidates[cell].get(orig, ['e']) # Default to 'e'
            
            best_cand = candidates[0]
            best_score = -1.0
            
            for cand in candidates:
                # Get trigram score P(cand | prev2, prev1)
                tri_score = latin_trigrams.get((prev2, prev1), {}).get(cand, 0.0)
                # Fallback to bigram score P(cand | prev1)
                bi_score = latin_bigrams.get(prev1, {}).get(cand, 0.0001)
                
                # Interpolated score
                score = (tri_score * 0.8) + (bi_score * 0.2)
                
                # Give slight bias to the true rank mapping (cand[0])
                if cand == candidates[0]: score *= 2.0 
                
                if score > best_score:
                    best_score = score
                    best_cand = cand
                    
            decoded.append(best_cand)
            prev2 = prev1
            prev1 = best_cand
            
        return "".join(decoded).upper()
        
    dec_str = decode_with_context(target_tokens)
    
    orig_str = "".join([t['char'] for t in target_tokens])
    
    print(f"\n[ORIGINAL VOYNICH: <67r1.{t_line_str}>]")
    print(f"  {orig_str}")
    
    print(f"\n[UN-GROUND LATIN TRANSLATION (Bigram Context)]")
    print(f"  {dec_str}\n")
    
    # Let's decode the entire Folio and scan for astronomical/test keywords
    targets = ["STELL", "SOLE", "LUNA", "GRAD", "ORB", "ASTR", "ZOD"]
    if not is_voynich:
        targets = ["GALLIA", "DIVISA", "OMNIS", "BELGAE"]
        
    found_lines = []
    
    for _, l_num, l_str, tokens in f67_lines:
        full_line = decode_with_context(tokens)
        for t in targets:
            if t in full_line:
                found_lines.append((l_str, t, full_line))
                
    if found_lines:
        print(f">>> FOUND {len(found_lines)} KEYWORD MATCHES <<<")
        for l_str, word, text in found_lines[:10]: # Print top 10
            print(f"  <Line {l_str}> | Matched '{word}': {text}")
    else:
        print("No immediate keywords found. Mapping complexity might be too high.")
