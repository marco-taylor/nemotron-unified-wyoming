//! PCM validation and conversion. Native sherpa performs model-compatible feature
//! extraction; this server intentionally accepts only the required 16 kHz format.
use crate::{Error, Result};
#[derive(Debug, Clone, Copy)]
pub struct PcmFormat {
    pub sample_rate: u32,
    pub channels: u16,
    pub sample_width: u16,
}
impl PcmFormat {
    pub fn validate(self) -> Result<()> {
        if self.sample_rate != 16_000 || self.channels != 1 || self.sample_width != 2 {
            return Err(Error::InvalidInput("requires 16 kHz mono signed PCM16 LE"));
        }
        Ok(())
    }
}

pub fn decode_pcm16(bytes: &[u8]) -> Result<Vec<i16>> {
    if !bytes.len().is_multiple_of(2) {
        return Err(Error::InvalidInput("incomplete PCM16 sample"));
    }
    Ok(bytes
        .chunks_exact(2)
        .map(|b| i16::from_le_bytes([b[0], b[1]]))
        .collect())
}
pub fn read_wav(path: &std::path::Path) -> Result<Vec<i16>> {
    let mut reader = hound::WavReader::open(path).map_err(|e| Error::Runtime(e.to_string()))?;
    let s = reader.spec();
    if s.channels != 1
        || s.sample_rate != 16_000
        || s.bits_per_sample != 16
        || s.sample_format != hound::SampleFormat::Int
    {
        return Err(Error::InvalidInput("WAV must be mono PCM16 at 16 kHz"));
    }
    reader
        .samples::<i16>()
        .map(|s| s.map_err(|e| Error::Runtime(e.to_string())))
        .collect()
}
