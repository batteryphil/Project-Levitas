"""
EVA-25 Core Character Mapping for v101 Voynich Corpus
======================================================
Maps the 172-symbol v101 alphabet to ~25 canonical EVA character classes.

v101 encoding reference (from Takahashi/Zandbergen documentation):
The Voynich Manuscript in v101 encoding uses a combination of letters,
digits, and punctuation to represent compound EVA glyphs.

Mapping rationale (based on Zandbergen's v101 documentation):
  Core single-char EVA: a c d e f g h i k m n o p q r s t y
  Compound EVA glyphs encoded as digit+letter or letter pairs in v101:
    '8'      → 'a'  (EVA 'a'  — most frequent stroke)
    '9'      → 'i'  (EVA 'i'/'in' — vertical stroke)
    '1'      → 'ch' → map to 'c'
    '2'      → 'sh' → 's'
    '4'      → 'o'  (loop glyph variant)
    '7'      → 'e'  (EVA 'ee'/'e' variant)
    '3'      → 'r'  (EVA 'r' variant)
    '5'      → 't'  (EVA 't' variant)
    '6'      → 'l'  (EVA 'l' variant)
    '0'      → 'd'  (EVA 'd' variant)
  Uppercase: C→c, K→k, H→h, A→a, M→m, Z→z, N→n, J→j
  Punctuation/other: all → X (catch-all rare class)

Result: ~26 core character classes (a-z lower + X for unknowns)
"""

import collections, math, random, re, zlib, string
random.seed(42)

V_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
L_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/latin_control_large.txt"

# EVA-25 mapping table
EVA_MAP = {
    # Digits → EVA equivalents
    '8': 'a',   # a-like glyph (Zandbergen v101: qo-line glyph)
    '9': 'i',   # in/iin vertical stroke
    '1': 'c',   # ch compound
    '2': 's',   # sh compound
    '4': 'o',   # loop variant
    '7': 'e',   # ee/ee variant
    '3': 'r',   # r variant
    '5': 't',   # t variant
    '6': 'l',   # l variant
    '0': 'd',   # d variant
    # Uppercase → lowercase equivalents
    'C': 'c',
    'K': 'k',
    'H': 'h',
    'A': 'a',
    'M': 'm',
    'Z': 'z',
    'N': 'n',
    'J': 'j',
    'G': 'g',
    'P': 'p',
    'F': 'f',
    'Q': 'q',
    'S': 's',
    'T': 't',
    'R': 'r',
    'E': 'e',
    'D': 'd',
    'B': 'b',
    'I': 'i',
    'L': 'l',
    'O': 'o',
    'U': 'u',
    'V': 'v',
    'W': 'w',
    'X': 'x',
    'Y': 'y',
}

def parse_v101_eva25(text):
    tokens = []
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'): continue
        body = re.sub(r'<[^>]*>', '', line)
        for ch in body:
            if ch.isalnum():
                mapped = EVA_MAP.get(ch, ch.lower())
                tokens.append(mapped)
            elif ch in '.,':
                if tokens and tokens[-1] != ' ':
                    tokens.append(' ')
    return tokens

def tokenize_plain(text):
    tokens = []
    for ch in text:
        if ch.isalpha(): tokens.append(ch.lower())
        elif ch == ' ' and tokens and tokens[-1] != ' ':
            tokens.append(' ')
    return tokens

def sig(tokens):
    n = len(tokens)
    if n < 10: return None
    tri = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(n-2):
        tri[(tokens[i], tokens[i+1])][tokens[i+2]] += 1
    be = sum(-sum((c/sum(s.values()))*math.log2(c/sum(s.values())) for c in s.values())
             for s in tri.values()) / len(tri) if tri else 0
    det95 = sum(1 for s in tri.values()
                if max(s.values())/sum(s.values()) >= 0.95) / len(tri) if tri else 0
    raw = "".join(tokens[:min(n, 5000)]).encode()
    bpg = len(zlib.compress(raw)) * 8 / max(len(raw), 1)
    return {"n": n, "states": len(tri), "be": be, "det95": det95, "bpg": bpg,
            "alph": len(set(tokens) - {' '})}

def eucl(a, b):
    keys = ["be", "det95", "bpg"]
    return math.sqrt(sum((a[k]-b[k])**2 for k in keys))

# Load
print("Loading corpora...")
with open(V_PATH) as f: v_raw_text = f.read()
with open(L_PATH) as f: l_full = tokenize_plain(f.read())

v_eva25 = parse_v101_eva25(v_raw_text)
N_V = len(v_eva25)
N_L = len(l_full)

# Show final alphabet after EVA-25 mapping
alph_counts = collections.Counter(t for t in v_eva25 if t != ' ')
print(f"\nEVA-25 alphabet size: {len(alph_counts)} symbols")
print(f"Symbols: {sorted(alph_counts.keys())}")
print(f"Latin alphabet size: {len(set(l_full)-{' '})}")

# Full comparison at N = 193,960
print("\n" + "="*72)
print(f"FULL N = 193,960 — EVA-25 Normalized Voynich vs Latin (Perseus)")
print("="*72)
random.seed(42)
ls = random.randint(0, N_L - N_V)
l_sub = l_full[ls:ls+N_V]
sv = sig(v_eva25[:N_V])
sl = sig(l_sub)

print(f"\n  {'':18} {'States':>7} {'Alph':>5} {'BE':>7} {'Det@95':>7} {'BPG':>7}")
print(f"  {'Voynich (EVA-25)':18} {sv['states']:>7} {sv['alph']:>5} {sv['be']:>7.4f} {sv['det95']:>7.1%} {sv['bpg']:>7.3f}")
print(f"  {'Latin (Perseus)':18} {sl['states']:>7} {sl['alph']:>5} {sl['be']:>7.4f} {sl['det95']:>7.1%} {sl['bpg']:>7.3f}")
ratio = sv['states'] / sl['states']
print(f"\n  State ratio (V/L): {ratio:.3f}")
print(f"  BE gap (V-L):      {sv['be'] - sl['be']:+.4f}")
print(f"  Det gap (V-L):     {sv['det95'] - sl['det95']:+.3f}")

# Heaps' Law curve — EVA-25 Voynich vs Latin (truly growing)
print("\n" + "="*72)
print("HEAPS' LAW CURVE — EVA-25 Voynich vs Latin (N growing, no tiling)")
print("="*72)
print(f"  {'N':>8} | {'V States':>8} | {'V Alph':>7} | {'V BE':>7} | {'L States':>8} | {'L Alph':>7} | {'L BE':>7} | {'Leader':>8}")
print("  " + "-"*82)

for N in [500, 937, 2000, 5000, 10000, 50000, 100000, 193960]:
    if N > min(N_V, N_L): break
    random.seed(42)
    vs = random.randint(0, N_V - N); v_sub = v_eva25[vs:vs+N]
    ls2 = random.randint(0, N_L - N); l_sub2 = l_full[ls2:ls2+N]
    sv2 = sig(v_sub); sl2 = sig(l_sub2)
    leader = "Voynich" if sv2['states'] > sl2['states'] else "Latin  "
    print(f"  {N:>8,} | {sv2['states']:>8} | {sv2['alph']:>7} | {sv2['be']:>7.4f} | "
          f"{sl2['states']:>8} | {sl2['alph']:>7} | {sl2['be']:>7.4f} | {leader}")
