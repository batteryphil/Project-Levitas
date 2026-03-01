import re
import difflib
import sys

# Dictionary Anchor (Targeting Folio 67 themes)
LEXICON = [
    "stella", "solis", "luna", "ventus", "gradus", "manere", "astra",
    "istam", "senum", "sensum", "esset", "belgae", "gallia", "divisa",
    "omnis", "partes", "tres", "quarum", "unam", "incolunt"
]

def strip_gear_lash(text):
    """
    Identifies repeating character runs that exceed natural Latin phonotactics
    (e.g., ssss -> s) and treats them as mechanical spacers.
    """
    # Collapse any sequence of 3 or more identical characters into one
    return re.sub(r'(.)\1{2,}', r'\1', text)

def find_closest_match(word, lexicon, threshold=0.7):
    """
    Finds the closest match in the lexicon using a similarity threshold.
    """
    matches = difflib.get_close_matches(word, lexicon, n=1, cutoff=threshold)
    return matches[0] if matches else None

def lexical_anchor_filter(decoded_text):
    """
    Cleans mechanical noise and snaps sequences to the closest Latin terms.
    """
    # Step 1: Gear-lash removal
    cleaned = strip_gear_lash(decoded_text)
    
    # Step 2: Snap-to-Lexicon
    final_output = []
    for word in cleaned.split():
        # Clean word-specific junk
        w_clean = re.sub(r'[^a-z]', '', word.lower())
        if len(w_clean) < 3:
            final_output.append(word)
            continue
            
        match = find_closest_match(w_clean, LEXICON)
        if match:
            # Preserve case if original was caps (simplified)
            if word.isupper():
                final_output.append(match.upper())
            else:
                final_output.append(match)
        else:
            final_output.append(word)
            
    return " ".join(final_output)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            content = f.read()
        print(lexical_anchor_filter(content))
    else:
        # Test case
        test_str = "stam senim sensm esed steeeeit"
        print(f"Original: {test_str}")
        print(f"Filtered: {lexical_anchor_filter(test_str)}")
