import collections
import re
import json

FUNCTION_WORDS = ["et", "in", "est", "non", "ad", "cum", "sed", "si", "ac", "ut"]

def audit_decryption(text_path):
    with open(text_path) as f:
        text = f.read()
    
    # Split specifically into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    total_words = len(words)
    counts = collections.Counter(words)
    
    print("=" * 70)
    print("LATIN GRAMMATICAL AUDIT (PHASE 10)")
    print("-" * 70)
    print(f"Total Words Analyzed: {total_words}")
    print("-" * 70)
    print(f"{'Word':<10} | {'Count':<10} | {'Frequency'}")
    print("-" * 70)
    
    found_any = False
    for fw in FUNCTION_WORDS:
        count = counts[fw]
        if count > 0:
            freq = (count / total_words) * 100
            print(f"{fw:<10} | {count:<10} | {freq:.2f}%")
            found_any = True
    
    if not found_any:
        print("No standard Latin functional words detected.")
    
    print("-" * 70)
    # Check for morphological suffix consistency (e.g. -am, -as, -is, -um)
    suffixes = ["am", "as", "is", "um", "es"]
    print("Morphological Suffix Profile:")
    for s in suffixes:
        s_count = sum(1 for w in words if w.endswith(s))
        s_freq = (s_count / total_words) * 100
        print(f"-{s:<9} | {s_count:<10} | {s_freq:.2f}%")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="stability_results_detailed.txt")
    args = parser.parse_args()
    audit_decryption(args.file)
