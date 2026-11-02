//! Bounded Wyoming JSONL header + optional data block + binary payload codec.
use crate::inference::{Backend, RecognitionSession};
use crate::{Error, Result};
use serde_json::{json, Map, Value};
use std::io::{BufRead, Read, Write};

const HEADER_LIMIT: usize = 16 * 1024;
const DATA_LIMIT: usize = 64 * 1024;
const PAYLOAD_LIMIT: usize = 320_000;
const SESSION_SAMPLES_LIMIT: usize = 16_000 * 120;
#[derive(Debug, Clone, PartialEq)]
pub struct Event {
    pub kind: String,
    pub data: Map<String, Value>,
    pub payload: Vec<u8>,
}
impl Event {
    pub fn new(kind: &str, data: Value) -> Self {
        Self {
            kind: kind.into(),
            data: data.as_object().cloned().unwrap_or_default(),
            payload: Vec::new(),
        }
    }
}
fn length(h: &Value, key: &str, limit: usize) -> Result<usize> {
    match h.get(key) {
        None => Ok(0),
        Some(v) => {
            let n = v
                .as_u64()
                .ok_or(Error::InvalidInput("length must be unsigned integer"))?;
            if n > limit as u64 {
                return Err(Error::InvalidInput("frame limit exceeded"));
            }
            Ok(n as usize)
        }
    }
}
pub fn read_event<R: BufRead>(reader: &mut R) -> Result<Option<Event>> {
    read_event_with_limit(reader, PAYLOAD_LIMIT)
}
pub fn read_event_with_limit<R: BufRead>(
    reader: &mut R,
    payload_limit: usize,
) -> Result<Option<Event>> {
    let mut header = Vec::new();
    reader
        .take((HEADER_LIMIT + 1) as u64)
        .read_until(b'\n', &mut header)?;
    if header.is_empty() {
        return Ok(None);
    }
    if header.len() > HEADER_LIMIT || header.last() != Some(&b'\n') {
        return Err(Error::InvalidInput("header too long or missing newline"));
    }
    let h: Value = serde_json::from_slice(&header)?;
    let kind = h
        .get("type")
        .and_then(Value::as_str)
        .filter(|s| !s.is_empty())
        .ok_or(Error::InvalidInput("missing event type"))?
        .to_owned();
    let mut data = match h.get("data") {
        None => Map::new(),
        Some(Value::Object(d)) => d.clone(),
        _ => return Err(Error::InvalidInput("data must be an object")),
    };
    let n = length(&h, "data_length", DATA_LIMIT)?;
    let p = length(&h, "payload_length", payload_limit.min(PAYLOAD_LIMIT))?;
    if n > 0 {
        let mut bytes = vec![0; n];
        reader.read_exact(&mut bytes)?;
        let block: Map<String, Value> = serde_json::from_slice(&bytes)?;
        data.extend(block); // External block overrides inline data, matching Python reference.
    }
    let mut payload = vec![0; p];
    reader.read_exact(&mut payload)?;
    Ok(Some(Event {
        kind,
        data,
        payload,
    }))
}
pub fn write_event<W: Write>(writer: &mut W, event: &Event) -> Result<()> {
    let data = serde_json::to_vec(&event.data)?;
    if data.len() > DATA_LIMIT || event.payload.len() > PAYLOAD_LIMIT {
        return Err(Error::InvalidInput("output frame limit exceeded"));
    }
    let header =
        json!({"type":event.kind,"data_length":data.len(),"payload_length":event.payload.len()});
    serde_json::to_writer(&mut *writer, &header)?;
    writer.write_all(b"\n")?;
    writer.write_all(&data)?;
    writer.write_all(&event.payload)?;
    writer.flush()?;
    Ok(())
}
fn format(data: &Map<String, Value>) -> Result<()> {
    if data.get("rate").and_then(Value::as_u64) != Some(16_000)
        || data.get("width").and_then(Value::as_u64) != Some(2)
        || data.get("channels").and_then(Value::as_u64) != Some(1)
    {
        return Err(Error::InvalidInput(
            "requires rate=16000, width=2, channels=1",
        ));
    }
    Ok(())
}
#[derive(Default)]
enum State {
    #[default]
    Idle,
    Requested,
    Audio {
        session: Box<dyn RecognitionSession>,
        samples: usize,
    },
}
pub struct Handler<'a> {
    backend: &'a dyn Backend,
    state: State,
    sample_limit: usize,
}
impl<'a> Handler<'a> {
    pub fn new(backend: &'a dyn Backend) -> Self {
        Self {
            backend,
            state: State::Idle,
            sample_limit: SESSION_SAMPLES_LIMIT,
        }
    }
    pub fn with_sample_limit(backend: &'a dyn Backend, sample_limit: usize) -> Self {
        Self {
            backend,
            state: State::Idle,
            sample_limit,
        }
    }
    pub fn active(&self) -> bool {
        !matches!(self.state, State::Idle)
    }
    pub fn handle(&mut self, event: Event) -> Vec<Event> {
        match self.handle_inner(event) {
            Ok(events) => events,
            Err(e) => {
                self.state = State::Idle;
                vec![Event::new(
                    "error",
                    json!({"code":"stt-error","text":e.to_string()}),
                )]
            }
        }
    }
    fn handle_inner(&mut self, event: Event) -> Result<Vec<Event>> {
        if event.kind != "audio-chunk" && !event.payload.is_empty() {
            return Err(Error::InvalidInput("unexpected binary payload"));
        }
        match event.kind.as_str() {
            "describe" => Ok(vec![info(self.backend.name())]),
            // info is a peer advertisement, never an STT request. Consume without echo.
            "info" => {
                if event.data.get("asr").is_some_and(|v| !v.is_array()) {
                    return Err(Error::InvalidInput("info.asr must be an array"));
                }
                Ok(vec![])
            }
            "select-program" => {
                if event.data.get("name").and_then(Value::as_str) != Some(self.backend.name()) {
                    return Err(Error::InvalidInput("unknown ASR program"));
                }
                Ok(vec![])
            }
            "transcribe" if matches!(self.state, State::Idle) => {
                if let Some(lang) = event.data.get("language") {
                    if !lang.is_null() && lang.as_str() != Some("de") {
                        return Err(Error::InvalidInput("only de is supported"));
                    }
                }
                if let Some(name) = event.data.get("name") {
                    if !name.is_null() && name.as_str() != Some(self.backend.name()) {
                        return Err(Error::InvalidInput("unknown ASR model name"));
                    }
                }
                self.state = State::Requested;
                Ok(vec![])
            }
            "audio-start" if matches!(self.state, State::Requested) => {
                format(&event.data)?;
                self.state = State::Audio {
                    session: self.backend.create_session()?,
                    samples: 0,
                };
                Ok(vec![])
            }
            "audio-chunk" => {
                format(&event.data)?;
                if event.payload.is_empty() || !event.payload.len().is_multiple_of(2) {
                    return Err(Error::InvalidInput(
                        "PCM payload must contain complete i16 samples",
                    ));
                }
                let State::Audio { session, samples } = &mut self.state else {
                    return Err(Error::InvalidInput("audio-chunk without audio-start"));
                };
                *samples += event.payload.len() / 2;
                if *samples > self.sample_limit {
                    return Err(Error::InvalidInput(
                        "configured audio duration limit exceeded",
                    ));
                }
                let pcm = crate::audio::decode_pcm16(&event.payload)?;
                // Partial hypotheses are observed by benchmark, not emitted as final transcripts.
                session.push_pcm(&pcm)?;
                Ok(vec![])
            }
            "audio-stop" => {
                let State::Audio {
                    mut session,
                    samples,
                } = std::mem::take(&mut self.state)
                else {
                    return Err(Error::InvalidInput("audio-stop without audio-start"));
                };
                if samples == 0 {
                    return Err(Error::InvalidInput("empty audio"));
                }
                let text = session.finish()?;
                Ok(vec![Event::new(
                    "transcript",
                    json!({"text":text,"language":"de"}),
                )])
            }
            "transcribe" | "audio-start" => Err(Error::InvalidInput("invalid event order")),
            // Wyoming requires unknown extension events to be dropped for forward compatibility.
            _ => Ok(vec![]),
        }
    }
}
pub fn connection<R: BufRead, W: Write>(
    reader: &mut R,
    writer: &mut W,
    backend: &dyn Backend,
) -> Result<()> {
    let mut handler = Handler::new(backend);
    loop {
        match read_event(reader) {
            Ok(Some(event)) => {
                for response in handler.handle(event) {
                    write_event(writer, &response)?;
                }
            }
            Ok(None) => return Ok(()),
            Err(e) => {
                write_event(
                    writer,
                    &Event::new(
                        "error",
                        json!({"code":"invalid-frame","text":e.to_string()}),
                    ),
                )?;
                return Err(e); // Framing errors cannot be safely resynchronized.
            }
        }
    }
}
pub fn info(name: &str) -> Event {
    let asr = if name == "unavailable" {
        json!([])
    } else {
        json!([{"name":name,"description":"Nemotron Unified CPU","version":env!("CARGO_PKG_VERSION"),"installed":true,
        "attribution":{"name":"NVIDIA","url":"https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b"},
        "supports_transcript_streaming":false,"requires_external_vad":true,
        "models":[{"name":name,"description":"L37 INT8, de, 1.12s","installed":true,
        "attribution":{"name":"NVIDIA","url":"https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b"},"languages":["de"]}]}])
    };
    Event::new("info", json!({"asr":asr}))
}
