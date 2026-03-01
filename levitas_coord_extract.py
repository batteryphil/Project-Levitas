import collections
import re
import numpy as np

VOY_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
TARGET_FOLIO = 67

def parse_with_2d_context(text):
    tokens = []
    for line_raw in text.splitlines():
        if not line_raw.strip() or line_raw.startswith('#'): continue
        
        # e.g., <67r1.outer_ring> or <1r.1>
        match = re.search(r'<(\d+)[^.]*\.([^>]+)>', line_raw)
        if match:
            folio_num = int(match.group(1))
            line_str = match.group(2)
            # Create a pseudo-line integer if it's text (outer_ring -> hash)
            if line_str.isdigit():
                line_num = int(line_str)
            else:
                line_num = sum(ord(c) for c in line_str) # Simple deterministic integer
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

if __name__ == "__main__":
    print(f"Reading Voynich corpus to isolate Folio {TARGET_FOLIO}...")
    with open(VOY_PATH) as f:
        tokens = parse_with_2d_context(f.read())
        
    folio_tokens = [t for t in tokens if t['folio'] == TARGET_FOLIO]
    
    print("=" * 70)
    print(f"EXPERIMENT 12: Coordinate-Frequency Extraction (Folio {TARGET_FOLIO})")
    print(f"Tokens isolated: {len(folio_tokens):,}")
    print("-" * 70)
    
    # Map frequencies by (Line, Pos) coordinate
    coord_stats = collections.defaultdict(lambda: collections.defaultdict(int))
    for t in folio_tokens:
        coord = (t['line'], t['pos'])
        coord_stats[coord][t['char']] += 1
        
    # We want to find the most "Rigid" cells.
    # Where the scribe produced the same glyph continuously at this exact coordinate
    # Oh wait, there is only one occurrence of (line 1, pos 5) on a single Folio!
    # A single folio only has one instance of Line L, Position P.
    # We should look at POS coordinates across all lines in the folio (Vertical Columns)
    # OR we use a sliding Grid Modulo (e.g. Line % H, Pos % W) to fold the folio onto a template.
    
    # Let's extract frequencies across Columns (Absolute Position) on this Folio
    # P(T | Pos, Folio=67)
    col_stats = collections.defaultdict(lambda: collections.defaultdict(int))
    for t in folio_tokens:
        col_stats[t['pos']][t['char']] += 1
        
    print("Vertical Column Determinism on Folio 67:")
    print("Displaying columns where a single character dominates (>30% frequency across all lines)")
    print(f"{'Position (Col)':<15} | {'Dominant Char':<15} | {'Frequency':<10} | {'Observations'}")
    print("-" * 70)
    
    rigid_cols = []
    
    for pos in sorted(col_stats.keys()):
        counts = col_stats[pos]
        total_obs = sum(counts.values())
        if total_obs < 5: continue # Ignore sparse margins
        
        best_char = max(counts, key=counts.get)
        freq = counts[best_char] / total_obs
        
        if freq >= 0.30:
            rigid_cols.append((pos, best_char, freq, total_obs))
            print(f"  Col {pos:<11} |  '{best_char}'            |  {freq:>7.2%}   |  {total_obs:>2}")
            
    print("\nExtracting Local XY Grid Modulo Determinism...")
    print("Assuming a repeating physical wheel/grille. Testing Grid Heights (H=2 to H=6)...")
    
    for H in range(2, 7):
        grid_stats = collections.defaultdict(lambda: collections.defaultdict(int))
        for t in folio_tokens:
            coord = (t['line'] % H, t['pos'])
            grid_stats[coord][t['char']] += 1
            
        deterministic_cells = 0
        total_valid_cells = 0
        
        for coord, counts in grid_stats.items():
            total_obs = sum(counts.values())
            if total_obs < 3: continue
            
            best_char = max(counts, key=counts.get)
            freq = counts[best_char] / total_obs
            
            total_valid_cells += 1
            if freq >= 0.60: # Extremely deterministic cell mapping
                deterministic_cells += 1
                
        if total_valid_cells > 0:
            rigid_rate = deterministic_cells / total_valid_cells
            print(f"  Modulo Height {H}: {rigid_rate:>6.2%} of cells are highly deterministic (>60%).")
