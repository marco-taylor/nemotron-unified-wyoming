//! RNN-T prediction state, joiner, blank handling and detokenization are owned by
//! the pinned sherpa Unified implementation. Rust does not reimplement the decoder.
pub const DECODING_METHOD: &str = "greedy_search";
