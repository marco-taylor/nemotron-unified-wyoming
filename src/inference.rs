//! Replaceable factory/session boundary; only sherpa provides real recognition.
use crate::{Error, Result};
use std::path::{Path, PathBuf};

pub const SHERPA_COMMIT: &str = "31ba0e438f8065189a8e5589d84dfd7faf516d3d";
#[derive(Debug, Clone)]
pub struct SessionConfig {
    pub model_dir: PathBuf,
    pub language: String,
    pub threads: usize,
    pub encoder_path: Option<PathBuf>,
    pub decoder_path: Option<PathBuf>,
    pub joiner_path: Option<PathBuf>,
    pub tokens_path: Option<PathBuf>,
    pub device: String,
    pub inference_chunk_ms: usize,
}
impl Default for SessionConfig {
    fn default() -> Self {
        Self {
            model_dir: "/models".into(),
            language: "de".into(),
            threads: 2,
            encoder_path: None,
            decoder_path: None,
            joiner_path: None,
            tokens_path: None,
            device: "cpu".into(),
            inference_chunk_ms: 20,
        }
    }
}
impl SessionConfig {
    pub fn path(&self, name: &str) -> PathBuf {
        let override_path = match name {
            "encoder.int8.onnx" => &self.encoder_path,
            "decoder.onnx" => &self.decoder_path,
            "joiner.onnx" => &self.joiner_path,
            "tokens.txt" => &self.tokens_path,
            _ => &None,
        };
        match override_path {
            Some(p) if p.is_absolute() => p.clone(),
            Some(p) => self.model_dir.join(p),
            None => self.model_dir.join(name),
        }
    }
    pub fn files(&self) -> Vec<PathBuf> {
        [
            "encoder.int8.onnx",
            "decoder.onnx",
            "joiner.onnx",
            "tokens.txt",
        ]
        .iter()
        .map(|n| self.path(n))
        .collect()
    }
    pub fn validate(&self) -> Result<()> {
        if self.language != "de" {
            return Err(Error::InvalidInput("language must be de"));
        }
        if ![1, 2, 4].contains(&self.threads) {
            return Err(Error::InvalidInput("threads must be 1, 2, or 4"));
        }
        if self.device != "cpu" {
            return Err(Error::InvalidInput("STT_DEVICE: only cpu is supported"));
        }
        if !(10..=560).contains(&self.inference_chunk_ms) {
            return Err(Error::InvalidInput("INFERENCE_CHUNK_MS must be 10..=560"));
        }
        for name in [
            "encoder.int8.onnx",
            "decoder.onnx",
            "joiner.onnx",
            "tokens.txt",
        ] {
            let p = self.path(name);
            let metadata = std::fs::metadata(&p).map_err(|e| {
                if e.kind() == std::io::ErrorKind::NotFound {
                    Error::Runtime(format!("missing model file: {}", p.display()))
                } else {
                    Error::Runtime(format!("cannot access model file {}: {e}", p.display()))
                }
            })?;
            if !metadata.is_file() {
                return Err(Error::Runtime(format!(
                    "missing model file: {}",
                    p.display()
                )));
            }
            let file = std::fs::File::open(&p)
                .map_err(|e| Error::Runtime(format!("cannot read {}: {e}", p.display())))?;
            if file.metadata()?.len() == 0 {
                return Err(Error::Runtime(format!("empty model file: {}", p.display())));
            }
            if p.to_str().is_none_or(|s| s.contains('\0')) {
                return Err(Error::InvalidInput("model paths must be UTF-8 without NUL"));
            }
        }
        Ok(())
    }
}
/// Calls are sequential; no shared mutable streams, no project-owned unsafe code.
pub trait RecognitionSession {
    fn push_pcm(&mut self, pcm: &[i16]) -> Result<Option<String>>;
    fn finish(&mut self) -> Result<String>;
}
pub trait Backend {
    fn name(&self) -> &'static str;
    fn create_session(&self) -> Result<Box<dyn RecognitionSession>>;
}

pub struct UnavailableBackend;
impl Backend for UnavailableBackend {
    fn name(&self) -> &'static str {
        "unavailable"
    }
    fn create_session(&self) -> Result<Box<dyn RecognitionSession>> {
        Err(Error::NotImplemented(
            "build with --features sherpa and provide real ONNX files",
        ))
    }
}

