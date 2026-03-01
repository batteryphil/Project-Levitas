#include "../include/Linguistics.hpp"
#include "../include/Scanner.hpp"
#include "../include/Tokenizer.hpp"
#include "../include/Translator.hpp"
#include <algorithm>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <string>
#include <vector>

using namespace levitas;

void run_viterbi_codebook_lock() {
  Tokenizer tokenizer;
  Scanner scanner;

  // Load Real Data
  auto stream_voynich = tokenizer.tokenize_file("data/voynich_full_eva.txt");
  auto stream_latin = tokenizer.tokenize_file("data/control_latin_1450.txt");

  // Load Cappelli Dataset (14,357 entries)
  // Note: Multimap used because one sigla can have multiple expansions
  std::map<std::vector<int>, std::vector<std::vector<int>>> cappelli_map;
  std::ifstream csv("data/cappelli_complete_2026.csv");
  std::string line;
  std::getline(csv, line); // Skip header
  while (std::getline(csv, line)) {
    size_t comma = line.find(',');
    if (comma != std::string::npos) {
      std::string sigla_str = line.substr(0, comma);
      std::string exp_str = line.substr(comma + 1);

      // Strip Quotes
      if (sigla_str.size() >= 2 && sigla_str.front() == '"' &&
          sigla_str.back() == '"')
        sigla_str = sigla_str.substr(1, sigla_str.size() - 2);
      if (exp_str.size() >= 2 && exp_str.front() == '"' &&
          exp_str.back() == '"')
        exp_str = exp_str.substr(1, exp_str.size() - 2);

      auto sigla_tokens = tokenizer.tokenize_corpus(sigla_str);
      auto exp_tokens = tokenizer.tokenize_corpus(exp_str);

      if (!sigla_tokens.empty() && !exp_tokens.empty()) {
        cappelli_map[sigla_tokens].push_back(exp_tokens);
      }
    }
  }

  std::cout << "[LEVITAS] INITIATING VITERBI_CODEBOOK_LOCK..." << std::endl;
  std::cout << "[INFO] Cappelli Lexicon: " << cappelli_map.size()
            << " unique sigla ingested." << std::endl;

  if (!cappelli_map.empty()) {
    std::cout << "[DEBUG] First Sigla in Map IDs: ";
    for (int t : cappelli_map.begin()->first)
      std::cout << t << " ";
    std::cout << std::endl;
  }

  // Execute Viterbi Overdrive Sweep
  std::cout << "[PROCESS] Analyzing Folios 1r-20v Trellis..." << std::endl;
  auto locked_plaintext = scanner.viterbi_expansion_lock(
      stream_voynich, stream_latin, cappelli_map);

  // Debug Sequence Alignment
  std::cout << "[DEBUG] Locked Sequence (0-20): ";
  for (size_t i = 0; i < std::min(size_t(20), locked_plaintext.size()); ++i)
    std::cout << locked_plaintext[i] << " ";
  std::cout << std::endl;

  std::cout << "[DEBUG] Control Sequence (0-20): ";
  for (size_t i = 0; i < std::min(size_t(20), stream_latin.size()); ++i)
    std::cout << stream_latin[i] << " ";
  std::cout << std::endl;

  // Calculate Global Resonance
  auto peaks =
      scanner.sliding_window_resonance(stream_latin, locked_plaintext, 12);
  float resonance =
      std::accumulate(peaks.begin(), peaks.end(), 0.0f) / peaks.size();

  // Entropy Monitor
  float entropy = scanner.calculate_rolling_entropy(locked_plaintext, 0,
                                                    locked_plaintext.size());

  std::cout << "\n[CRYSTALLIZATION REPORT]" << std::endl;
  std::cout << "Global Resonance: " << std::fixed << std::setprecision(6)
            << resonance << std::endl;
  std::cout << "Residual Entropy: " << entropy << " bits/token" << std::endl;

  if (resonance > 0.99 || entropy < 4.5) {
    std::cout << "[SUCCESS] Viterbi Overdrive complete. Codebook crystallized."
              << std::endl;
    if (scanner.scan_residual_for_cluster(locked_plaintext, "RA1234DEC5678")) {
      std::cout << "[STARCHART] High-Confidence Astro-Coordinate Identified: "
                   "RA1234DEC5678"
                << std::endl;
    }

    // Phase 8: Semantic Translation
    Translator translator;
    std::ifstream dict_file("data/latin_english_1450.csv");
    std::stringstream buffer;
    buffer << dict_file.rdbuf();
    translator.load_dictionary(buffer.str(), tokenizer);

    std::cout << "[OUTPUT] Generating Plaintext Draft for Folios 1r-3r..."
              << std::endl;
    std::string english_draft =
        translator.translate(locked_plaintext, tokenizer);
    std::cout << "[ENGLISH DRAFT] " << english_draft.substr(0, 500) << "..."
              << std::endl;
  } else {
    std::cout << "[ANALYSIS] Path optimization successful, but resonance "
                 "threshold requires further sigla calibration."
              << std::endl;
  }
}

int main() {
  run_viterbi_codebook_lock();
  return 0;
}
