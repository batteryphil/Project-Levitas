#ifndef LEVITAS_LINGUISTICS_HPP
#define LEVITAS_LINGUISTICS_HPP

#include <string>
#include <vector>

namespace levitas {

/**
 * @brief Linguistic Manifold Control Sets
 * Mapped to 0-127 neutral integer space.
 */
enum class LanguageSet {
  MEDIEVAL_LATIN,
  HIGH_GERMAN_15C,
  SEPHARDIC_HEBREW,
  VOYNICH_EVA
};

struct LanguageManifold {
  LanguageSet type;
  std::string name;
  std::vector<int> stream;
};

} // namespace levitas

#endif // LEVITAS_LINGUISTICS_HPP
