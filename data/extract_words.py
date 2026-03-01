import collections
import re

with open("vulgate_latin.txt") as f:
    text = f.read().lower()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    counts = collections.Counter(words)
    # Get top 5000 common words
    with open("latin_dictionary.txt", "w") as out:
        for word, _ in counts.most_common(5000):
            out.write(word + "\n")