#[cfg(feature = "sherpa")]
pub struct SherpaBackend {
    recognizer: std::rc::Rc<sherpa_onnx::OnlineRecognizer>,
    chunk_samples: usize,
}
#[cfg(feature = "sherpa")]
impl SherpaBackend {
    pub fn load(config: &SessionConfig) -> Result<Self> {
        config.validate()?;
        let native_sha = sherpa_onnx::git_sha1();
        if native_sha != SHERPA_COMMIT {
            return Err(Error::Runtime(format!(
                "loaded native git SHA mismatch: {native_sha}"
            )));
        }
        crate::model::validate_l37(&config.path("encoder.int8.onnx"))?;
        // The Docker build writes this next to its libraries; fail closed on other builds.
        let lib_dir =
            std::env::var("SHERPA_ONNX_LIB_DIR").unwrap_or_else(|_| "/opt/sherpa/lib".into());
        let stamp = std::fs::read_to_string(Path::new(&lib_dir).join("SOURCE_COMMIT"))?;
        if stamp.trim() != SHERPA_COMMIT {
            return Err(Error::InvalidInput("native runtime commit mismatch"));
        }
        let path = |name: &str| config.path(name).to_str().unwrap().to_owned();
        let mut c = sherpa_onnx::OnlineRecognizerConfig::default();
        c.model_config.transducer.encoder = Some(path("encoder.int8.onnx"));
        c.model_config.transducer.decoder = Some(path("decoder.onnx"));
        c.model_config.transducer.joiner = Some(path("joiner.onnx"));
        c.model_config.tokens = Some(path("tokens.txt"));
        c.model_config.provider = Some(config.device.clone());
        c.model_config.num_threads = config.threads as i32;
        c.decoding_method = Some(crate::decoder::DECODING_METHOD.into());
        c.enable_endpoint = false; // Wyoming audio-stop / corpus boundaries own finalization.
        let recognizer = sherpa_onnx::OnlineRecognizer::create(&c).ok_or_else(|| {
            Error::Runtime(format!(
                "sherpa recognizer creation failed in {}; see native ONNX Runtime diagnostics",
                config.model_dir.display()
            ))
        })?;
        Ok(Self {
            recognizer: std::rc::Rc::new(recognizer),
            chunk_samples: config.inference_chunk_ms * 16,
        })
    }
}
#[cfg(feature = "sherpa")]
impl Backend for SherpaBackend {
    fn name(&self) -> &'static str {
        "nemotron-unified-l37-int8"
    }
    fn create_session(&self) -> Result<Box<dyn RecognitionSession>> {
        let stream = self.recognizer.create_stream();
        stream.set_option("language", "de");
        if stream.get_option("language") != "de" {
            return Err(Error::Runtime("per-stream language option rejected".into()));
        }
        Ok(Box::new(SherpaSession {
            stream,
            recognizer: self.recognizer.clone(),
            finished: false,
            chunk_samples: self.chunk_samples,
        }))
    }
}
#[cfg(feature = "sherpa")]
struct SherpaSession {
    // Stream drops before its recognizer owner.
    stream: sherpa_onnx::OnlineStream,
    recognizer: std::rc::Rc<sherpa_onnx::OnlineRecognizer>,
    finished: bool,
    chunk_samples: usize,
}
#[cfg(feature = "sherpa")]
impl SherpaSession {
    fn drain(&self) {
        while self.recognizer.is_ready(&self.stream) {
            self.recognizer.decode(&self.stream);
        }
    }
    fn text(&self) -> Result<String> {
        self.recognizer
            .get_result(&self.stream)
            .map(|r| r.text)
            .ok_or_else(|| Error::Runtime("sherpa returned invalid/missing result JSON".into()))
    }
}
#[cfg(feature = "sherpa")]
impl RecognitionSession for SherpaSession {
    fn push_pcm(&mut self, pcm: &[i16]) -> Result<Option<String>> {
        if self.finished {
            return Err(Error::InvalidInput("input after finish"));
        }
        if pcm.len() > 16_000 * 60 {
            return Err(Error::InvalidInput("PCM chunk exceeds one minute"));
        }
        let samples: Vec<f32> = pcm.iter().map(|&s| f32::from(s) / 32768.0).collect();
        for part in samples.chunks(self.chunk_samples) {
            self.stream.accept_waveform(16_000, part);
            self.drain();
        }
        let text = self.text()?;
        Ok(if text.is_empty() { None } else { Some(text) })
    }
    fn finish(&mut self) -> Result<String> {
        if self.finished {
            return Err(Error::InvalidInput("duplicate finish"));
        }
        self.finished = true;
        // Unified PR handles trailing context at EOF; do not invent silence padding.
        self.stream.input_finished();
        self.drain();
        self.text()
    }
}

pub fn load_backend(config: &SessionConfig) -> Result<Box<dyn Backend>> {
    #[cfg(feature = "sherpa")]
    {
        Ok(Box::new(SherpaBackend::load(config)?))
    }
    #[cfg(not(feature = "sherpa"))]
    {
        let _ = config;
        Err(Error::NotImplemented("binary has no sherpa feature"))
    }
}

pub fn required_model_files(dir: &Path) -> Vec<PathBuf> {
    [
        "encoder.int8.onnx",
        "decoder.onnx",
        "joiner.onnx",
        "tokens.txt",
    ]
    .iter()
    .map(|n| dir.join(n))
    .collect()
}
