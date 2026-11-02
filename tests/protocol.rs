//! Test fixtures below validate protocol plumbing only, never ASR accuracy.
use nemotron_unified_rust_wyoming::{
    inference::{Backend, RecognitionSession, UnavailableBackend},
    wyoming::*,
    Result,
};
use serde_json::json;
use std::io::{BufReader, Cursor, Read};
use std::sync::{Arc, Mutex};

fn roundtrip(e: &Event) -> Event {
    let mut bytes = Vec::new();
    write_event(&mut bytes, e).unwrap();
    read_event(&mut Cursor::new(bytes)).unwrap().unwrap()
}
#[test]
fn audio_and_transcription_wire_roundtrips() {
    for kind in ["transcribe", "audio-start", "audio-stop", "transcript"] {
        let d = if kind == "transcript" {
            json!({"text":"Öffne die Tür.","language":"de"})
        } else {
            json!({"rate":16000,"width":2,"channels":1,"language":"de"})
        };
        let e = Event::new(kind, d);
        assert_eq!(roundtrip(&e), e);
    }
    let mut e = Event::new("audio-chunk", json!({"rate":16000,"width":2,"channels":1}));
    e.payload = vec![0, 128, 255, 127, 0, 0, 10, 0];
    assert_eq!(roundtrip(&e), e);
    assert_eq!(
        nemotron_unified_rust_wyoming::audio::decode_pcm16(&e.payload).unwrap(),
        [-32768, 32767, 0, 10]
    );
}
#[test]
fn separate_data_overrides_inline_and_preserves_next_frame() {
    let block = br#"{"language":"de"}"#;
    let h = format!(
        "{{\"type\":\"transcribe\",\"data\":{{\"language\":\"en\"}},\"data_length\":{}}}\n",
        block.len()
    );
    let bytes = [h.as_bytes(), block, b"{\"type\":\"audio-stop\"}\n"].concat();
    let mut r = Cursor::new(bytes);
    assert_eq!(read_event(&mut r).unwrap().unwrap().data["language"], "de");
    assert_eq!(read_event(&mut r).unwrap().unwrap().kind, "audio-stop");
    assert!(read_event(&mut r).unwrap().is_none());
}
struct OneByte<R>(R);
impl<R: Read> Read for OneByte<R> {
    fn read(&mut self, b: &mut [u8]) -> std::io::Result<usize> {
        let n = b.len().min(1);
        self.0.read(&mut b[..n])
    }
}
#[test]
fn fragmented_reads_and_binary_newlines() {
    let mut e = Event::new("audio-chunk", json!({"rate":16000,"width":2,"channels":1}));
    e.payload = vec![10, 0, 13, 0];
    let mut bytes = vec![];
    write_event(&mut bytes, &e).unwrap();
    assert_eq!(
        read_event(&mut BufReader::new(OneByte(Cursor::new(bytes))))
            .unwrap()
            .unwrap(),
        e
    );
}
#[test]
fn rejects_malformed_truncated_and_excessive_frames() {
    for b in [
        b"{}\n".to_vec(),
        b"{\"type\":\"a\",\"payload_length\":-1}\n".to_vec(),
        b"{\"type\":\"a\",\"payload_length\":320001}\n".to_vec(),
        b"{\"type\":\"a\",\"data_length\":3}\n{}".to_vec(),
        b"{\"type\":\"a\",\"payload_length\":2}\nx".to_vec(),
        b"{\"type\":\"a\",\"data\":[]}\n".to_vec(),
        vec![b'x'; 16385],
    ] {
        assert!(read_event(&mut Cursor::new(b)).is_err());
    }
}
// Explicit protocol-test-only double. Production never constructs it.
struct FixtureBackend(Arc<Mutex<Vec<i16>>>);
struct FixtureSession(Arc<Mutex<Vec<i16>>>);
impl Backend for FixtureBackend {
    fn name(&self) -> &'static str {
        "protocol-fixture-not-asr"
    }
    fn create_session(&self) -> Result<Box<dyn RecognitionSession>> {
        Ok(Box::new(FixtureSession(self.0.clone())))
    }
}
impl RecognitionSession for FixtureSession {
    fn push_pcm(&mut self, p: &[i16]) -> Result<Option<String>> {
        self.0.lock().unwrap().extend(p);
        Ok(None)
    }
    fn finish(&mut self) -> Result<String> {
        Ok("PROTOCOL FIXTURE – keine Erkennung".into())
    }
}
fn input_frames() -> Vec<Event> {
    let mut audio = Event::new("audio-chunk", json!({"rate":16000,"width":2,"channels":1}));
    audio.payload = vec![1, 0, 255, 255];
    vec![
        Event::new("transcribe", json!({"language":"de"})),
        Event::new("audio-start", json!({"rate":16000,"width":2,"channels":1})),
        audio,
        Event::new("audio-stop", json!({})),
    ]
}
#[test]
fn full_connection_validates_pcm_and_transcript_framing() {
    let pcm = Arc::new(Mutex::new(vec![]));
    let backend = FixtureBackend(pcm.clone());
    let mut input = vec![];
    for e in input_frames() {
        write_event(&mut input, &e).unwrap();
    }
    let mut output = vec![];
    connection(&mut Cursor::new(input), &mut output, &backend).unwrap();
    let mut r = Cursor::new(output);
    let e = read_event(&mut r).unwrap().unwrap();
    assert_eq!(e.kind, "transcript");
    assert_eq!(e.data["language"], "de");
    assert_eq!(e.data["text"], "PROTOCOL FIXTURE – keine Erkennung");
    assert_eq!(*pcm.lock().unwrap(), vec![1, -1]);
    assert!(read_event(&mut r).unwrap().is_none());
}
#[test]
fn invalid_sequence_format_and_unavailable_backend_never_succeed() {
    let mut h = Handler::new(&UnavailableBackend);
    assert_eq!(
        h.handle(Event::new("describe", json!({})))[0].data["asr"],
        json!([])
    );
    for e in [
        Event::new("audio-stop", json!({})),
        Event::new("transcribe", json!({"language":"en"})),
    ] {
        assert_eq!(h.handle(e)[0].kind, "error");
    }
    assert!(h
        .handle(Event::new("transcribe", json!({"language":"de"})))
        .is_empty());
    assert_eq!(
        h.handle(Event::new(
            "audio-start",
            json!({"rate":48000,"width":2,"channels":1})
        ))[0]
            .kind,
        "error"
    );
    for e in input_frames() {
        let out = h.handle(e);
        assert!(out.iter().all(|x| x.kind != "transcript"));
    }
}
#[test]
fn malformed_wire_returns_error_and_closes() {
    let mut output = vec![];
    assert!(connection(
        &mut Cursor::new(b"{oops}\n"),
        &mut output,
        &UnavailableBackend
    )
    .is_err());
    assert_eq!(
        read_event(&mut Cursor::new(output)).unwrap().unwrap().kind,
        "error"
    );
}
#[test]
fn tcp_loopback_framing_without_asr() {
    use std::net::{TcpListener, TcpStream};
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let addr = listener.local_addr().unwrap();
    let server = std::thread::spawn(move || {
        let (mut socket, _) = listener.accept().unwrap();
        socket
            .set_read_timeout(Some(std::time::Duration::from_secs(3)))
            .unwrap();
        connection(
            &mut BufReader::new(socket.try_clone().unwrap()),
            &mut socket,
            &UnavailableBackend,
        )
        .unwrap();
    });
    let mut client = TcpStream::connect(addr).unwrap();
    client
        .set_read_timeout(Some(std::time::Duration::from_secs(3)))
        .unwrap();
    write_event(&mut client, &Event::new("describe", json!({}))).unwrap();
    let mut r = BufReader::new(client.try_clone().unwrap());
    assert_eq!(read_event(&mut r).unwrap().unwrap().kind, "info");
    client.shutdown(std::net::Shutdown::Both).unwrap();
    server.join().unwrap();
}
#[test]
fn pcm_odd_bytes_rejected_and_sessions_reset_after_errors() {
    assert!(nemotron_unified_rust_wyoming::audio::decode_pcm16(&[1]).is_err());
    let backend = FixtureBackend(Arc::new(Mutex::new(vec![])));
    let mut h = Handler::new(&backend);
    let mut events = input_frames();
    for e in events.drain(..2) {
        assert!(h.handle(e).is_empty());
    }
    events[0].payload = vec![1];
    assert_eq!(h.handle(events.remove(0))[0].kind, "error");
    assert_eq!(h.handle(events.remove(0))[0].kind, "error");
    for e in input_frames() {
        let _ = h.handle(e);
    }
}
#[test]
fn optional_nulls_peer_info_and_unknown_extensions_are_compatible() {
    let backend = FixtureBackend(Arc::new(Mutex::new(vec![])));
    let mut h = Handler::new(&backend);
    assert!(h.handle(Event::new("info", json!({"asr":[]}))).is_empty());
    assert!(h
        .handle(Event::new("future-extension", json!({})))
        .is_empty());
    assert!(h
        .handle(Event::new(
            "select-program",
            json!({"name":"protocol-fixture-not-asr"})
        ))
        .is_empty());
    assert!(h
        .handle(Event::new(
            "transcribe",
            json!({"name":null,"language":null})
        ))
        .is_empty());
    assert!(h.active());
    assert!(h.handle(Event::new("describe", json!({})))[0].kind == "info");
    assert!(h.active());
    assert_eq!(
        h.handle(Event::new("transcribe", json!({})))[0].kind,
        "error"
    );
    assert!(!h.active());
}
