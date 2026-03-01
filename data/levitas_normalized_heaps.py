"""
Alphabet-Normalized Heaps' Law Test
====================================
The Voynich v101 corpus uses 132 distinct symbols vs Latin's ~27.
A larger alphabet mechanically produces more bigram states.
This script:
  1. Shows what the 132 v101 symbols actually are (frequency table)
  2. Applies a principled collapse to ~25 core character classes
  3. Re-runs the Heaps' Law curve on NORMALIZED Voynich vs Latin
  4. Checks whether Voynich still out-discovers states with matched alphabet

Normalization strategy:
  - Lowercase: collapses uppercase variants (A→a, B→b, etc.)
  - Digit mapping: 0-9 → special glyph classes ('0'..'9' → bucket letters)
  - Space preserved as word separator
  Result: alphabet of size ≤ 37 (26 lowercase + 10 digit-buckets + space)
  
  Further reduction: digits mapped to just 3 buckets (common/rare/very-rare)
  giving a ~30-symbol alphabet, close to Latin's 27.
"""

import collections, math, random, zlib, re, string
random.seed(42)

V_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
L_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/latin_control_large.txt"


def parse_v101_raw(text):
    """Parse v101, keeping all characters as-is (no normalization)."""
    tokens = []
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'): continue
        body = re.sub(r'<[^>]*>', '', line)
        for ch in body:
            if ch.isalnum(): tokens.append(ch)
            elif ch in '.,':
                if tokens and tokens[-1] != ' ': tokens.append(' ')
    return tokens


def normalize_v101(tokens):
    """
    Collapse 132-symbol v101 alphabet to ~27-symbol EVA-like core:
    - All letters -> lowercase (collapses A-Z variants -> a-z, 26 classes)
    - Digits 0-9 -> 3 frequency-based buckets:
        high-freq digits (appear >1% of tokens): map to '#'
        mid-freq digits: map to '@'
        low-freq digits: map to '$'
    - Space preserved
    This gives alphabet size ≈ 26 + 3 + 1 = 30
    """
    counts = collections.Counter(t for t in tokens if t != ' ')
    total = sum(counts.values())
    digit_freq = {ch: counts[ch]/total for ch in string.digits if ch in counts}
    
    high = {ch for ch, f in digit_freq.items() if f >= 0.01}
    mid  = {ch for ch, f in digit_freq.items() if 0.001 <= f < 0.01}
    low  = set(string.digits) - high - mid
    
    normalized = []
    for t in tokens:
        if t == ' ':
            normalized.append(' ')
        elif t.isalpha():
            normalized.append(t.lower())
        elif t in high:
            normalized.append('#')
        elif t in mid:
            normalized.append('@')
        elif t in low:
            normalized.append('$')
        # else drop
    return normalized


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
    for i in range(n-2): tri[(tokens[i],tokens[i+1])][tokens[i+2]] += 1
    be = sum(-sum((c/sum(s.values()))*math.log2(c/sum(s.values())) for c in s.values())
             for s in tri.values()) / len(tri) if tri else 0
    det95 = sum(1 for s in tri.values() if max(s.values())/sum(s.values())>=0.95)/len(tri) if tri else 0
    return {"n":n, "states":len(tri), "be":be, "det95":det95,
            "alph":len(set(tokens)-{' '})}


# ── Load ──────────────────────────────────────────────────────────────────────
with open(V_PATH) as f: v_raw  = parse_v101_raw(f.read())
with open(L_PATH) as f: l_full = tokenize_plain(f.read())
v_norm = normalize_v101(v_raw)

print("="*72)
print("STEP 1: Symbol Frequency — Raw v101 Voynich Corpus")
print("="*72)
raw_counts = collections.Counter(t for t in v_raw if t != ' ')
alph_raw   = sorted(raw_counts.keys())
print(f"  Alphabet size (raw):        {len(alph_raw)} symbols")
print(f"  Top 20 by frequency:")
for ch, cnt in raw_counts.most_common(20):
    bar = '█' * int(cnt / max(raw_counts.values()) * 30)
    print(f"    {repr(ch):>6}  {cnt:>8,}  {bar}")

print()
norm_counts = collections.Counter(t for t in v_norm if t != ' ')
print(f"  Alphabet size (normalized): {len(norm_counts)} symbols  "
      f"({sorted(norm_counts.keys())})")
print(f"  Latin alphabet size:        {len(set(l_full)-{chr(32)})} symbols")

# ── Heaps' Law curve — normalized Voynich vs Latin ───────────────────────────
print()
print("="*72)
print("STEP 2: HEAPS' LAW CURVE — Normalized Voynich vs Latin (matched alpha)")
print("="*72)
print(f"  Voynich alphabet after normalization: {len(norm_counts)} symbols")
print(f"  Latin alphabet:                       {len(set(l_full)-{chr(32)})} symbols")
print()
print(f"  {'N':>8} | {'V States':>8} | {'V BE':>7} | {'V Alph':>7} | "
      f"{'L States':>8} | {'L BE':>7} | {'L Alph':>7} | {'Leader':>8}")
print("  "+"-"*80)

N_V = len(v_norm); N_L = len(l_full)

for N in [500, 937, 2000, 5000, 10000, 50000, 100000, 193960]:
    if N > min(N_V, N_L): break
    random.seed(42)
    vs = random.randint(0, N_V-N); v_sub = v_norm[vs:vs+N]
    ls = random.randint(0, N_L-N); l_sub = l_full[ls:ls+N]
    sv = sig(v_sub); sl = sig(l_sub)
    leader = "Voynich" if sv['states'] > sl['states'] else "Latin  "
    print(f"  {N:>8,} | {sv['states']:>8} | {sv['be']:>7.4f} | {sv['alph']:>7} | "
          f"{sl['states']:>8} | {sl['be']:>7.4f} | {sl['alph']:>7} | {leader}")

# ── Full N comparison ────────────────────────────────────────────────────────
print()
print("="*72)
print(f"STEP 3: FULL N = 193,960 — Normalized Voynich vs Latin")
print("="*72)
random.seed(42)
ls = random.randint(0, N_L - 193960); l_sub_full = l_full[ls:ls+193960]
sv_full = sig(v_norm[:193960])
sl_full = sig(l_sub_full)
print(f"  Voynich (normalized):  alphabet={sv_full['alph']:>3}  states={sv_full['states']:>5}  "
      f"BE={sv_full['be']:.4f}  Det@95={sv_full['det95']:.1%}")
print(f"  Latin (Perseus):       alphabet={sl_full['alph']:>3}  states={sl_full['states']:>5}  "
      f"BE={sl_full['be']:.4f}  Det@95={sl_full['det95']:.1%}")
ratio = sv_full['states'] / sl_full['states']
print(f"\n  State ratio (V/L):     {ratio:.3f}  "
      f"({'Voynich has MORE states even with matched alphabet' if ratio > 1.0 else 'Latin leads at matched alphabet'})")
print(f"  BE gap (V-L):          {sv_full['be'] - sl_full['be']:+.4f}  "
      f"({'Voynich lower = more predictable' if sv_full['be'] < sl_full['be'] else 'Latin lower'})")
