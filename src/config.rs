//! Validated Docker configuration. Existing names remain compatible.
use crate::{inference::SessionConfig, Error, Result};
use std::{path::PathBuf, time::Duration};
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum LogLevel {
    Error,
    Warn,
    Info,
    Debug,
}
impl LogLevel {
    pub fn enabled(self, level: Self) -> bool {
        level <= self
    }
    pub fn parse(s: &str) -> Result<Self> {
        match s.to_ascii_lowercase().as_str() {
            "error" => Ok(Self::Error),
            "warn" | "warning" => Ok(Self::Warn),
            "info" => Ok(Self::Info),
            "debug" => Ok(Self::Debug),
            _ => Err(Error::InvalidInput(
                "LOG_LEVEL: expected error, warn, info or debug",
            )),
        }
    }
}
#[derive(Clone, Debug)]
pub struct Config {
    pub model: SessionConfig,
    pub bind: String,
    pub max_connections: usize,
    pub max_audio_seconds: usize,
    pub client_timeout: Duration,
    pub max_audio_chunk_bytes: usize,
    pub log_level: LogLevel,
    pub log_transcripts: bool,
}
impl Config {
    pub fn transcript_log(&self, event: &crate::wyoming::Event) -> Option<String> {
        if self.log_transcripts
            && self.log_level.enabled(LogLevel::Info)
            && event.kind == "transcript"
        {
            Some(format!(
                "transcript: {}",
                serde_json::Value::Object(event.data.clone())
            ))
        } else {
            None
        }
    }
    pub fn from_env() -> Result<Self> {
        // Do not silently fall back when a supplied value is not UTF-8.
        for (key, value) in std::env::vars_os() {
            if Self::variable_names().iter().any(|k| key == *k) && value.to_str().is_none() {
                return Err(Error::Runtime(format!(
                    "{} must be UTF-8",
                    key.to_string_lossy()
                )));
            }
        }
        Self::from_values(|k| std::env::var(k).ok())
    }
    pub fn variable_names() -> &'static [&'static str] {
        &[
            "MODEL_DIR",
            "ENCODER_PATH",
            "DECODER_PATH",
            "JOINER_PATH",
            "TOKENS_PATH",
            "LANGUAGE",
            "THREADS",
            "STT_DEVICE",
            "WYOMING_HOST",
            "WYOMING_PORT",
            "MAX_CONNECTIONS",
            "MAX_AUDIO_SECONDS",
            "CLIENT_TIMEOUT_SECONDS",
            "MAX_AUDIO_CHUNK_BYTES",
            "INFERENCE_CHUNK_MS",
            "LOG_LEVEL",
            "LOG_TRANSCRIPTS",
        ]
    }
    pub fn from_values(get: impl Fn(&str) -> Option<String>) -> Result<Self> {
        let number = |key: &str, default: usize, low: usize, high: usize| -> Result<usize> {
            let n = match get(key) {
                Some(s) => s.parse().map_err(|_| {
                    Error::Runtime(format!("{key}: expected integer {low}..={high}"))
                })?,
                None => default,
            };
            if !(low..=high).contains(&n) {
                return Err(Error::Runtime(format!("{key} must be {low}..={high}")));
            }
            Ok(n)
        };
        let log_transcripts = match get("LOG_TRANSCRIPTS").as_deref() {
            None | Some("false") => false,
            Some("true") => true,
            _ => return Err(Error::InvalidInput("LOG_TRANSCRIPTS must be true or false")),
        };
        let language = get("LANGUAGE").unwrap_or_else(|| "de".into());
        if language != "de" {
            return Err(Error::InvalidInput("LANGUAGE must be de"));
        }
        let threads = number("THREADS", 2, 1, 4)?;
        if ![1, 2, 4].contains(&threads) {
            return Err(Error::InvalidInput("THREADS must be 1, 2 or 4"));
        }
        let device = get("STT_DEVICE").unwrap_or_else(|| "cpu".into());
        if device != "cpu" {
            return Err(Error::InvalidInput(
                "STT_DEVICE: this build supports only cpu",
            ));
        }
        let model_dir = PathBuf::from(get("MODEL_DIR").unwrap_or_else(|| "/models".into()));
        if model_dir.as_os_str().is_empty() || model_dir.to_string_lossy().contains('\0') {
            return Err(Error::InvalidInput(
                "MODEL_DIR must be a nonempty path without NUL",
            ));
        }
        let path = |key| -> Result<Option<PathBuf>> {
            match get(key).filter(|s| !s.is_empty()) {
                Some(s) if s.contains('\0') => {
                    Err(Error::Runtime(format!("{key}: path contains NUL")))
                }
                Some(s) => Ok(Some(PathBuf::from(s))),
                None => Ok(None),
            }
        };
        let host = get("WYOMING_HOST").unwrap_or_else(|| "0.0.0.0".into());
        let host = host.trim_matches(|c| c == '[' || c == ']');
        let ip: std::net::IpAddr = host
            .parse()
            .map_err(|_| Error::InvalidInput("WYOMING_HOST: expected IPv4 or IPv6 bind address"))?;
        let port = number("WYOMING_PORT", 10300, 1, 65535)? as u16;
        let chunk = number("MAX_AUDIO_CHUNK_BYTES", 320000, 640, 320000)?;
        if chunk % 2 != 0 {
            return Err(Error::InvalidInput(
                "MAX_AUDIO_CHUNK_BYTES must be even (PCM16)",
            ));
        }
        Ok(Self {
            model: SessionConfig {
                model_dir,
                language,
                threads,
                encoder_path: path("ENCODER_PATH")?,
                decoder_path: path("DECODER_PATH")?,
                joiner_path: path("JOINER_PATH")?,
                tokens_path: path("TOKENS_PATH")?,
                device,
                inference_chunk_ms: number("INFERENCE_CHUNK_MS", 20, 10, 560)?,
            },
            bind: std::net::SocketAddr::new(ip, port).to_string(),
            max_connections: number("MAX_CONNECTIONS", 8, 1, 32)?,
            max_audio_seconds: number("MAX_AUDIO_SECONDS", 120, 1, 120)?,
            client_timeout: Duration::from_secs(
                number("CLIENT_TIMEOUT_SECONDS", 30, 1, 300)? as u64
            ),
            max_audio_chunk_bytes: chunk,
            log_transcripts,
            log_level: LogLevel::parse(&get("LOG_LEVEL").unwrap_or_else(|| "info".into()))?,
        })
    }
}
