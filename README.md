# MNN

Matrix Neural Network (MNN)

## PostgreSQL Relational Buffer schema
The relational buffer schema tailored for `/artifacts/{appId}/public/data/` lives in `sql/relational_buffer_schema.sql`. It models:
* `applications` and `artifacts` with generated storage paths rooted at `/artifacts/{appId}/public/data/`
* `manifolds`, `manifold_coordinates`, and `void_spaces` to track manifold coverage and void regions
* `buffer_segments` to pin coordinate bounds to on-disk slices

Apply with:
```bash
psql -f sql/relational_buffer_schema.sql
```

## C++ MNN core
The C++ implementation under `include/mnn_core.hpp` and `src/mnn_core.cpp` provides first principles tensor math, broadcasting, and the Geometric Character Embedding used by the 200M+ parameter Matrix Neural Network.

Build a quick sanity check:
```bash
g++ -std=c++17 -Iinclude -c src/mnn_core.cpp
```
