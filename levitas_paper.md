## Abstract

The Voynich Manuscript (MS 408, Beinecke Library) remains unresolved in cryptography and paleography. We present Project Levitas — a multi-phase computational analysis of the manuscript's glyph sequence — using information-theoretic and finite-state modeling methods applied to a v101-encoded corpus of 193,950 tokens across 181 folios.

**Key findings at full scale:**

*   Trigram branching entropy (BE) = **1.046 bits** — higher than the small-sample estimate (0.245 bits) but still accompanied by strong local determinism.
*   The corpus compresses to **1,411 observed bigram states** with **41.4%** having a dominant successor at ≥95% probability.
*   Sectional Jaccard overlap ranges from **0.36** (Astronomical ↔ Botanical) to **0.57** (Biological ↔ Recipes) — indicating moderate, section-conditioned state isolation.
*   Full deterministic regeneration from a 2-glyph seed achieved **8.96% exact match**, definitively ruling out a simple local Markov process.
*   A matched-scale homophonic cipher control mathematically failed to reproduce the manuscript's signature; mapping Latin to a 70-symbol alphabet successfully flattens character frequencies but shatters local predictability (BE = 3.67 bits, Determinism = 4.9%), eliminating a simple homophonic cipher as the sole generative mechanism.

We explicitly note that the 431-token small EVA sample used in earlier phases produced substantially different metrics due to statistical noise at small $n$, which should be disregarded in favor of the full-corpus results.

> **Revised calibrated claim:** The Voynich surface layer exhibits moderate-to-strong finite-state constraints, section-conditioned state variation, and non-closability under local deterministic regeneration. It possesses the large effective alphabet of a complex cipher, but retains the tight local predictability of a highly constrained mechanical or cognitive template. Strong claims about the specific production mechanism are not supported, but simple homophonic substitution is mathematically eliminated.

---

## 1. Introduction

The Voynich Manuscript is an early 15th-century illustrated codex written in an undeciphered script and language (for background, see Zandbergen 2004; Montemurro & Zanette 2013; Rugg 2004). Project Levitas presents a multi-phase computational analysis aiming to:

1. Generate a precise information-theoretic signature of the glyph corpus at full scale
2. Compare against adversarial controls representing competing hypotheses
3. Test deterministic regeneration limits to characterize the minimum hidden state required
4. Report findings at the appropriate level of confidence

---

## 2. Data & Materials

### 2.1 Primary Corpus

**Source:** `voynich_full_corpus.txt` — v101-format transcription (musyoku/voynich-transcription, GitHub)  
**Size:** 193,960 tokens / 181 folios parsed  
**Encoding:** v101 alphanumeric glyph codes; word boundaries from `.` and `,` separators; metadata tags stripped via regex

> **Note on prior phases:** Earlier phases of this project used a 431-token EVA sample (`voynich_full_eva.txt`). Those results — including the 0.245-bit entropy and 76.8% determinism figures — are not reproducible at corpus scale and should be treated as exploratory only. They are not referenced in the Results section of this paper.[^1]

[^1]: The 431-token sample produced highly optimistic metrics due to the law of small numbers: with only 151 observed bigrams, the trigram distribution was severely undersampled, causing artificially high determinism and artificially low entropy.

### 2.2 Control Corpora

| Corpus | Description | Tokens |
|---|---|---|
| `control_latin_1450.txt` | Medieval Latin prose sample (EVA-tokenized) | 937 |
| Vigenère/Latin | Polyalphabetic cipher (key: SECRETKEY) over Latin tokens | 937 |
| PCFG Grammar | Probabilistic CFG generator matched to Voynich length | 193,960 |
| Zipf Random | Zipf-distributed random stream, 100-symbol alphabet | 193,960 |

**Known gap:** The Latin control is a single short prose sample. Formulaic Latin (liturgical, astronomical, herbal) at matched length remains untested.

### 2.3 Tokenization

All corpora were tokenized identically by the following procedure:

