# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `BloomFilter.union` (and `|`) — merge two same-shape filters; any item present in
  either input is present in the union.

## [0.1.0]

### Added
- `BloomFilter`, `CountMinSketch` and `HyperLogLog` with shared BLAKE2b hashing.
- Statistical-guarantee tests (no false negatives, no underestimate, error within bounds).
