//! German Nemotron Unified ASR integration; requires separately provisioned models.
pub mod audio;
pub mod benchmark;
pub mod config;
pub mod decoder;
pub mod inference;
pub mod server;
pub mod streaming;
pub mod wyoming;

#[derive(Debug)]
pub enum Error {
    InvalidInput(&'static str),
    NotImplemented(&'static str),
    Runtime(String),
    Io(std::io::Error),
    Json(serde_json::Error),
}
impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidInput(s) => write!(f, "invalid input: {s}"),
            Self::NotImplemented(s) => write!(f, "not implemented: {s}"),
            Self::Runtime(s) => write!(f, "runtime: {s}"),
            Self::Io(e) => e.fmt(f),
            Self::Json(e) => e.fmt(f),
        }
    }
}
impl std::error::Error for Error {}
impl From<std::io::Error> for Error {
    fn from(e: std::io::Error) -> Self {
        Self::Io(e)
    }
}
impl From<serde_json::Error> for Error {
    fn from(e: serde_json::Error) -> Self {
        Self::Json(e)
    }
}
pub type Result<T> = std::result::Result<T, Error>;
pub mod model;