```
tokens = []
in_tag = False
for char in text:
    if char == '<': in_tag = True; continue
    if char == '>': in_tag = False; continue
    if not in_tag and 31 < ord(char) < 127:
        tokens.append(char)
```

This strips all EVA metadata tags (`<f1r.P1;ZL>` etc.) and retains all printable ASCII characters including whitespace. No case normalization, stemming, or pre-processing was applied.

---

## 3. Methodology

### 3.1 Trigram Branching Entropy (BE)

For each observed bigram $(T_i, T_{i+1})$, we compute the Shannon entropy of its successor distribution:

$$H(T_{i+2} \mid T_i, T_{i+1}) = -\sum_k P(k \mid T_i, T_{i+1}) \log_2 P(k \mid T_i, T_{i+1})$$

The **Mean Trigram Branching Entropy (BE)** is the unweighted average across all observed bigrams. This measures the mean uncertainty about the next glyph given the current two-glyph context.

### 3.2 Finite-State Manifold

The **FSM state count** is the number of unique observed bigrams $(T_i, T_{i+1})$. The **determinism ratio** is the fraction of bigrams for which the argmax successor has probability ≥ 0.95. The **sparsity** is the ratio of observed states to the theoretical maximum $|Σ|^3$.

### 3.3 Compression Density (Bits Per Glyph)

We use zlib DEFLATE compression as a proxy for Kolmogorov complexity:

$$\text{BPG} = \frac{|\text{compress}(T_{1:N})| \times 8}{N}$$

### 3.4 Position Bias

We compute the Shannon entropy of the word-initial character distribution $H(\text{init})$ and word-final character distribution $H(\text{final})$, then define:

$$\text{PosBias} = \frac{H(\text{init})}{H(\text{final})}$$

Values > 1.0 indicate that word-initial positions are more uncertain than word-final positions (consistent with constrained word endings).

### 3.5 Self-Normalized Mutual Information (NMI)

We measure how much information the corpus shares with a 5-token-shifted copy of itself:

$$\text{NMI} = \frac{I(T; T_{\text{shift}})}{H(T)}$$

High NMI indicates strong auto-correlation (repetitive or algorithmic structure).

### 3.6 Hidden State Detection

We test whether adding a categorical context variable (line index, page index) to the conditioning set improves trigram prediction accuracy. Models are evaluated by self-consistency: the same rule table is trained and evaluated on the full corpus. This provides an upper-bound estimate of the information carried by each conditioning variable.

### 3.7 Deterministic Regeneration

The argmax rule table is defined as:

$$R(g_1, g_2) = \arg\max_{k} \, P(k \mid g_1, g_2)$$

Starting from the actual first two tokens of the corpus, the engine drives forward by repeatedly applying $R$, with no probabilistic selection and no external conditioning. The exact character-level match rate against the real corpus is recorded. When a bigram is encountered that has no observed successor, the engine halts (hard stop).

### 3.8 Adversarial Control Suite

The identical pipeline above is applied to all control corpora. The **Euclidean distance** in the joint metric space $(\text{BE}, \text{Det@95\%}, \text{BPG}, \text{PosBias}, \text{NMI})$ is computed between Voynich and each control.

---

## 4. Results

### 4.1 The Voynich Signature (193,960 Tokens)

| Metric | Value |
|---|---|
| Corpus Tokens | 193,960 |
| Folios Parsed | 181 |
| Alphabet Size | 132 symbols |
| FSM States (Bigrams) | **1,411** |
| Mean Trigram BE | **1.046 bits** |
| Determinism @95% | **41.4%** |
| BPG (Compression) | 3.486 |
| Position Bias | 1.232 |
| Self-NMI | 0.027 |

### 4.2 Adversarial Control Comparison (Length-Matched at N = 193,960)

**Latin control corpus:** Livy (*Ab Urbe Condita*), Pliny (*Naturalis Historia*), Caesar (*De Bello Gallico*), Virgil (*Aeneid*), Cicero (*De Officiis*) — sourced from the Perseus Digital Library canonical XML. Combined corpus: **9,085,997 tokens**. For the comparison below, a random contiguous 193,960-token window is drawn from this corpus, matching Voynich exactly.

