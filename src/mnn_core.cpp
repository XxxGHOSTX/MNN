#include "mnn_core.hpp"

#include <algorithm>
#include <cstddef>
#include <cmath>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using mnn::Shape;

std::size_t compute_size(const Shape &shape) {
    if (shape.empty()) {
        return 0;
    }
    return std::accumulate(shape.begin(), shape.end(), static_cast<std::size_t>(1),
                           [](std::size_t acc, std::size_t v) { return acc * v; });
}

std::vector<std::size_t> make_strides(const Shape &shape) {
    std::vector<std::size_t> strides(shape.size(), 1);
    if (shape.empty()) {
        return strides;
    }
    for (std::ptrdiff_t i = static_cast<std::ptrdiff_t>(shape.size()) - 2; i >= 0; --i) {
        strides[static_cast<std::size_t>(i)] =
            strides[static_cast<std::size_t>(i + 1)] * shape[static_cast<std::size_t>(i + 1)];
    }
    return strides;
}

Shape infer_broadcast_shape(const Shape &a, const Shape &b) {
    const std::size_t rank = std::max(a.size(), b.size());
    Shape result(rank, 1);
    for (std::size_t i = 0; i < rank; ++i) {
        const std::size_t a_idx = (i < rank - a.size()) ? 1 : a[i - (rank - a.size())];
        const std::size_t b_idx = (i < rank - b.size()) ? 1 : b[i - (rank - b.size())];
        if (a_idx != b_idx && a_idx != 1 && b_idx != 1) {
            throw std::invalid_argument("Incompatible shapes for broadcasting");
        }
        result[i] = std::max(a_idx, b_idx);
    }
    return result;
}

std::size_t broadcast_offset(std::size_t linear_index, const Shape &source_shape,
                             const std::vector<std::size_t> &source_strides, const Shape &target_shape,
                             const std::vector<std::size_t> &target_strides) {
    const std::size_t rank = target_shape.size();
    const std::size_t src_rank = source_shape.size();
    std::size_t remaining = linear_index;
    std::size_t offset = 0;
    for (std::size_t i = 0; i < rank; ++i) {
        const std::size_t coord = remaining / target_strides[i];
        remaining %= target_strides[i];
        if (i < rank - src_rank) {
            continue; // implicit broadcasted dimension
        }
        const std::size_t src_dim = i - (rank - src_rank);
        if (source_shape[src_dim] == 1) {
            continue; // broadcast dimension
        }
        offset += coord * source_strides[src_dim];
    }
    return offset;
}

template <typename Fn>
mnn::Tensor broadcast_binary(const mnn::Tensor &lhs, const mnn::Tensor &rhs, Fn fn) {
    Shape result_shape = infer_broadcast_shape(lhs.shape(), rhs.shape());
    const auto result_strides = make_strides(result_shape);
    const auto lhs_strides = make_strides(lhs.shape());
    const auto rhs_strides = make_strides(rhs.shape());

    mnn::Tensor out(result_shape, 0.0);
    const std::size_t total = compute_size(result_shape);
    for (std::size_t idx = 0; idx < total; ++idx) {
        const std::size_t lhs_offset =
            broadcast_offset(idx, lhs.shape(), lhs_strides, result_shape, result_strides);
        const std::size_t rhs_offset =
            broadcast_offset(idx, rhs.shape(), rhs_strides, result_shape, result_strides);
        out.data()[idx] = fn(lhs.data()[lhs_offset], rhs.data()[rhs_offset]);
    }
    return out;
}

} // namespace

