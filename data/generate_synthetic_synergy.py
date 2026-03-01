import random

def generate_grid_reset_corpus(output_path, lines=100, cols=40):
    # A 4x2 grid of substitution rules
    # Each cell (r, c) has a different transition matrix
    # For simplicity: char = (prev_char + grid_value) % 26
    grid = [
        [3, 7],
        [1, 5],
        [2, 0],
        [4, 6]
    ]
    
    with open(output_path, "w") as f:
        for r in range(lines):
            line = []
            prev_char = random.randint(0, 25)
            line.append(chr(ord('a') + prev_char))
            
            for c in range(1, cols):
                grid_val = grid[r % 4][c % 2]
                curr_char = (prev_char + grid_val) % 26
                line.append(chr(ord('a') + curr_char))
                prev_char = curr_char
            
            f.write("".join(line) + "\n")

if __name__ == "__main__":
    generate_grid_reset_corpus("/home/phil/.gemini/antigravity/scratch/levitas-engine/data/synthetic_grid_reset.txt")