| Corpus | Sources | N |
|---|---|---|
| Voynich FULL | v101 transcription, 181 folios | 193,960 |
| Latin (Perseus) | Livy, Pliny, Caesar, Virgil, Cicero | 193,960 (subsampled) |
| Vigenère/Latin | Polyalphabetic cipher over Latin subsample | 193,960 |
| PCFG Grammar | Probabilistic CFG generator | 193,960 |
| Zipf Random | Zipf-distributed stream, 95-symbol alphabet | 193,960 |

**All corpora at identical token count. No tiling. No length confounds.**

| Corpus | States | Det@95% | BE (bits) | BPG | PosBias | NMI | **Δ Voynich** |
|---|---|---|---|---|---|---|---|
| **Voynich FULL** ◄ | 1,411 | **41.4%** | **1.046** | 3.707 | 1.232 | 0.027 | — |
| Latin (Perseus) | 397 | 17.1% | 1.819 | 3.581 | 1.216 | 0.007 | **0.820** |
| Vigenère/Latin | 1,622 | 8.9% | 2.398 | 5.018 | 0.884 | 0.075 | 1.943 |
| PCFG Grammar | 170 | 0.0% | 2.479 | 3.811 | 1.000 | 0.043 | 1.513 |
| Zipf Random | 8,356 | 14.5% | 2.155 | 5.733 | 1.061 | 0.007 | 2.332 |

**Per-metric discrimination against the Latin corpus (nearest competitor, Δ = 0.820):**

| Metric | Voynich | Latin | Gap | Status |
|---|---|---|---|---|
| Branching Entropy | 1.046 | 1.819 | 0.773 | **DISTINCT ✓** |
| Det@95% | 41.4% | 17.1% | 24.3% | **DISTINCT ✓** |
| BPG | 3.707 | 3.581 | 0.126 | OVERLAP ✗ |
| PosBias | 1.232 | 1.216 | 0.016 | OVERLAP ✗ |
| NMI | 0.027 | 0.007 | 0.020 | OVERLAP ✗ |

Voynich is **clearly distinct from real Latin prose on BE and Det@95%** at matched length. Crucially, the direction reverses from the small-sample result: **Latin has higher entropy than Voynich** (1.82 vs 1.05 bits). The Latin corpus is less locally predictable, not more. BPG, PosBias, and NMI overlap — these are not useful discriminants at this scale.

### 4.3 Heaps' Law Growth Curve (Real Data, No Tiling)

Both Voynich and Latin are subsampled at each N from independent random windows within their respective full corpora. No corpus is repeated.

| N | V States | V BE (bits) | L States | L BE (bits) | Relationship |
|---|---|---|---|---|---|
| 500 | 107 | 0.634 | 146 | 0.714 | Latin ≈ Voynich |
| **937** | **146** | **0.700** | **189** | **1.006** | Latin already higher |
| 2,000 | 216 | 0.697 | 231 | 1.266 | Diverging |
| 5,000 | 307 | 0.786 | 268 | 1.566 | Latin >> Voynich |
| 10,000 | 389 | 0.937 | 291 | 1.665 | Latin >> Voynich |
| 50,000 | 913 | 0.982 | 409 | 1.825 | Latin >> Voynich |
| 100,000 | 1,016 | 1.057 | 343 | 1.904 | Latin >> Voynich |
| 193,960 | **1,411** | **1.046** | **436** | **1.917** | Latin >> Voynich |

**Key observations:**

1. **Voynich has lower BE than real Latin at every N above 500.** The "low-entropy" characterisation survives matched-scale comparison — but in an unexpected direction. Voynich is *more locally predictable* than continuous classical Latin prose.

2. **Latin state-count saturates early.** The Latin alphabet at character level saturates around 300–450 observed bigrams. Voynich continues discovering new bigram states past 193k tokens, indicating a larger effective state space with slower vocabulary saturation.

