#include "deterministic_state.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "usage: cpp_descriptor_dump <seed> <stream_index> <words>\n";
        return 2;
    }

    uint64_t seed = static_cast<uint64_t>(std::strtoull(argv[1], nullptr, 10));
    uint64_t stream_index = static_cast<uint64_t>(std::strtoull(argv[2], nullptr, 10));
    std::size_t words = static_cast<std::size_t>(std::strtoull(argv[3], nullptr, 10));

    auto vec = deterministic::splitmix64_words(seed, stream_index, words);
    std::cout << deterministic::words_to_csv(vec) << std::endl;
    return 0;
}
