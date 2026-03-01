#ifndef LEVITAS_TOKENIZER_HPP
#define LEVITAS_TOKENIZER_HPP

#include "Linguistics.hpp"
#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace levitas {

/**
 * @brief Linguistic Tokenizer
 * Maps text corpus and EVA transcription to 1-127 neutral IDs.
 */
class Tokenizer {
public:
  Tokenizer() = default;

  /**
   * @brief Reads a file into a token stream (1-127).
   */
  std::vector<int> tokenize_file(const std::string &filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
      return {};
    }
    std::stringstream buffer;
    buffer << file.rdbuf();
    return tokenize_corpus(buffer.str());
  }

  /**
   * @brief Maps a string corpus to 1-127 neutral IDs.
   * Skips Voynich metadata tags <...>.
   */
  std::vector<int> tokenize_corpus(const std::string &text) {
    std::vector<int> tokens;
    bool in_tag = false;
    for (char c : text) {
      if (c == '<') {
        in_tag = true;
        continue;
      }
      if (c == '>') {
        in_tag = false;
        continue;
      }
      if (!in_tag && c > 31 && c < 127) { // Printable ASCII range
        tokens.push_back(static_cast<uint8_t>(c) % 127 + 1);
      }
    }
    return tokens;
  }

  /**
   * @brief Specialized EVA Tokenizer for Voynich Manuscript.
   */
  std::vector<int> tokenize_voynich(const std::string &filepath) {
    return tokenize_file(filepath);
  }
};

} // namespace levitas

#endif // LEVITAS_TOKENIZER_HPP
