#ifndef DETERMINISTIC_STATE_HPP
#define DETERMINISTIC_STATE_HPP

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace deterministic {

std::vector<uint64_t> splitmix64_words(uint64_t seed, uint64_t stream_index, std::size_t words);
std::string words_to_csv(const std::vector<uint64_t>& words);

}  // namespace deterministic

#endif  // DETERMINISTIC_STATE_HPP
