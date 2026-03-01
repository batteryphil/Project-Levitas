"""
Real Matched-Length Control — Perseus Latin vs Voynich
=======================================================
Latin corpus: Livy, Pliny, Caesar, Virgil, Cicero (Perseus)
= 9,085,997 tokens. We subsample to match Voynich at multiple N.
"""
import collections, math, random, zlib, re, string
random.seed(42)

V_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/voynich_full_corpus.txt"
L_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/latin_control_large.txt"

def parse_v101(text):
    tokens = []
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'): continue
        body = re.sub(r'<[^>]*>', '', line)
        for ch in body:
            if ch.isalnum(): tokens.append(ch)
            elif ch in '.,':
                if tokens and tokens[-1] != ' ': tokens.append(' ')
    return tokens

def tokenize_plain(text):
    """Tokenize plain alpha text with white-space word splits."""
    tokens = []
    for ch in text:
        if ch.isalpha(): tokens.append(ch.lower())
        elif ch == ' ' and tokens and tokens[-1] != ' ':
            tokens.append(' ')
    return tokens

def make_vigenere(tokens, key="SECRETKEY"):
    result = []
    for i, ch in enumerate(tokens):
        shift = ord(key[i % len(key)]) - 65
        result.append(chr(((ord(ch) - 32 + shift) % 95) + 32))
    return result

def make_pcfg(n):
    NP, VP, CN = list("abcde"), list("fghij"), list("klmno")
    toks = []
    while len(toks) < n:
        r = random.random()
        if r < 0.4: toks += random.choices(NP, k=3) + random.choices(VP, k=2)
        elif r < 0.7: toks += random.choices(VP, k=2) + random.choices(NP, k=3)
        else: toks += random.choices(NP, k=2) + random.choices(CN, k=1) + random.choices(VP, k=2)
        toks.append(' ')
    return toks[:n]

def make_zipf(n, size=95):
    alph = list(string.printable[:size])
    w = [1/(k+1) for k in range(len(alph))]; t=sum(w); w=[x/t for x in w]
    return random.choices(alph, weights=w, k=n)

def sig(tokens):
    n = len(tokens)
    if n < 10: return None
    tri = collections.defaultdict(lambda: collections.defaultdict(int))
    for i in range(n-2): tri[(tokens[i],tokens[i+1])][tokens[i+2]] += 1
    be = sum(-sum((c/sum(s.values()))*math.log2(c/sum(s.values())) for c in s.values()) for s in tri.values()) / len(tri) if tri else 0
    det95 = sum(1 for s in tri.values() if max(s.values())/sum(s.values())>=0.95)/len(tri) if tri else 0
    raw = "".join(tokens[:min(n,5000)]).encode()
    bpg = len(zlib.compress(raw))*8/max(len(raw),1)
    words = "".join(tokens).split()
    ic = collections.Counter(w[0] for w in words if w)
    fc = collections.Counter(w[-1] for w in words if w)
    def h(c): t=sum(c.values()); return -sum((v/t)*math.log2(v/t) for v in c.values()) if t else 0
    pb = h(ic)/h(fc) if h(fc)>0 else 1.0
    shifted = tokens[5:]+tokens[:5]
    def h2(d): c=collections.Counter(d); t=len(d); return -sum((v/t)*math.log2(v/t) for v in c.values()) if t else 0
    def jh(x,y):
        m=min(len(x),len(y)); p=list(zip(x[:m],y[:m])); c=collections.Counter(p); t=len(p)
        return -sum((v/t)*math.log2(v/t) for v in c.values()) if t else 0
    hv=h2(tokens); nmi=(h2(tokens)+h2(shifted)-jh(tokens,shifted))/hv if hv>0 else 0
    return {"n":n,"states":len(tri),"det95":det95,"be":be,"bpg":bpg,"pb":pb,"nmi":nmi}

def eucl(a,b):
    keys=["be","det95","bpg","pb","nmi"]
    return math.sqrt(sum((a[k]-b[k])**2 for k in keys))

# Load
print("Loading corpora...")
with open(V_PATH) as f: v_full = parse_v101(f.read())
with open(L_PATH) as f: l_full = tokenize_plain(f.read())
print(f"Voynich:  {len(v_full):>12,} tokens")
print(f"Latin:    {len(l_full):>12,} tokens")
N_V = len(v_full)
N_L = len(l_full)

# Full-scale signature (full Voynich vs random subwindow of Latin at same N)
print("\n" + "="*80)
print(f"MATCHED N = {N_V:,} (Voynich FULL vs Latin subsampled)")
print("="*80)
random.seed(42)
l_start = random.randint(0, N_L - N_V)
l_sub_full = l_full[l_start:l_start+N_V]
vigenere_base = l_sub_full[:min(5000, len(l_sub_full))]  # Vigenère on first 5k for speed

sigs_full = {
    "Voynich FULL":    sig(v_full),
    "Latin (Perseus)": sig(l_sub_full),
    "Vigenère/Latin":  sig(make_vigenere(l_sub_full[:N_V])),
    "PCFG Grammar":    sig(make_pcfg(N_V)),
    "Zipf Random":     sig(make_zipf(N_V)),
}

hdr = f"  {'Corpus':<18}|{'States':>8}|{'Det@95':>8}|{'BE':>8}|{'BPG':>7}|{'PBias':>8}|{'NMI':>8}|{'Δ Voyn':>9}"
print(hdr); print("  "+"-"*(len(hdr)-2))
v = sigs_full["Voynich FULL"]
for name, s in sigs_full.items():
    d = eucl(s,v) if name != "Voynich FULL" else 0
    mark = "  ◄" if d==0 else f" {d:>8.4f}"
    print(f"  {name:<18}|{s['states']:>8}|{s['det95']:>7.1%}|{s['be']:>8.4f}|{s['bpg']:>7.3f}|{s['pb']:>8.4f}|{s['nmi']:>8.4f}|{mark}")

# Heaps' Law growth curve — both corpora growing from same start
print("\n" + "="*72)
print("HEAPS' LAW CURVE: Voynich vs Real Latin (both truly growing)")
print("="*72)
print(f"  {'N':>8} | {'V States':>8} | {'V BE':>7} | {'L States':>9} | {'L BE':>7}")
print("  "+"-"*55)
for N in [500, 937, 2000, 5000, 10000, 50000, 100000, 193960]:
    if N > min(N_V, N_L): break
    random.seed(42)
    vs = random.randint(0, N_V-N); v_sub = v_full[vs:vs+N]
    ls = random.randint(0, N_L-N); l_sub = l_full[ls:ls+N]
    sv=sig(v_sub); sl=sig(l_sub)
    print(f"  {N:>8,} | {sv['states']:>8} | {sv['be']:>7.4f} | {sl['states']:>9} | {sl['be']:>7.4f}")

# Final per-metric discrimination at N=193960
print("\n" + "="*72)
print("PER-METRIC DISCRIMINATION: Voynich vs Latin (N=193,960 each)")
print("="*72)
keys = [("BE","be"), ("Det@95%","det95"), ("BPG","bpg"), ("PosBias","pb"), ("NMI","nmi")]
l_s = sigs_full["Latin (Perseus)"]
for label, k in keys:
    gap = abs(v[k]-l_s[k])
    status = "DISTINCT ✓" if gap > 0.05 else "OVERLAP  ✗"
    print(f"  {label:>10}: Voynich={v[k]:.4f}  Latin={l_s[k]:.4f}  gap={gap:.4f}  {status}")

if __name__ == "__main__":
    pass