namespace mnn {

Tensor::Tensor() = default;

Tensor::Tensor(Shape shape, double fill_value) : shape_(std::move(shape)) {
    const std::size_t total = compute_size(shape_);
    data_.assign(total, fill_value);
    compute_strides();
}

Tensor::Tensor(Shape shape, std::vector<double> data)
    : shape_(std::move(shape)), data_(std::move(data)) {
    if (compute_size(shape_) != data_.size()) {
        throw std::invalid_argument("Data size does not match shape product");
    }
    compute_strides();
}

const Shape &Tensor::shape() const { return shape_; }

std::size_t Tensor::size() const { return data_.size(); }

const std::vector<double> &Tensor::data() const { return data_; }

std::vector<double> &Tensor::data() { return data_; }

double Tensor::at(const std::vector<std::size_t> &indices) const {
    return data_.at(offset(indices));
}

double &Tensor::at(const std::vector<std::size_t> &indices) {
    return data_.at(offset(indices));
}

Tensor Tensor::broadcast_to(const Shape &target) const {
    if (shape_ == target) {
        return *this;
    }
    if (target.size() < shape_.size()) {
        throw std::invalid_argument("Cannot broadcast to a lower-rank shape");
    }
    Shape aligned = target;
    // validate compatibility
    const std::size_t rank = target.size();
    const std::size_t src_rank = shape_.size();
    for (std::size_t i = 0; i < rank; ++i) {
        const std::size_t src_dim = (i < rank - src_rank) ? 1 : shape_[i - (rank - src_rank)];
        if (src_dim != aligned[i] && src_dim != 1) {
            throw std::invalid_argument("Cannot broadcast tensor to target shape");
        }
    }
    Tensor out(aligned, 0.0);
    const auto result_strides = make_strides(aligned);
    const auto source_strides = make_strides(shape_);
    const std::size_t total = compute_size(aligned);
    for (std::size_t idx = 0; idx < total; ++idx) {
        const std::size_t src_off =
            broadcast_offset(idx, shape_, source_strides, aligned, result_strides);
        out.data()[idx] = data_[src_off];
    }
    return out;
}

Tensor Tensor::add(const Tensor &other) const { return broadcast_add(*this, other); }

Tensor Tensor::multiply(const Tensor &other) const {
    return broadcast_binary(*this, other, [](double a, double b) { return a * b; });
}

Tensor Tensor::matmul(const Tensor &other) const {
    if (shape_.size() != 2 || other.shape_.size() != 2) {
        throw std::invalid_argument("matmul expects 2D tensors");
    }
    const std::size_t m = shape_[0];
    const std::size_t k = shape_[1];
    const std::size_t k_other = other.shape_[0];
    const std::size_t n = other.shape_[1];
    if (k != k_other) {
        throw std::invalid_argument("Inner dimensions do not match for matmul");
    }
    Tensor out({m, n}, 0.0);
    for (std::size_t i = 0; i < m; ++i) {
        for (std::size_t j = 0; j < n; ++j) {
            double acc = 0.0;
            const std::size_t row_offset = i * k;
            const std::size_t col_offset = j;
            for (std::size_t p = 0; p < k; ++p) {
                acc += data_[row_offset + p] * other.data_[p * n + col_offset];
            }
            out.data_[i * n + j] = acc;
        }
    }
    return out;
}

Tensor Tensor::map(const std::function<double(double)> &fn) const {
    Tensor out = *this;
    std::transform(data_.begin(), data_.end(), out.data_.begin(), fn);
    return out;
}

Tensor Tensor::zeros(const Shape &shape) { return Tensor(shape, 0.0); }

void Tensor::compute_strides() { strides_ = make_strides(shape_); }

std::size_t Tensor::offset(const std::vector<std::size_t> &indices) const {
    if (indices.size() != shape_.size()) {
        throw std::out_of_range("Index rank does not match tensor rank");
    }
    std::size_t off = 0;
    for (std::size_t i = 0; i < shape_.size(); ++i) {
        if (indices[i] >= shape_[i]) {
            throw std::out_of_range("Index out of bounds for tensor");
        }
        off += indices[i] * strides_[i];
    }
    return off;
}

GeometricCharacterEmbedding::GeometricCharacterEmbedding(std::size_t embedding_dim, double curvature)
    : embedding_dim_(embedding_dim), curvature_(curvature) {
    if (embedding_dim_ == 0) {
        throw std::invalid_argument("Embedding dimension must be positive");
    }
}

Tensor GeometricCharacterEmbedding::encode(const std::string &text) const {
    Shape out_shape{ text.size(), embedding_dim_ };
    Tensor out(out_shape, 0.0);
    if (text.empty()) {
        return out;
    }
    constexpr double pi = 3.14159265358979323846;
    for (std::size_t i = 0; i < text.size(); ++i) {
        const auto code = static_cast<unsigned char>(text[i]);
        const double radius = 1.0 + (static_cast<double>(code % 31) / 31.0) * curvature_;
        for (std::size_t j = 0; j < embedding_dim_; ++j) {
            const double phase = static_cast<double>(j) / static_cast<double>(embedding_dim_);
            const double angle = radius * 0.25 * static_cast<double>(i + 1) + phase * pi;
            const double geom = std::sin(angle) + std::cos(angle * 0.5);
            const double harmonic = std::sin((code + j) * 0.017);
            out.data()[i * embedding_dim_ + j] = radius * geom + harmonic;
        }
    }
    return out;
}

MNNCore::MNNCore(Tensor weights, Tensor bias)
    : weights_(std::move(weights)), bias_(std::move(bias)) {
    if (weights_.shape().size() != 2) {
        throw std::invalid_argument("Weights must be 2D");
    }
    if (bias_.shape().size() != 1 || bias_.shape()[0] != weights_.shape()[1]) {
        throw std::invalid_argument("Bias must match output dimension of weights");
    }
}

Tensor MNNCore::forward(const Tensor &input, const Tensor &embedding) const {
    if (input.shape().size() != 2) {
        throw std::invalid_argument("Input must be [batch, features]");
    }
    const Tensor projected = input.matmul(weights_);
    const Tensor with_bias = broadcast_add(projected, bias_);
    const Tensor embedded = embedding.broadcast_to(with_bias.shape());
    return broadcast_add(with_bias, embedded);
}

Tensor broadcast_add(const Tensor &lhs, const Tensor &rhs) {
    return broadcast_binary(lhs, rhs, [](double a, double b) { return a + b; });
}

} // namespace mnn
