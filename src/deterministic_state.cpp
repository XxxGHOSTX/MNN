#include "deterministic_state.hpp"

#include <sstream>

namespace deterministic {

namespace {
constexpr uint64_t MASK_64 = 0xFFFFFFFFFFFFFFFFULL;
}

std::vector<uint64_t> splitmix64_words(uint64_t seed, uint64_t stream_index, std::size_t words) {
    uint64_t x = (seed ^ ((stream_index + 1ULL) * 0x9E3779B97F4A7C15ULL)) & MASK_64;
    std::vector<uint64_t> out;
    out.reserve(words);

    for (std::size_t i = 0; i < words; ++i) {
        x = (x + 0x9E3779B97F4A7C15ULL) & MASK_64;
        uint64_t z = x;
        z = ((z ^ (z >> 30U)) * 0xBF58476D1CE4E5B9ULL) & MASK_64;
        z = ((z ^ (z >> 27U)) * 0x94D049BB133111EBULL) & MASK_64;
        z = z ^ (z >> 31U);
        out.push_back(z & MASK_64);
    }
    return out;
}

std::string words_to_csv(const std::vector<uint64_t>& words) {
    std::ostringstream oss;
    for (std::size_t i = 0; i < words.size(); ++i) {
        if (i > 0) {
            oss << ",";
        }
        oss << words[i];
    }
    return oss.str();
}

}  // namespace deterministic
