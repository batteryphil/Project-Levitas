import random
import collections

# Load the entire Latin Vulgate for maximum statistical stability
LATIN_PATH = "/home/phil/.gemini/antigravity/scratch/levitas-engine/data/vulgate_latin.txt"
with open(LATIN_PATH) as f:
    lines = f.readlines()[50:] # Skip English header
    PLAINTEXT = "".join(lines).lower().replace(' ', '')
    # Filter for alnum only to be safe
    PLAINTEXT = "".join([c for c in PLAINTEXT if c.isalnum()])

# Dimensions of our 'Hidden Mechanism' (A 3x2 Grid)
SECRET_W = 3
SECRET_H = 2

# We create 6 unique substitution alphabets (The 6 'Holes' in the Grille)
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
SECRET_MAPS = []
for i in range(SECRET_W * SECRET_H):
    shuffled = list(ALPHABET)
    random.seed(i + 42) # Deterministic for testing
    random.shuffle(shuffled)
    SECRET_MAPS.append(dict(zip(ALPHABET, shuffled)))

def encrypt_grille(text, w, h):
    ciphertext = []
    for idx, char in enumerate(text):
        if char not in ALPHABET: continue
        line_idx = idx // 20 # Simulate 20-char lines
        pos_idx = idx % 20
        
        cell_id = (line_idx % h) * w + (pos_idx % w)
        ciphertext.append(SECRET_MAPS[cell_id][char])
    return "".join(ciphertext)

if __name__ == "__main__":
    print(f"Generating 'Cracked Cipher' Ground Truth...")
    print(f"Secret Dimensions: W={SECRET_W}, H={SECRET_H}")
    
    cipher_text = encrypt_grille(PLAINTEXT, SECRET_W, SECRET_H)
    
    # Save as a pseudo-Voynich file for the pipeline to consume
    with open("cracked_cipher_input.txt", "w") as f:
        # Format it so the parse_with_2d_context can read it: <1.1>body
        chars_per_line = 20
        for i in range(0, len(cipher_text), chars_per_line):
            line_content = cipher_text[i:i+chars_per_line]
            line_num = (i // chars_per_line) + 1
            f.write(f"<999.{line_num}>{line_content}\n")
            
    print(f"Ciphertext generated and saved to 'cracked_cipher_input.txt'")
    print(f"Snippet: {cipher_text[:40]}...")