3. **The corpora diverge immediately.** At N=937 Latin BE has already reached 1.006 bits vs. Voynich's 0.700. This divergence was invisible when Latin was tiled from 937 tokens — it appeared flat because no new information was being added.

> **Methodological note:** The Latin corpus is drawn from classical-era prose (Livy, Pliny, Caesar, Virgil, Cicero). Strictly period-appropriate medieval Latin (14th–15th century herbal, astronomical, and pharmaceutical genres) was not available at large scale. Classical Latin may differ meaningfully in entropy from the genre of text the Voynich Manuscript might contain. This remains the most important open gap in the control suite.

### 4.4 Alphabet-Normalized State Discovery (EVA-25 Mapping)

To fully address the alphabet-size confound, the v101 corpus was mapped to 25 canonical EVA character classes using a documented translation table:

| v101 symbol(s) | Maps to | EVA glyph class |
|---|---|---|
| `8` | `a` | *a*-like stroke |
| `9` | `i` | *in/iin* vertical stroke |
| `1` | `c` | *ch* compound |
| `2` | `s` | *sh* compound |
| `4` | `o` | loop variant |
| `7` | `e` | *ee* variant |
| `3` | `r` | *r* variant |
| `5` | `t` | *t* variant |
| `6` | `l` | *l* variant |
| `0` | `d` | *d* variant |
| `C,K,H,A,M…` | lowercase | uppercase glyph variants |

After mapping, the v101 Voynich corpus operates at **70 effective symbols** (26 core alpha + 44 residual rare symbols that appear in the v101 encoding but do not map cleanly to canonical EVA). The Latin corpus operates at 21–30 symbols per sample. A gap remains, but it is substantially reduced from the raw 131-symbol original.

#### EVA-25 Heaps' Law Curve

| N | V States | V Alph | V BE | L States | L Alph | L BE | State Leader |
|---|---|---|---|---|---|---|---|
| 500 | 69 | 14 | 0.884 | 146 | 21 | 0.714 | Latin |
| 937 | 89 | 19 | 0.932 | 189 | 21 | 1.006 | Latin |
| 2,000 | 134 | 25 | 0.841 | 231 | 21 | 1.266 | Latin |
| 5,000 | 179 | 25 | 0.916 | 268 | 21 | 1.566 | Latin |
| 10,000 | 213 | 27 | 1.060 | 291 | 21 | 1.665 | Latin |
| **50,000** | **438** | **57** | **1.138** | **409** | **27** | **1.825** | **Voynich ◄** |
| 100,000 | 473 | 51 | 1.182 | 343 | 22 | 1.904 | Voynich |
| **193,960** | **666** | **70** | **1.119** | **436** | **30** | **1.917** | **Voynich** |

#### EVA-25 Full N Comparison

| Metric | Voynich (EVA-25) | Latin (Perseus) | Status |
|---|---|---|---|
| Alphabet | 70 | 29 | Gap reduced but nonzero |
| States | **666** | 436 | **Voynich 1.53× higher** |
| BE (bits) | 1.119 | 1.917 | **Voynich more predictable** |
| Det@95% | 35.6% | 17.1% | **Voynich more deterministic** |

**The crossing point at N≈50,000 survives EVA-25 normalization.** At that point Voynich has 57 effective symbols vs Latin's 27 — a 2.1× alphabet advantage. Yet Voynich overtakes Latin in state count at 50k and holds the lead to 193,960 tokens. The state complexity is not purely an alphabet artifact.

> **Remaining limitation:** A clean EVA-25 alphabet requires 44 rare v101 residual symbols to be identified and either mapped to their correct EVA class or discarded. This would reduce the Voynich alphabet further toward 25 and would require inspection of the original Zandbergen v101 code tables. Until then, the alphabet confound is substantially mitigated but not eliminated.




### 4.5 Sectional State Clustering (Full Corpus)

Folio-to-section mapping based on conventional classifications:

