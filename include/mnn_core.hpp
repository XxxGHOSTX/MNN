#pragma once

#include <cstddef>
#include <functional>
#include <string>
#include <vector>

namespace mnn {

using Shape = std::vector<std::size_t>;

class Tensor {
public:
    Tensor();
    explicit Tensor(Shape shape, double fill_value = 0.0);
    Tensor(Shape shape, std::vector<double> data);

    const Shape &shape() const;
    std::size_t size() const;
    const std::vector<double> &data() const;
    std::vector<double> &data();

    double at(const std::vector<std::size_t> &indices) const;
    double &at(const std::vector<std::size_t> &indices);

    Tensor broadcast_to(const Shape &target) const;
    Tensor add(const Tensor &other) const;
    Tensor multiply(const Tensor &other) const;
    Tensor matmul(const Tensor &other) const;
    Tensor map(const std::function<double(double)> &fn) const;

    static Tensor zeros(const Shape &shape);

private:
    Shape shape_{};
    std::vector<std::size_t> strides_{};
    std::vector<double> data_{};

    void compute_strides();
    std::size_t offset(const std::vector<std::size_t> &indices) const;
};

class GeometricCharacterEmbedding {
public:
    explicit GeometricCharacterEmbedding(std::size_t embedding_dim = 16, double curvature = 1.0);
    Tensor encode(const std::string &text) const;

private:
    std::size_t embedding_dim_;
    double curvature_;
};

class MNNCore {
public:
    MNNCore(Tensor weights, Tensor bias);
    Tensor forward(const Tensor &input, const Tensor &embedding) const;

private:
    Tensor weights_;
    Tensor bias_;
};

Tensor broadcast_add(const Tensor &lhs, const Tensor &rhs);

} // namespace mnn
