#[cfg(feature = "sherpa")]
#[test]
fn native_library_is_actual_pr_build() {
    let sha = sherpa_onnx::git_sha1();
    eprintln!(
        "native version={} git={} ort={}",
        sherpa_onnx::version(),
        sha,
        sherpa_onnx::onnxruntime_version()
    );
    assert_eq!(sha, nemotron_unified_rust_wyoming::inference::SHERPA_COMMIT);
    assert_eq!(sherpa_onnx::version(), "2.0.1");
}
