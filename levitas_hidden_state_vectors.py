import collections, math, re

FULL_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/latin_control_large.txt"

def get_section(folio_num):
    if 1 <= folio_num <= 66: return "Botanical"
    if 67 <= folio_num <= 73: return "Astronomical"
    if 75 <= folio_num <= 84: return "Biological"
    if 87 <= folio_num <= 102: return "Pharmaceutical"
    if 103 <= folio_num <= 116: return "Recipes"
    return "Other"

def parse_v101_rich(text):
    tokens = []
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'): continue
        match = re.search(r'<(\d+)[rvA-Z]*\.(\d+)>', line)
        if match:
            folio_num = int(match.group(1))
            line_num = int(match.group(2))
        else:
            folio_num, line_num = 0, 0
            
        sec = get_section(folio_num)
        
        body = re.sub(r'<[^>]*>', '', line)
        for ch in body:
            if ch.isalnum(): tokens.append((ch, line_num, sec))
            elif ch in '.,':
                if tokens and tokens[-1][0] != ' ': tokens.append((' ', line_num, sec))
    return tokens

def tokenize_eva(text):
    tokens, in_tag = [], False
    for ch in text:
        if ch == '<': in_tag = True; continue
        if ch == '>': in_tag = False; continue
        if not in_tag and 31 < ord(ch) < 127: tokens.append(ch)
    return tokens

# ==== 1. Line-Index & Vertical Conditioning ====
def experiment_1(tokens_rich):
    print("=" * 60)
    print("EXPERIMENT 1: Line-Index & Vertical Conditioning")
    
    # Baseline Trigram BE
    n = len(tokens_rich)
    tri_base = collections.defaultdict(lambda: collections.defaultdict(int))
    tri_line = collections.defaultdict(lambda: collections.defaultdict(int))
    
    for i in range(n-2):
        t1, l1, _ = tokens_rich[i]
        t2, _, _ = tokens_rich[i+1]
        t3, _, _ = tokens_rich[i+2]
        
        tri_base[(t1, t2)][t3] += 1
        tri_line[(t1, t2, l1)][t3] += 1
        
    def calc_metrics(tri):
        be = (sum(-sum((c/sum(s.values()))*math.log2(c/sum(s.values())) for c in s.values()) for s in tri.values()) / len(tri)) if tri else 0
        det95 = sum(1 for s in tri.values() if max(s.values())/sum(s.values()) >= 0.95) / len(tri) if tri else 0
        return be, det95, len(tri)

    b_be, b_det, b_states = calc_metrics(tri_base)
    l_be, l_det, l_states = calc_metrics(tri_line)
    
    print(f"  Baseline (2-gram context):  BE={b_be:.4f} bits, Det@95={b_det:.1%}, States={b_states:,}")
    print(f"  Conditioned (+ Line Index): BE={l_be:.4f} bits, Det@95={l_det:.1%}, States={l_states:,}")
    print(f"  => Determinism Jump: {l_det - b_det:+.1%}")

# ==== 2. Inter-word Mutual Information ====
def calc_inter_word_mi(tokens, is_rich=False):
    if is_rich:
        text = "".join(t[0] for t in tokens)
    else:
        text = "".join(tokens)
        
    words = text.split()
    pairs = []
    for i in range(len(words)-1):
        if len(words[i]) > 0 and len(words[i+1]) > 0:
            pairs.append((words[i][-1], words[i+1][0]))
            
    c_i = collections.Counter(p[0] for p in pairs)
    c_j = collections.Counter(p[1] for p in pairs)
    c_ij = collections.Counter(pairs)
    
    t = len(pairs)
    mi = 0
    for (i, j), count in c_ij.items():
        p_ij = count / t
        p_i = c_i[i] / t
        p_j = c_j[j] / t
        mi += p_ij * math.log2(p_ij / (p_i * p_j))
    return mi

def experiment_2(v_tok_rich, l_tok):
    print("\n" + "=" * 60)
    print("EXPERIMENT 2: Inter-word Mutual Information")
    
    v_mi = calc_inter_word_mi(v_tok_rich, is_rich=True)
    l_mi = calc_inter_word_mi(l_tok, is_rich=False)
    
    print(f"  Voynich I(T_end ; T_start): {v_mi:.4f} bits")
    print(f"  Latin   I(T_end ; T_start): {l_mi:.4f} bits")

# ==== 3. High-Entropy Bridge Glyphs ====
def experiment_3(tokens_rich):
    print("\n" + "=" * 60)
    print("EXPERIMENT 3: High-Entropy Bridge Glyphs")
    
    # H(T_{i+1} | T_i = g)
    bi = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(len(tokens_rich)-1):
        bi[tokens_rich[i][0]][tokens_rich[i+1][0]] += 1
        
    sbe = {}
    for g, succs in bi.items():
        tot = sum(succs.values())
        if tot >= 50: # filter out very rare symbols
            ent = -sum((c/tot)*math.log2(c/tot) for c in succs.values())
            sbe[g] = (ent, tot)
            
    print("  Top 10 High-Entropy 'State-Shifter' Candidates:")
    for g, (ent, tot) in sorted(sbe.items(), key=lambda x: -x[1][0])[:10]:
        print(f"    Glyph {g!r}: Specific BE = {ent:.4f} bits (n={tot})")

# ==== 4. Cross-Sectional State Transfer ====
def experiment_4(tokens_rich):
    print("\n" + "=" * 60)
    print("EXPERIMENT 4: Cross-Sectional State Transfer")
    
    # Find most common bigram
    bi = collections.defaultdict(int)
    for i in range(len(tokens_rich)-2):
        bi[(tokens_rich[i][0], tokens_rich[i+1][0])] += 1
        
    target = sorted(bi.items(), key=lambda x: -x[1])[0][0]
    print(f"  Tracking most common bigram: {''.join(target)!r} (n={bi[target]})")
    
    dist_by_sec = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(len(tokens_rich)-2):
        if (tokens_rich[i][0], tokens_rich[i+1][0]) == target:
            sec = tokens_rich[i][2]
            succ = tokens_rich[i+2][0]
            dist_by_sec[sec][succ] += 1
            
    sections = ["Botanical", "Astronomical", "Biological", "Pharmaceutical", "Recipes"]
    for sec in sections:
        succs = dist_by_sec[sec]
        tot = sum(succs.values())
        if tot == 0: continue
        
        top3 = sorted(succs.items(), key=lambda x: -x[1])[:3]
        dist_str = ", ".join(f"{k!r}: {v/tot:.1%}" for k, v in top3)
        print(f"    {sec[:10]:<10} (n={tot:<4}): {dist_str}")

if __name__ == "__main__":
    with open(FULL_PATH) as f:
        v_tok_rich = parse_v101_rich(f.read())
        
    with open(LATIN_PATH) as f:
        l_tok_raw = tokenize_eva(f.read())
        l_tok = l_tok_raw[:len(v_tok_rich)] # length-match exactly
        
    experiment_1(v_tok_rich)
    experiment_2(v_tok_rich, l_tok)
    experiment_3(v_tok_rich)
    experiment_4(v_tok_rich)