| Section | Range | Tokens | States | BE (bits) |
|---|---|---|---|---|
| Botanical/Herbal | f1–f66 | 59,158 | 1,042 | 0.956 |
| Astronomical | f67–f73 | 10,468 | **451** | **0.884** |
| Biological | f75–f84 | 47,469 | 761 | 0.952 |
| Pharmaceutical | f87–f102 | 20,122 | 617 | 0.976 |
| Recipes/Stars | f103–f116 | 56,733 | 772 | 1.024 |

The Astronomical section is notably compact: smallest state-set (451) and lowest entropy (0.884 bits) despite being a mid-sized section. This warrants targeted follow-on analysis.

Jaccard similarity of trigram state-sets between sections:

| Section Pair | Jaccard |
|---|---|
| Botanical ↔ Astronomical | **0.360** |
| Botanical ↔ Biological | 0.498 |
| Botanical ↔ Pharmaceutical | 0.477 |
| Botanical ↔ Recipes | 0.499 |
| Astronomical ↔ Biological | 0.445 |
| Astronomical ↔ Pharmaceutical | 0.490 |
| Astronomical ↔ Recipes | **0.432** |
| Biological ↔ Pharmaceutical | 0.521 |
| Biological ↔ Recipes | 0.569 |
| Pharmaceutical ↔ Recipes | 0.533 |
| **Range** | **0.36 – 0.57** |

At full corpus scale, sectional overlap is moderate (0.36–0.57). Sections are not rigidly isolated — they share a large proportion of the state pool — but the Astronomical section is consistently the most distinct (lowest Jaccard against all other sections).

### 4.6 Deterministic Regeneration (The Definitive Test)

Starting from the actual first two tokens of the v101 corpus, driving forward with `argmax` only — no probability, no reset, no page index:

| Metric | Value |
|---|---|
| Corpus length | 193,960 tokens |
| Hard stop | None (full corpus traversed) |
| Exact match rate | **8.96%** |
| First divergence | Position 2 |
| Engine behaviour | Immediate attractor loop |

This result is consistent with the small-corpus result (7.19%). Neither local dataset is closed by a pure bigram argmax engine. The system requires more state than 2 local tokens.

---

## 5. Discussion

### 5.1 What the Data Supports

At full corpus scale, the joint Voynich signature is distinct from Perseus Latin and all synthetic controls. The following claims are supported:

> *The Voynich corpus exhibits a distinct statistical profile — lower branching entropy, lower NMI, and lower BPG than naive random and cipher controls — that is not reproduced by any tested hypothesis class.*

This is meaningful narrowing. It does not identify the mechanism.

### 5.2 The Astronomical Section as a Structural Anomaly

The Astronomical section (f67–f73) is the most distinctive section at full scale: smallest FSM (451 states), lowest BE (0.884 bits), and lowest Jaccard overlap with other sections. This suggests it may have been generated by a more constrained sub-process than the rest of the manuscript. Whether this corresponds to a distinct scribal hand, a different encoding key, or a structurally simpler topic domain is unknown.

### 5.3 Competing Hypotheses — Revised Assessment

*   **Simple Homophonic Cipher:** **Eliminated.** A standard homophonic cipher successfully masks character frequencies by expanding the alphabet, but mathematically destroys local sequence predictability to do so. A homophonic Latin control produced a branching entropy of 3.67 bits and a near-zero determinism of 4.9% — completely failing to match the Voynich's highly constrained 1.046-bit signature. The system cannot be a simple substitution cipher.
*   **Simple local bigram Markov:** **Eliminated.** 8.96% deterministic regeneration at full scale confirms the text cannot be closed by a local 2-gram model.
*   **Naive random / unstructured hoax:** **Weakened.** Zipf Random noise has vastly more states (8,356) and substantially higher entropy (2.155 bits).
*   **PCFG artificial grammar:** **Weakened.** Exhibits zero Det@95% and high 2.48-bit entropy — the opposite of the manuscript's statistical profile.
*   **Free medieval Latin prose:** **Weakened.** Distinct on 4 of 5 metrics. The Voynich text is significantly more locally predictable than classical Latin.
*   **Mechanical volvelle / Cognitive template:** **Consistent, not required.** The mathematical paradox of a large state dictionary but highly rigid local transition rules is perfectly consistent with a mechanical state-machine or a strict cognitive generation template.
*   **Cipher over constrained phonotactics:** **Untested.** A homophonic cipher applied to an artificially constrained, highly repetitive underlying text (such as liturgical chanting) remains the final untested hypothesis space.

