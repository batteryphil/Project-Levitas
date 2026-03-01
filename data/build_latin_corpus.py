"""
Build a large Latin control corpus from Perseus Digital Library canonical texts.
Downloads multiple Latin works and concatenates them, stripping XML tags.
Target: ~200,000 tokens of continuous medieval/classical Latin.
"""
import urllib.request, re, os, sys

DATA_DIR = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data"

# Perseus canonical Latin texts — large works
URLS = [
    # Vulgate (New Testament)
    ("https://raw.githubusercontent.com/cltk/latin_text_perseus/master/txt/Latin.txt", "cltk_latin.txt"),
    # Cicero - De Officiis (large)
    ("https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data/phi0474/phi021/phi0474.phi021.perseus-lat2.xml", "cicero_deofficiis.xml"),
    # Caesar - De Bello Gallico
    ("https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data/phi0448/phi001/phi0448.phi001.perseus-lat2.xml", "caesar_dbg.xml"),
    # Virgil - Aeneid
    ("https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data/phi0690/phi003/phi0690.phi003.perseus-lat2.xml", "virgil_aeneid.xml"),
    # Livy - Ab Urbe Condita Book 1
    ("https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data/phi0914/phi001/phi0914.phi001.perseus-lat2.xml", "livy_auc.xml"),
    # Tacitus - Annals
    ("https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data/phi1351/phi005/phi1351.phi005.perseus-lat2.xml", "tacitus_annals.xml"),
    # Sallust - Bellum Catilinae
    ("https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data/phi0631/phi001/phi0631.phi001.perseus-lat2.xml", "sallust.xml"),
    # Pliny - Naturalis Historia (book 1)
    ("https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data/phi0978/phi001/phi0978.phi001.perseus-lat2.xml", "pliny_nh.xml"),
]

def strip_xml(text):
    """Remove all XML/HTML tags and normalize whitespace."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

combined = []
total_chars = 0

for url, fname in URLS:
    out_path = os.path.join(DATA_DIR, fname)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="replace")
        with open(out_path, "w") as f:
            f.write(raw)
        cleaned = strip_xml(raw)
        combined.append(cleaned)
        total_chars += len(cleaned)
        print(f"  OK  {fname:<30} {len(cleaned):>9,} chars")
    except Exception as e:
        print(f"  FAIL {fname:<30} {str(e)[:50]}")

# Concatenate all
mega = " ".join(combined)
# Tokenize same way as Voynich v101 (alphanumeric + space separators)
tokens = []
for ch in mega:
    if ch.isalpha():  # Latin uses only alpha chars
        tokens.append(ch.lower())
    elif ch in ' \t\n' and tokens and tokens[-1] != ' ':
        tokens.append(' ')

print(f"\nTotal concatenated:  {total_chars:,} chars")
print(f"Tokens extracted:    {len(tokens):,}")

# Save
tok_path = os.path.join(DATA_DIR, "latin_control_large.txt")
with open(tok_path, "w") as f:
    f.write("".join(tokens))
print(f"Saved to: {tok_path}")
