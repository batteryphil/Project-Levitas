#ifndef LEVITAS_TRANSLATOR_HPP
#define LEVITAS_TRANSLATOR_HPP

#include "Tokenizer.hpp"
#include <map>
#include <string>
#include <vector>

namespace levitas {

class Translator {
public:
  Translator() = default;

  /**
   * @brief Load a Latin-English dictionary map.
   */
  void load_dictionary(const std::string &csv_content, Tokenizer &tokenizer) {
    // Simplified CSV parsing for the dictionary
    std::string line;
    size_t start = 0;
    size_t end = csv_content.find('\n');

    while (end != std::string::npos) {
      line = csv_content.substr(start, end - start);
      size_t comma = line.find(',');
      if (comma != std::string::npos) {
        std::string latin = line.substr(0, comma);
        std::string english = line.substr(comma + 1);

        // Strip quotes
        if (latin.size() >= 2 && latin.front() == '"' && latin.back() == '"')
          latin = latin.substr(1, latin.size() - 2);
        if (english.size() >= 2 && english.front() == '"' &&
            english.back() == '"')
          english = english.substr(1, english.size() - 2);

        auto tokens = tokenizer.tokenize_corpus(latin);
        if (!tokens.empty()) {
          dictionary[tokens] = english;
        }
      }
      start = end + 1;
      end = csv_content.find('\n', start);
    }
  }

  /**
   * @brief Translate a token stream into an English draft.
   */
  std::string translate(const std::vector<int> &stream, Tokenizer &tokenizer) {
    std::string result;
    for (size_t i = 0; i < stream.size();) {
      bool matched = false;
      // Greedy match for multi-token Latin words/phrases
      for (int len = 32; len >= 1; --len) {
        if (i + len <= stream.size()) {
          std::vector<int> sub(stream.begin() + i, stream.begin() + i + len);
          if (dictionary.count(sub)) {
            result += dictionary[sub] + " ";
            i += len;
            matched = true;
            break;
          }
        }
      }
      if (!matched) {
        // Recover original character from neutral ID: c = (ID - 1)
        char c = static_cast<char>(stream[i] - 1);
        if (c >= 32 && c < 127)
          result += c;
        i++;
      }
    }
    return result;
  }

private:
  std::map<std::vector<int>, std::string> dictionary;
};

} // namespace levitas

#endif // LEVITAS_TRANSLATOR_HPP
