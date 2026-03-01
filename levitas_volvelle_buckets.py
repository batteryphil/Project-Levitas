import collections
import re
import os

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/homophonic_latin.txt"
if not os.path.exists(LATIN_PATH):
    LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/homophonic_latin_193k.txt"

TARGET_FOLIO = 67
RAIL_COLS = {0, 76, 92}

def parse_with_2d_context(text):
    tokens = []
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
        for ch in body:
            if ch.isalnum(): 
                tokens.append({'char': ch, 'folio': folio_num, 'line': line_num, 'pos': char_idx})
                char_idx += 1
            elif ch in '.,':
                if tokens and tokens[-1]['char'] != ' ': 
                    tokens.append({'char': ' ', 'folio': folio_num, 'line': line_num, 'pos': char_idx})
                    char_idx += 1
    return tokens

def analyze_stationary_suffixes(bucket_tokens, target_char='9'):
    # Look at trailing characters of words
    word_ends = []
    # Reconstruct words in the bucket
    words = []
    current_word = []
    for t in bucket_tokens:
        if t['char'] == ' ':
            if current_word:
                words.append("".join(current_word))
                current_word = []
        else:
            current_word.append(t['char'])
    if current_word:
        words.append("".join(current_word))

    end_freqs = collections.Counter(w[-1] for w in words if w)
    total_ends = sum(end_freqs.values())
    if total_ends == 0: return 0.0, 0
    return end_freqs[target_char] / total_ends, end_freqs[target_char]

def get_character_distribution(tokens):
    freqs = collections.Counter(t['char'] for t in tokens if t['char'] != ' ')
    total = sum(freqs.values())
    return {k: v / total for k, v in freqs.items() if total > 0}

if __name__ == "__main__":
    print(f"Reading Voynich corpus to isolate Folio {TARGET_FOLIO}...")
    with open(VOY_PATH) as f:
        tokens = parse_with_2d_context(f.read())
        
    folio_tokens = [t for t in tokens if t['folio'] == TARGET_FOLIO]
    print(f"Tokens isolated: {len(folio_tokens):,}")
    
    # 1. Strip the "Rails"
    cleaned_tokens = [t for t in folio_tokens if t['pos'] not in RAIL_COLS]
    print(f"Tokens after stripping mechanical rails (Cols 0, 76, 92): {len(cleaned_tokens):,}\n")
    
    # 2. Virtual Volvelle (Segregate by Modulo-4 line cycle)
    buckets = {0: [], 1: [], 2: [], 3: []}
    for t in cleaned_tokens:
        buckets[t['line'] % 4].append(t)
        
    print("=" * 70)
    print("EXPERIMENT 13: Volvelle Bucket Alignment (Inverse Encoding)")
    print("=" * 70)
    
    print("Looking for 'The Aligned Ghost' - Top Suffixes per Bucket")
    
    def get_all_word_ends(bucket_tokens):
        words = []
        current_word = []
        for t in bucket_tokens:
            if t['char'] == ' ':
                if current_word:
                    words.append("".join(current_word))
                    current_word = []
            else:
                current_word.append(t['char'])
        if current_word:
            words.append("".join(current_word))
        return [w[-1] for w in words if w]
    
    for b_id in range(4):
        b_tokens = buckets[b_id]
        if not b_tokens: continue
        
        ends = get_all_word_ends(b_tokens)
        if not ends: continue
        
        counts = collections.Counter(ends)
        total = sum(counts.values())
        top5 = counts.most_common(5)
        
        print(f"\nBucket {b_id} Top Suffixes (Total Words: {total}):")
        for char, count in top5:
            print(f"  '{char}': {count/total:>6.2%} (Count: {count})")
            
    print("\nGlobal Top Suffixes:")
    global_ends = get_all_word_ends(cleaned_tokens)
    g_counts = collections.Counter(global_ends)
    g_total = sum(g_counts.values())
    for char, count in g_counts.most_common(5):
        print(f"  '{char}': {count/g_total:>6.2%} (Count: {count})")
    
    print("\nExtracting Bucket 0 Un-Ground Distribution vs Latin Control...")
    with open(LATIN_PATH) as f:
        latin_text = f.read().replace(' ', '').lower()
        latin_chars = [c for c in latin_text if c.isalnum()][:10000] # Use a chunk
        latin_freq = collections.Counter(latin_chars)
        ltotal = sum(latin_freq.values())
        latin_dist = {k: v / ltotal for k, v in latin_freq.items()}
        
    # We sort taking top 5 chars in bucket 0, just to visually compare the Zipf curve
    b0_dist = get_character_distribution(buckets[0])
    top_b0 = sorted(b0_dist.items(), key=lambda x: x[1], reverse=True)[:5]
    top_lat = sorted(latin_dist.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print("Top 5 Characters in Aligned Bucket 0:")
    for char, freq in top_b0:
        print(f"  '{char}': {freq:>6.2%}")
        
    print("Top 5 Characters in Sanguine & Steel Latin Control:")
    for char, freq in top_lat:
        print(f"  '{char}': {freq:>6.2%}")
