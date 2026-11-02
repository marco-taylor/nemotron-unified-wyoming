//! Tiny protobuf metadata fixtures, not neural models and never used for recognition.
use nemotron_unified_rust_wyoming::model::validate_l37;
fn metadata_bytes(language: &str) -> Vec<u8> {
    let mut result = vec![];
    for (k, v) in [
        ("streaming_model_type", "nemo_parakeet_unified_streaming"),
        ("left_encoder_frames", "37"),
        ("chunk_encoder_frames", "7"),
        ("right_encoder_frames", "7"),
        ("buffered_streaming", "1"),
        ("prompt_dictionary", language),
    ] {
        let mut entry = vec![10, k.len() as u8];
        entry.extend(k.as_bytes());
        entry.extend([18, v.len() as u8]);
        entry.extend(v.as_bytes());
        assert!(entry.len() < 128);
        result.extend([114, entry.len() as u8]);
        result.extend(entry);
    }
    result
}
#[test]
fn rejects_english_only_and_accepts_expected_metadata_contract() {
    let p = std::env::temp_dir().join(format!("nemotron-metadata-test-{}.bin", std::process::id()));
    std::fs::write(&p, metadata_bytes(r#"{"auto":0,"en":1}"#)).unwrap();
    assert!(validate_l37(&p).is_err());
    std::fs::write(&p, metadata_bytes(r#"{"auto":0,"de":2}"#)).unwrap();
    assert_eq!(validate_l37(&p).unwrap()["left_encoder_frames"], "37");
    std::fs::remove_file(p).unwrap();
}
