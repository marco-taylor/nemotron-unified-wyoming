//! Real backend timing only. No generated transcript substitutes.
use crate::inference::{Backend, SessionConfig, SHERPA_COMMIT};
use crate::{Error, Result};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::io::Read;
use std::path::Path;
use std::time::{Duration, Instant};
use unicode_normalization::UnicodeNormalization;

pub fn sha256(path: &Path) -> Result<String> {
    let mut file = std::fs::File::open(path)?;
    let mut h = Sha256::new();
    let mut buf = [0; 65536];
    loop {
        let n = file.read(&mut buf)?;
        if n == 0 {
            break;
        }
        h.update(&buf[..n]);
    }
    Ok(format!("{:x}", h.finalize()))
}
pub fn normalize(s: &str) -> String {
    s.nfc()
        .flat_map(char::to_lowercase)
        .map(|c| {
            if c.is_alphanumeric() || c.is_whitespace() {
                c
            } else {
                ' '
            }
        })
        .collect::<String>()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}
pub fn word_errors(reference: &str, hypothesis: &str) -> (usize, usize) {
    let r = normalize(reference);
    let h = normalize(hypothesis);
    let r: Vec<_> = r.split_whitespace().collect();
    let h: Vec<_> = h.split_whitespace().collect();
    let mut row: Vec<usize> = (0..=h.len()).collect();
    for (i, a) in r.iter().enumerate() {
        let mut prev = row[0];
        row[0] = i + 1;
        for (j, b) in h.iter().enumerate() {
            let old = row[j + 1];
            row[j + 1] = (prev + usize::from(a != b)).min(row[j] + 1).min(old + 1);
            prev = old;
        }
    }
    (row[h.len()], r.len())
}
fn peak_rss_bytes() -> Option<u64> {
    std::fs::read_to_string("/proc/self/status")
        .ok()?
        .lines()
        .find_map(|s| {
            s.strip_prefix("VmHWM:")
                .and_then(|s| s.split_whitespace().next())
                .and_then(|s| s.parse::<u64>().ok())
                .map(|kb| kb * 1024)
        })
}
pub fn run(
    backend: &dyn Backend,
    config: &SessionConfig,
    wav: &Path,
    reference: &str,
    paced: bool,
    load_ms: f64,
) -> Result<serde_json::Value> {
    let pcm = crate::audio::read_wav(wav)?;
    if pcm.len() < 1280 || pcm.len() > 16_000 * 120 {
        return Err(Error::InvalidInput("benchmark audio requires 80ms..120s"));
    }
    // One unmeasured warm-up session. A new stream starts the timed utterance.
    let mut warm = backend.create_session()?;
    for chunk in pcm.chunks(2560) {
        warm.push_pcm(chunk)?;
    }
    warm.finish()?;
    drop(warm);
    let mut session = backend.create_session()?;
    let start = Instant::now();
    let mut compute = Duration::ZERO;
    let mut first = None;
    let mut fed = 0usize;
    for chunk in pcm.chunks(2560) {
        fed += chunk.len();
        if paced {
            std::thread::sleep(
                Duration::from_secs_f64(fed as f64 / 16000.0).saturating_sub(start.elapsed()),
            );
        }
        let t = Instant::now();
        let partial = session.push_pcm(chunk)?;
        compute += t.elapsed();
        if first.is_none() && partial.as_ref().is_some_and(|s| !s.trim().is_empty()) {
            first = Some(start.elapsed().as_secs_f64() * 1000.0);
        }
    }
    let stop = Instant::now();
    let text = session.finish()?;
    compute += stop.elapsed();
    let final_ms = start.elapsed().as_secs_f64() * 1000.0;
    let after_stop_ms = stop.elapsed().as_secs_f64() * 1000.0;
    let (errors, words) = word_errors(reference, &text);
    let rss = peak_rss_bytes();
    let mut hashes = serde_json::Map::new();
    for p in config.files() {
        hashes.insert(
            p.file_name().unwrap().to_string_lossy().into_owned(),
            json!(sha256(&p)?),
        );
    }
    Ok(
        json!({"schema":1,"backend":backend.name(),"sherpa_commit":SHERPA_COMMIT,
        "threads":config.threads,"language":"de","precision":"encoder-MatMul-QUInt8-partial",
        "left_ms":2960,"chunk_ms":560,"right_ms":560,"algorithmic_latency_ms":1120,
        "paced":paced,"input_packet_samples":2560,"warmup_utterances":1,
        "audio":wav,"audio_sha256":sha256(wav)?,"model_sha256":hashes,
        "audio_seconds":pcm.len() as f64 / 16000.0,"model_load_ms":load_ms,
        "compute_seconds":compute.as_secs_f64(),"rtf":compute.as_secs_f64()/(pcm.len() as f64/16000.0),
        "first_partial_from_start_ms":first,"final_from_start_ms":final_ms,"final_after_audio_stop_ms":after_stop_ms,
        "peak_rss_bytes":rss,"ram_scope":"process VmHWM including load and warmup; read before model hashing",
        "reference":reference,"hypothesis":text,"normalizer":"NFC-lower-alnum-spaces-v1",
        "word_errors":errors,"reference_words":words,"wer":if words>0 { Some(errors as f64/words as f64) } else { None },
        "silence_false_positive":words==0 && !text.trim().is_empty()}),
    )
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn german_wer_and_empty_reference() {
        assert_eq!(
            word_errors("Schalte das Licht ein.", "schalte licht aus"),
            (2, 4)
        );
        assert_eq!(word_errors("TÜR ÄÖÜ ß", "tür äöü ß"), (0, 3));
        assert_eq!(word_errors("", "licht"), (1, 0));
        assert_eq!(word_errors("a b", "a x b"), (1, 2));
    }
}
