//! Read only top-level ONNX metadata; skip tensor/graph bodies without loading weights.
use crate::{Error, Result};
use std::collections::BTreeMap;
use std::io::{Read, Seek, SeekFrom};
fn varint<R: Read>(r: &mut R) -> Result<u64> {
    let mut n = 0u64;
    for shift in (0..70).step_by(7) {
        let mut b = [0];
        r.read_exact(&mut b)?;
        if shift == 63 && b[0] > 1 {
            return Err(Error::InvalidInput("protobuf varint overflow"));
        }
        n |= u64::from(b[0] & 127) << shift;
        if b[0] < 128 {
            return Ok(n);
        }
    }
    Err(Error::InvalidInput("invalid protobuf varint"))
}
fn block<R: Read>(r: &mut R) -> Result<Vec<u8>> {
    let n = varint(r)?;
    if n > 65_536 {
        return Err(Error::InvalidInput("ONNX metadata entry too large"));
    }
    let mut b = vec![0; n as usize];
    r.read_exact(&mut b)?;
    Ok(b)
}
fn read_metadata<R: Read + Seek>(r: &mut R) -> Result<BTreeMap<String, String>> {
    let end = r.seek(SeekFrom::End(0))?;
    r.seek(SeekFrom::Start(0))?;
    let mut out = BTreeMap::new();
    while r.stream_position()? < end {
        let tag = varint(r)?;
        if tag == (14 << 3 | 2) {
            let b = block(r)?;
            let mut e = std::io::Cursor::new(&b);
            let mut key = None;
            let mut value = None;
            while (e.position() as usize) < b.len() {
                let t = varint(&mut e)?;
                let s = String::from_utf8(block(&mut e)?)
                    .map_err(|_| Error::InvalidInput("metadata UTF-8"))?;
                match t {
                    10 => key = Some(s),
                    18 => value = Some(s),
                    _ => return Err(Error::InvalidInput("metadata field")),
                }
            }
            let (Some(k), Some(v)) = (key, value) else {
                return Err(Error::InvalidInput("incomplete metadata"));
            };
            if out.insert(k, v).is_some() {
                return Err(Error::InvalidInput("duplicate metadata key"));
            }
        } else {
            let skip = match tag & 7 {
                0 => {
                    varint(r)?;
                    0
                }
                1 => 8,
                2 => varint(r)?,
                5 => 4,
                _ => return Err(Error::InvalidInput("unsupported protobuf wire type")),
            };
            let pos = r.stream_position()?;
            let next = pos
                .checked_add(skip)
                .ok_or(Error::InvalidInput("ONNX length overflow"))?;
            if next > end {
                return Err(Error::InvalidInput("truncated ONNX field"));
            }
            r.seek(SeekFrom::Start(next))?;
        }
    }
    Ok(out)
}
pub fn validate_l37(path: &std::path::Path) -> Result<BTreeMap<String, String>> {
    let m = read_metadata(&mut std::fs::File::open(path)?)?;
    for (k, v) in [
        ("streaming_model_type", "nemo_parakeet_unified_streaming"),
        ("left_encoder_frames", "37"),
        ("chunk_encoder_frames", "7"),
        ("right_encoder_frames", "7"),
        ("buffered_streaming", "1"),
    ] {
        if m.get(k).map(String::as_str) != Some(v) {
            return Err(Error::Runtime(format!(
                "model metadata mismatch: {k} must be {v}"
            )));
        }
    }
    let prompts: BTreeMap<String, u64> = serde_json::from_str(
        m.get("prompt_dictionary")
            .or_else(|| m.get("language_prompt_ids"))
            .ok_or(Error::InvalidInput(
                "multilingual language prompt metadata missing",
            ))?,
    )?;
    if !prompts.contains_key("de") {
        return Err(Error::InvalidInput("German prompt missing"));
    }
    Ok(m)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn reads_metadata_and_skips_graph() {
        let bytes = [58, 3, 0, 0, 0, 114, 6, 10, 1, b'k', 18, 1, b'v'];
        assert_eq!(
            read_metadata(&mut std::io::Cursor::new(bytes)).unwrap()["k"],
            "v"
        );
    }
    #[test]
    fn rejects_truncation_and_overflow() {
        assert!(read_metadata(&mut std::io::Cursor::new([58, 100, 0])).is_err());
        assert!(read_metadata(&mut std::io::Cursor::new([255; 12])).is_err());
    }
}