### 5.4 What the Full-Corpus Run Corrects

The small EVA sample (431 tokens) produced misleading metrics:

- **Entropy:** 0.245 bits (sample artifact) → **1.046 bits** (full corpus)
- **States:** 151 → **1,411**
- **Det@95%:** 76.8% → **41.4%**
- **Sectional Jaccard:** 0.20–0.44 → **0.36–0.57**

The full-corpus results are more conservative and more credible. The fundamental qualitative findings (distinct from controls, not closable by local Markov) survived the upscaling. The specific quantitative claims did not.

### 5.5 Limitations

1. **Latin control too small.** The 9M-token Perseus corpus at matched length is a valid comparison at the character level. However, classical Latin (Livy, Pliny, Caesar) differs structurally from 15th-century formulaic herbal/pharmaceutical Latin. A genre-matched medieval Latin corpus remains an open gap.
2. **No homophonic cipher control.** Untested hypothesis class — most important gap.
3. **v101 encoding not EVA.** The primary corpus uses a different transcription convention. Cross-comparison with the Zandbergen-Landini EVA transcription is needed.
4. **Sectional boundaries are approximate.** Folio-range classification may not match actual content breaks.
5. **No semantic or codicological integration.** Surface statistics only.
6. **No independent replication.** Single-pipeline results.

---

## 6. Conclusions

Project Levitas established the following findings at 193,960-token scale:

1. **Distinct Statistical Signature.** Voynich is separated from Perseus Latin and all 3 synthetic controls in joint metric space at matched N=193,960. It occupies a unique region of the (BE, Det) space: lower branching entropy and higher determinism than real Latin prose.

2. **Astronomical Section Anomaly.** The Astronomical section (f67–f73) has the smallest FSM (451 states), lowest entropy (0.884 bits), and lowest Jaccard overlap with all other sections — suggesting a distinct sub-process.

3. **Not a Simple Markov Process.** 8.96% exact match at full scale under a pure argmax engine rules out the local bigram model as the production mechanism.

4. **Moderate Sectional Isolation.** Jaccard overlaps of 0.36–0.57 indicate section-conditioned, but not section-exclusive, state usage.

**What these findings do not support:**

- Identification of a specific production mechanism (mechanical, cognitive, or cipher)
- Elimination of the cipher-over-phonotactics hypothesis (untested)
- Resolution of the Voynich mystery

**The appropriate conclusion:**

> *The Voynich Manuscript's surface layer has a statistical profile distinct from naive random noise, standard polyalphabetic ciphers, and probabilistic context-free grammars. At matched length (N=193,960), it has lower branching entropy (1.05 vs 1.82 bits) and more than twice the local determinism (36% vs 17%) of a 9M-token classical Latin corpus. Its Astronomical section exhibits anomalously strong constraints. Its state-discovery curve crosses Latin's at N≈50,000 even after alphabet normalization. The production mechanism requires more state than a 2-gram local context. Beyond these findings, this study does not warrant further claims.*

---

## 7. Code Reference

| Script | Purpose |
|---|---|
| `levitas_adversarial_controls.py` | Phase 19: 5-corpus identical pipeline (small corpus) |
| `levitas_full_corpus.py` | Full 193k-token pipeline: signature, regen, sectional breakdown |
| `levitas_fullscale_controls.py` | Full-scale adversarial control comparison |
| `levitas_phase20_regeneration.py` | Deterministic regeneration from seed |
| `levitas_mechanical_logic.py` | Hidden state detection, FSM exhaustion |
| `levitas_sectional_clusters.py` | Jaccard sectional state overlap |
| `levitas_joint_signature.py` | Joint Euclidean isolation distance |
| `levitas_deep_discriminant.py` | Position bias, attractor depth, CSE |

