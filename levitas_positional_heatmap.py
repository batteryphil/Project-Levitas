import collections, math, re

FULL_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"

def parse_with_horizontal_pos(text):
    tokens = []
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'): continue
        body = re.sub(r'<[^>]*>', '', line)
        char_idx = 0
        for ch in body:
            if ch.isalnum(): 
                tokens.append((ch, char_idx))
                char_idx += 1
            elif ch in '.,':
                if tokens and tokens[-1][0] != ' ': 
                    tokens.append((' ', char_idx))
                    char_idx += 1
    return tokens

def positional_heatmap(tokens):
    print("=" * 60)
    print("EXPERIMENT 5: Positional Heatmap (BE by Horizontal Index)")
    
    # tri_by_pos[pos3][(t1, t2)][t3] += 1
    tri_by_pos = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))
    counts_by_pos = collections.defaultdict(int)
    
    for i in range(len(tokens)-2):
        t1 = tokens[i][0]
        t2 = tokens[i+1][0]
        t3 = tokens[i+2][0]
        pos3 = tokens[i+2][1]
        
        if pos3 < 60:
            tri_by_pos[pos3][(t1, t2)][t3] += 1
            counts_by_pos[pos3] += 1
            
    print(f"  Pos | Tokens | BE (bits) | Det@95% | States ")
    print("  " + "-"*46)
    
    for pos in range(60):
        tri = tri_by_pos[pos]
        count = counts_by_pos[pos]
        if count < 500: continue # Skip positions with very few samples
        
        be = (sum(-sum((c/sum(s.values()))*math.log2(c/sum(s.values())) for c in s.values()) for s in tri.values()) / len(tri)) if tri else 0
        det95 = sum(1 for s in tri.values() if max(s.values())/sum(s.values()) >= 0.95) / len(tri) if tri else 0
        
        # Visualize the BE as a bar for heatmap effect
        bar_len = int((be / 2.0) * 20) # scale: 2.0 bits = 20 chars
        bar = "#" * bar_len
        
        print(f"  {pos:>3} | {count:>6} | {be:>9.4f} | {det95:>6.1%} | {len(tri):>6} | {bar}")

if __name__ == "__main__":
    with open(FULL_PATH) as f:
        toks = parse_with_horizontal_pos(f.read())
    positional_heatmap(toks)
