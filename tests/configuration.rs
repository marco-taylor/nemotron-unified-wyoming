use nemotron_unified_wyoming::{
    config::{Config, LogLevel},
    inference::SessionConfig,
    wyoming::{read_event_with_limit, write_event, Event},
};
use serde_json::json;
fn config(values: &[(&str, &str)]) -> nemotron_unified_wyoming::Result<Config> {
    Config::from_values(|key| {
        values
            .iter()
            .find(|(k, _)| *k == key)
            .map(|(_, v)| v.to_string())
    })
}
#[test]
fn all_defaults_are_safe_and_applied() {
    let c = config(&[]).unwrap();
    assert_eq!(c.bind, "0.0.0.0:10300");
    assert_eq!(c.model.language, "de");
    assert_eq!(c.model.threads, 2);
    assert_eq!(c.model.device, "cpu");
    assert_eq!(c.model.inference_chunk_ms, 20);
    assert_eq!(c.max_audio_chunk_bytes, 320000);
    assert_eq!(c.max_audio_seconds, 120);
    assert_eq!(c.max_connections, 8);
    assert_eq!(c.client_timeout.as_secs(), 30);
    assert_eq!(c.log_level, LogLevel::Info);
    assert!(!c.log_transcripts);
    assert_eq!(
        c.model.path("encoder.int8.onnx"),
        std::path::PathBuf::from("/models/encoder.int8.onnx")
    );
}
#[test]
fn all_overrides_reach_the_configuration() {
    let c = config(&[
        ("WYOMING_HOST", "::1"),
        ("WYOMING_PORT", "10400"),
        ("MODEL_DIR", "/custom"),
        ("ENCODER_PATH", "enc.onnx"),
        ("DECODER_PATH", "/else/dec.onnx"),
        ("JOINER_PATH", "join.onnx"),
        ("TOKENS_PATH", "vocab.txt"),
        ("THREADS", "4"),
        ("LANGUAGE", "de"),
        ("STT_DEVICE", "cpu"),
        ("MAX_CONNECTIONS", "2"),
        ("MAX_AUDIO_SECONDS", "15"),
        ("CLIENT_TIMEOUT_SECONDS", "5"),
        ("MAX_AUDIO_CHUNK_BYTES", "1280"),
        ("INFERENCE_CHUNK_MS", "80"),
        ("LOG_LEVEL", "DEBUG"),
        ("LOG_TRANSCRIPTS", "true"),
    ])
    .unwrap();
    assert_eq!(c.bind, "[::1]:10400");
    assert_eq!(c.model.threads, 4);
    assert_eq!(
        c.model.path("encoder.int8.onnx"),
        std::path::PathBuf::from("/custom/enc.onnx")
    );
    assert_eq!(
        c.model.path("decoder.onnx"),
        std::path::PathBuf::from("/else/dec.onnx")
    );
    assert_eq!(
        c.model.path("joiner.onnx"),
        std::path::PathBuf::from("/custom/join.onnx")
    );
    assert_eq!(
        c.model.path("tokens.txt"),
        std::path::PathBuf::from("/custom/vocab.txt")
    );
    assert_eq!(c.max_connections, 2);
    assert_eq!(c.max_audio_seconds, 15);
    assert_eq!(c.client_timeout.as_secs(), 5);
    assert_eq!(c.max_audio_chunk_bytes, 1280);
    assert_eq!(c.model.inference_chunk_ms, 80);
    assert_eq!(c.log_level, LogLevel::Debug);
    assert!(c.log_transcripts);
    assert_eq!(
        config(&[("ENCODER_PATH", "")]).unwrap().model.encoder_path,
        None
    );
}
#[test]
fn invalid_values_name_the_variable() {
    for (k, v) in [
        ("WYOMING_HOST", "not an address"),
        ("WYOMING_PORT", "0"),
        ("WYOMING_PORT", "65536"),
        ("WYOMING_PORT", "x"),
        ("MODEL_DIR", ""),
        ("ENCODER_PATH", "a\0b"),
        ("DECODER_PATH", "a\0b"),
        ("JOINER_PATH", "a\0b"),
        ("TOKENS_PATH", "a\0b"),
        ("THREADS", "3"),
        ("LANGUAGE", "en"),
        ("STT_DEVICE", "cuda"),
        ("MAX_CONNECTIONS", "33"),
        ("MAX_AUDIO_SECONDS", "121"),
        ("CLIENT_TIMEOUT_SECONDS", "0"),
        ("MAX_AUDIO_CHUNK_BYTES", "641"),
        ("MAX_AUDIO_CHUNK_BYTES", "320002"),
        ("INFERENCE_CHUNK_MS", "9"),
        ("INFERENCE_CHUNK_MS", "561"),
        ("LOG_LEVEL", "trace"),
        ("LOG_TRANSCRIPTS", "yes"),
    ] {
        let e = config(&[(k, v)]).unwrap_err().to_string();
        assert!(e.contains(k), "{k}: {e}");
    }
}
#[test]
fn configured_chunk_limit_is_enforced_before_allocation() {
    let c = config(&[("MAX_AUDIO_CHUNK_BYTES", "640")]).unwrap();
    let mut e = Event::new("audio-chunk", json!({"rate":16000,"width":2,"channels":1}));
    e.payload = vec![0; 642];
    let mut wire = vec![];
    write_event(&mut wire, &e).unwrap();
    assert!(
        read_event_with_limit(&mut std::io::Cursor::new(wire), c.max_audio_chunk_bytes).is_err()
    );
    e.payload.truncate(640);
    let mut wire = vec![];
    write_event(&mut wire, &e).unwrap();
    assert!(
        read_event_with_limit(&mut std::io::Cursor::new(wire), c.max_audio_chunk_bytes).is_ok()
    );
}
#[test]
fn logging_levels_and_transcript_privacy_have_effect() {
    let e = Event::new("transcript", json!({"text":"TEST FIXTURE, NOT ASR"}));
    assert!(config(&[]).unwrap().transcript_log(&e).is_none());
    assert!(config(&[("LOG_TRANSCRIPTS", "true")])
        .unwrap()
        .transcript_log(&e)
        .unwrap()
        .contains("TEST FIXTURE"));
    assert!(
        config(&[("LOG_TRANSCRIPTS", "true"), ("LOG_LEVEL", "warn")])
            .unwrap()
            .transcript_log(&e)
            .is_none()
    );
    for level in [
        LogLevel::Error,
        LogLevel::Warn,
        LogLevel::Info,
        LogLevel::Debug,
    ] {
        assert!(level.enabled(LogLevel::Error));
    }
    assert!(!LogLevel::Warn.enabled(LogLevel::Info));
    assert!(LogLevel::Debug.enabled(LogLevel::Debug));
}
#[test]
fn model_override_validation_checks_the_selected_file() {
    let c = config(&[("ENCODER_PATH", "/missing-selected-encoder-for-tests")]).unwrap();
    assert!(c
        .model
        .validate()
        .unwrap_err()
        .to_string()
        .contains("/missing-selected-encoder-for-tests"));
    let c = SessionConfig {
        inference_chunk_ms: 0,
        ..SessionConfig::default()
    };
    assert!(c
        .validate()
        .unwrap_err()
        .to_string()
        .contains("INFERENCE_CHUNK_MS"));
}
#[test]
fn documented_variables_match_the_parser() {
    let rows: Vec<Vec<String>> =
        serde_json::from_str(include_str!("../config/variables.json")).unwrap();
    let documented: std::collections::BTreeSet<_> = rows
        .iter()
        .map(|r| r[0].as_str())
        .filter(|n| !["PUID", "PGID"].contains(n))
        .collect();
    let parsed: std::collections::BTreeSet<_> = Config::variable_names().iter().copied().collect();
    assert_eq!(documented, parsed);
    for row in rows
        .iter()
        .filter(|r| !["PUID", "PGID"].contains(&r[0].as_str()))
    {
        // Every advertised default must parse when explicitly supplied (including optional empty paths).
        config(&[(&row[0], &row[1])]).unwrap();
    }
}

#[test]
fn entrypoint_identity_defaults_are_documented_separately() {
    let rows: Vec<Vec<String>> =
        serde_json::from_str(include_str!("../config/variables.json")).unwrap();
    let ids: Vec<_> = rows
        .iter()
        .filter(|r| ["PUID", "PGID"].contains(&r[0].as_str()))
        .collect();
    assert_eq!(ids.len(), 2);
    assert_eq!(ids.iter().find(|r| r[0] == "PUID").unwrap()[1], "99");
    assert_eq!(ids.iter().find(|r| r[0] == "PGID").unwrap()[1], "100");
}