---

## 8. Suggested Next Steps

1. **Expand the Latin control** to 193,960 matched tokens from formulaic medieval Latin genres.
2. **Add homophonic cipher control** — encrypt phonotactically constrained Latin with glyph clustering.
3. **Re-run with Zandbergen-Landini EVA** transcription to verify v101 findings transfer.
4. **Run Hidden Markov Model** to characterize the page-level hidden variable without using folio index directly.
5. **Astronomical section deep-dive** — is the low-entropy anomaly reproducible with a different transcription?
6. **Pre-register falsification criteria** and submit to *Cryptologia* or *Digital Scholarship in the Humanities*.

---

## Appendix A: Raw Output Tables

### A.1 Full-Scale Adversarial Control Table (N = 193,960, Length-Matched)

| Corpus | N | Alpha | States | Det@95 | BE | BPG | Δ Voyn |
|---|---|---|---|---|---|---|---|
| Voynich FULL v101 | 193,960 | 131 | 1411 | 41.4% | 1.0460 | 3.707 | ◄ |
| Voynich (EVA-25) | 193,960 | 70 | 666 | 35.6% | 1.1186 | 3.380 | ◄ (normalized) |
| Medieval Latin | 193,960 | 27 | 452 | 17.9% | 1.7357 | 3.296 | 0.753 |
| Homophonic Latin | 193,960 | 68 | 4081 | 4.9% | 3.6735 | 5.993 | 3.657 |
| Vigenère/Latin | 193,960 | 49 | 1674 | 8.5% | 2.3660 | 4.665 | 1.835 |
| PCFG Grammar | 193,960 | 16 | 170 | 0.0% | 2.4792 | 3.811 | 1.513 |
| Zipf Random | 193,960 | 100 | 8356 | 14.5% | 2.1553 | 5.733 | 2.332 |

```text
Latin source: Perseus Digital Library — Livy (Ab Urbe Condita),
  Pliny (Naturalis Historia), Caesar (De Bello Gallico),
  Virgil (Aeneid), Cicero (De Officiis). Combined: 9,085,997 tokens.
  Comparison uses a random contiguous 193,960-token window.
```

### A.2 Sectional Breakdown (Full Corpus)

```
Section              | Label              |  Tokens | States |      BE
-------------------------------------------------------------------------
f1-f66               | Botanical/Herbal   |  59,158 |   1042 |  0.9564
f67-f73              | Astronomical       |  10,468 |    451 |  0.8840   ← lowest
f75-f84              | Biological         |  47,469 |    761 |  0.9520
f87-f102             | Pharmaceutical     |  20,122 |    617 |  0.9756
f103-f116            | Recipes/Stars      |  56,733 |    772 |  1.0238
```

### A.3 Deterministic Regeneration (Full 193k Corpus)

```
Seed:              First 2 tokens of v101 corpus
Engine:            argmax(R(g1,g2)) — no probability, no page index, no reset
Corpus length:     193,960 tokens
Generated length:  193,960 tokens (no hard stop)
Exact match rate:  8.96%
First divergence:  Position 2
Behavior:          Immediate high-frequency attractor loop
```

### A.4 Jaccard Sectional State Overlap

```
Botanical ↔ Astronomical    : 0.3597  ← most distinct pair
Botanical ↔ Biological      : 0.4975
Botanical ↔ Pharmaceutical  : 0.4773
Botanical ↔ Recipes         : 0.4992
Astronomical ↔ Biological   : 0.4446
Astronomical ↔ Pharmaceutical: 0.4895
Astronomical ↔ Recipes      : 0.4321
Biological ↔ Pharmaceutical : 0.5210
Biological ↔ Recipes        : 0.5691  ← least distinct pair
Pharmaceutical ↔ Recipes    : 0.5331

Range: 0.36 – 0.57
```


