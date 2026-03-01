#ifndef LEVITAS_AUTOENCODER_HPP
#define LEVITAS_AUTOENCODER_HPP

#include <cmath>
#include <numeric>
#include <vector>

namespace levitas {

/**
 * @brief Sequence Autoencoder Architecture
 * Focused on high-compression bottleneck to extract Minimal Description Length
 * (MDL).
 */
class Autoencoder {
public:
  explicit Autoencoder(size_t sequence_length, size_t bottleneck_size)
      : seq_len(sequence_length), bottleneck(bottleneck_size) {}

  /**
   * @brief Calculates MDL of the input stream.
   * In this implementation, MDL is simulated by sequence entropy and
   * compression ratio.
   */
  double calculate_mdl(const std::vector<int> &stream) {
    if (stream.empty())
      return 0.0;

    // Histogram for entropy
    int freq[128] = {0};
    for (int t : stream) {
      if (t >= 0 && t <= 127)
        freq[t]++;
    }

    double entropy = 0.0;
    double n = static_cast<double>(stream.size());
    for (int i = 0; i < 128; ++i) {
      if (freq[i] > 0) {
        double p = freq[i] / n;
        entropy -= p * std::log2(p);
      }
    }

    // Simulate bottleneck compression: sequence length * entropy /
    // bottleneck-factor
    return (entropy * n) / bottleneck;
  }

private:
  size_t seq_len;
  size_t bottleneck;
};

} // namespace levitas

#endif // LEVITAS_AUTOENCODER_HPP
