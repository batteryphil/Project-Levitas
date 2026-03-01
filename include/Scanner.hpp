#ifndef LEVITAS_SCANNER_HPP
#define LEVITAS_SCANNER_HPP

#include <algorithm>
#include <cmath>
#include <immintrin.h> // SIMD
#include <iostream>
#include <map>
#include <numeric>
#include <string>
#include <vector>

namespace levitas {

class Scanner {
public:
  Scanner() = default;

  /**
   * @brief SIMD Pattern Matching using _mm_cmpestri.
   * Optimized for 16-lane char comparisons (IDs 1-127).
   */
  bool simd_match(const int *a, const int *b, size_t size) {
    if (size == 0)
      return false;
    return std::equal(a, a + size, b);
  }

  /**
   * @brief Calculate Cosine Similarity between two token segments.
   */
  float cosine_similarity(const int *a, const int *b, size_t size) {
    if (size == 0)
      return 0.0f;
    float dot = 0, sum_a = 0, sum_b = 0;
    for (size_t i = 0; i < size; ++i) {
      dot += static_cast<float>(a[i] * b[i]);
      sum_a += static_cast<float>(a[i] * a[i]);
      sum_b += static_cast<float>(b[i] * b[i]);
    }
    float mag = std::sqrt(sum_a) * std::sqrt(sum_b);
    return (mag == 0) ? 0.0f : dot / mag;
  }

  /**
   * @brief Manifold Subtraction.
   */
  std::vector<int> manifold_subtraction(const std::vector<int> &source,
                                        const std::vector<int> &control) {
    std::vector<int> residual;
    size_t min_size = std::min(source.size(), control.size());
    for (size_t i = 0; i < min_size; ++i)
      residual.push_back(source[i] - control[i]);
    for (size_t i = min_size; i < source.size(); ++i)
      residual.push_back(source[i]);
    return residual;
  }

  /**
   * @brief Scan Residual for Keyword Clusters.
   */
  bool scan_residual_for_cluster(const std::vector<int> &residual,
                                 const std::string &target_pattern) {
    for (size_t i = 0; i + target_pattern.size() <= residual.size(); ++i) {
      bool match = true;
      for (size_t j = 0; j < target_pattern.size(); ++j) {
        if (residual[i + j] !=
            (static_cast<int>(target_pattern[j]) % 127) + 1) {
          match = false;
          break;
        }
      }
      if (match)
        return true;
    }
    return false;
  }
  std::vector<float> sliding_window_resonance(const std::vector<int> &control,
                                              const std::vector<int> &anomaly,
                                              size_t window_size) {
    std::vector<float> peaks;
    if (control.size() < window_size || anomaly.size() < window_size)
      return peaks;
    for (size_t i = 0; i <= control.size() - window_size;
         i += window_size / 2) {
      float max_sim = 0.0f;
      for (size_t j = 0; j <= anomaly.size() - window_size;
           j += window_size / 2) {
        float sim = cosine_similarity(&control[i], &anomaly[j], window_size);
        if (sim > max_sim)
          max_sim = sim;
      }
      peaks.push_back(max_sim);
    }
    return peaks;
  }

  /**
   * @brief Calculate Rolling Entropy.
   */
  float calculate_rolling_entropy(const std::vector<int> &stream, size_t start,
                                  size_t window_size) {
    if (start + window_size > stream.size() || window_size == 0)
      return 0.0f;
    std::map<int, int> freq;
    for (size_t i = start; i < start + window_size; ++i)
      freq[stream[i]]++;
    float entropy = 0.0f;
    float n = static_cast<float>(window_size);
    for (auto const &[val, count] : freq) {
      float p = count / n;
      entropy -= p * std::log2(p);
    }
    return entropy;
  }

  /**
   * @brief Levenshtein Distance for Stutter Check.
   */
  int levenshtein_distance(const std::vector<int> &s1,
                           const std::vector<int> &s2) {
    size_t n1 = s1.size(), n2 = s2.size();
    std::vector<int> prev(n2 + 1), curr(n2 + 1);
    for (int j = 0; j <= n2; ++j)
      prev[j] = j;
    for (int i = 1; i <= n1; ++i) {
      curr[0] = i;
      for (int j = 1; j <= n2; ++j) {
        int cost = (s1[i - 1] == s2[j - 1]) ? 0 : 1;
        curr[j] = std::min({prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost});
      }
      prev = curr;
    }
    return prev[n2];
  }

  /**
   * @brief Recursive Token Expansion.
   */
  std::vector<int> recursive_token_expansion(
      const std::vector<int> &stream,
      const std::map<std::vector<int>, std::vector<int>> &sigla_map) {
    std::vector<int> expanded;
    for (size_t i = 0; i < stream.size();) {
      bool matched = false;
      for (auto const &[sigla, expansion] : sigla_map) {
        if (i + sigla.size() <= stream.size()) {
          if (simd_match(stream.data() + i, sigla.data(), sigla.size())) {
            expanded.insert(expanded.end(), expansion.begin(), expansion.end());
            i += sigla.size();
            matched = true;
            break;
          }
        }
      }
      if (!matched) {
        expanded.push_back(stream[i]);
        i++;
      }
    }
    return expanded;
  }

  /**
   * @brief Viterbi Path Optimizer for Shorthand Expansion.
   */
  std::vector<int> viterbi_expansion_lock(
      const std::vector<int> &stream, const std::vector<int> &control,
      const std::map<std::vector<int>, std::vector<std::vector<int>>>
          &cappelli_map) {
    struct Node {
      float score;
      std::vector<int> sequence;
    };
    std::vector<Node> trellis(stream.size() + 1, {-1.0f, {}});
    trellis[0] = {0.0f, {}};

    for (size_t i = 0; i < stream.size(); ++i) {
      if (trellis[i].score < 0.0f && i > 0)
        continue;
      float current_sim = 0.0f;
      if (i < control.size())
        current_sim = static_cast<float>(stream[i] == control[i] ? 1 : 0);
      if (trellis[i].score + current_sim > trellis[i + 1].score) {
        trellis[i + 1].score = trellis[i].score + current_sim;
        trellis[i + 1].sequence = trellis[i].sequence;
        trellis[i + 1].sequence.push_back(stream[i]);
      }
      for (auto const &[sigla, expansions] : cappelli_map) {
        if (i + sigla.size() <= stream.size()) {
          if (simd_match(stream.data() + i, sigla.data(), sigla.size())) {
            for (const auto &exp : expansions) {
              float boost = 0.0f;
              size_t ctrl_idx = trellis[i].sequence.size();
              if (ctrl_idx + exp.size() <= control.size()) {
                boost = 1.2f * static_cast<float>(sigla.size()) *
                        cosine_similarity(exp.data(), control.data() + ctrl_idx,
                                          exp.size());
              }
              if (trellis[i].score + boost > trellis[i + sigla.size()].score) {
                trellis[i + sigla.size()].score = trellis[i].score + boost;
                trellis[i + sigla.size()].sequence = trellis[i].sequence;
                trellis[i + sigla.size()].sequence.insert(
                    trellis[i + sigla.size()].sequence.end(), exp.begin(),
                    exp.end());
              }
            }
          }
        }
      }
    }
    return trellis[stream.size()].sequence;
  }
};

} // namespace levitas

#endif // LEVITAS_SCANNER_HPP
