//! Real TCP and lifecycle tests. The explicitly named fixture is not an ASR model.
use nemotron_unified_rust_wyoming::{
    config::Config,
    inference::{Backend, RecognitionSession, SessionConfig},
    server,
    wyoming::{read_event, write_event, Event},
    Result,
};
use serde_json::json;
use std::{
    io::{BufReader, Write},
    net::{Shutdown, TcpListener, TcpStream},
    sync::{
        atomic::{AtomicBool, AtomicUsize, Ordering},
        Arc,
    },
    thread,
    time::{Duration, Instant},
};
struct Fixture(Arc<AtomicUsize>);
struct Session(Arc<AtomicUsize>);
impl Drop for Session {
    fn drop(&mut self) {
        self.0.fetch_sub(1, Ordering::SeqCst);
    }
}
impl Backend for Fixture {
    fn name(&self) -> &'static str {
        "protocol-fixture-not-asr"
    }
    fn create_session(&self) -> Result<Box<dyn RecognitionSession>> {
        self.0.fetch_add(1, Ordering::SeqCst);
        Ok(Box::new(Session(self.0.clone())))
    }
}
impl RecognitionSession for Session {
    fn push_pcm(&mut self, _: &[i16]) -> Result<Option<String>> {
        Ok(None)
    }
    fn finish(&mut self) -> Result<String> {
        Ok("PROTOCOL FIXTURE – keine Erkennung".into())
    }
}
struct Running {
    addr: String,
    stop: Arc<AtomicBool>,
    handle: Option<thread::JoinHandle<Result<()>>>,
    sessions: Arc<AtomicUsize>,
}
impl Running {
    fn start(max_connections: usize, max_audio_seconds: usize) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let addr = listener.local_addr().unwrap().to_string();
        let mut config = Config::from_values(|_| None).unwrap();
        config.max_connections = max_connections;
        config.max_audio_seconds = max_audio_seconds;
        config.client_timeout = Duration::from_millis(250);
        let stop = Arc::new(AtomicBool::new(false));
        let flag = stop.clone();
        let sessions = Arc::new(AtomicUsize::new(0));
        let count = sessions.clone();
        let handle = thread::spawn(move || {
            server::serve(listener, config, flag, move || Ok(Box::new(Fixture(count))))
        });
        let started = Instant::now();
        while server::healthcheck(&addr).is_err() {
            assert!(started.elapsed() < Duration::from_secs(4));
            thread::sleep(Duration::from_millis(20));
        }
        // Let the healthcheck connection close before testing the configured slot limit.
        thread::sleep(Duration::from_millis(60));
        Self {
            addr,
            stop,
            handle: Some(handle),
            sessions,
        }
    }
    fn connect(&self) -> TcpStream {
        let s = TcpStream::connect(&self.addr).unwrap();
        s.set_read_timeout(Some(Duration::from_secs(3))).unwrap();
        s
    }
    fn shutdown(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
        self.handle.take().unwrap().join().unwrap().unwrap();
        assert_eq!(self.sessions.load(Ordering::SeqCst), 0);
    }
}
impl Drop for Running {
    fn drop(&mut self) {
        if self.handle.is_some() {
            self.shutdown();
        }
    }
}
fn send(s: &mut TcpStream, kind: &str, data: serde_json::Value) {
    write_event(s, &Event::new(kind, data)).unwrap();
}
fn start(s: &mut TcpStream) {
    send(s, "transcribe", json!({"language":"de"}));
    send(
        s,
        "audio-start",
        json!({"rate":16000,"width":2,"channels":1}),
    );
}
fn chunk(s: &mut TcpStream, bytes: usize) {
    let mut e = Event::new("audio-chunk", json!({"rate":16000,"width":2,"channels":1}));
    e.payload = vec![0; bytes];
    write_event(s, &e).unwrap();
}
fn receive(s: &TcpStream) -> Event {
    read_event(&mut BufReader::new(s.try_clone().unwrap()))
        .unwrap()
        .unwrap()
}
#[test]
fn repeated_requests_and_simultaneous_description() {
    let r = Running::start(4, 2);
    let mut s = r.connect();
    for _ in 0..3 {
        start(&mut s);
        chunk(&mut s, 320);
        send(&mut s, "audio-stop", json!({}));
        assert_eq!(receive(&s).kind, "transcript");
    }
    start(&mut s);
    chunk(&mut s, 320);
    assert!(server::healthcheck(&r.addr).is_ok());
    send(&mut s, "describe", json!({}));
    let e = receive(&s);
    assert_eq!(e.kind, "info");
    assert_eq!(e.data["asr"][0]["requires_external_vad"], true);
    send(&mut s, "audio-stop", json!({}));
    assert_eq!(receive(&s).kind, "transcript");
}
#[test]
fn audio_limits_errors_recover_and_disconnect_releases_session() {
    let r = Running::start(4, 1);
    let mut s = r.connect();
    start(&mut s);
    chunk(&mut s, 32002);
    assert_eq!(receive(&s).kind, "error");
    start(&mut s);
    chunk(&mut s, 1);
    assert_eq!(receive(&s).kind, "error");
    start(&mut s);
    send(&mut s, "audio-stop", json!({}));
    assert_eq!(receive(&s).kind, "error");
    start(&mut s);
    chunk(&mut s, 320);
    send(&mut s, "audio-stop", json!({}));
    assert_eq!(receive(&s).kind, "transcript");
    start(&mut s);
    chunk(&mut s, 320);
    send(&mut s, "describe", json!({}));
    assert_eq!(receive(&s).kind, "info");
    assert_eq!(r.sessions.load(Ordering::SeqCst), 1);
    s.shutdown(Shutdown::Both).unwrap();
    let t = Instant::now();
    while r.sessions.load(Ordering::SeqCst) > 0 {
        assert!(t.elapsed() < Duration::from_secs(2));
        thread::sleep(Duration::from_millis(10));
    }
}
#[test]
fn malformed_frame_timeout_and_connection_limit() {
    let r = Running::start(1, 1);
    let mut s = r.connect();
    send(&mut s, "describe", json!({}));
    assert_eq!(receive(&s).kind, "info");
    let second = r.connect();
    assert_eq!(receive(&second).data["code"], "busy");
    s.write_all(b"{\"type\":").unwrap();
    assert_eq!(receive(&s).data["code"], "invalid-frame");
    let t = Instant::now();
    while server::healthcheck(&r.addr).is_err() {
        assert!(t.elapsed() < Duration::from_secs(3));
        thread::sleep(Duration::from_millis(20));
    }
}
#[test]
fn shutdown_unblocks_idle_and_active_connections() {
    let mut r = Running::start(4, 2);
    let _idle = r.connect();
    let mut active = r.connect();
    start(&mut active);
    chunk(&mut active, 320);
    send(&mut active, "describe", json!({}));
    assert_eq!(receive(&active).kind, "info");
    let t = Instant::now();
    r.shutdown();
    assert!(t.elapsed() < Duration::from_secs(2));
}
#[test]
fn configuration_validation_and_missing_models() {
    let c = Config::from_values(|_| None).unwrap();
    assert_eq!(c.model.threads, 2);
    assert_eq!(c.model.language, "de");
    for (k, v) in [
        ("THREADS", "3"),
        ("THREADS", "wrong"),
        ("MAX_CONNECTIONS", "0"),
        ("MAX_AUDIO_SECONDS", "121"),
        ("WYOMING_PORT", "65536"),
        ("LANGUAGE", "en"),
    ] {
        assert!(Config::from_values(|key| (key == k).then(|| v.into())).is_err());
    }
    let c = SessionConfig {
        model_dir: "/this-path-does-not-exist-for-model-tests".into(),
        language: "de".into(),
        threads: 2,
        ..SessionConfig::default()
    };
    assert!(c
        .validate()
        .unwrap_err()
        .to_string()
        .contains("missing model file"));
}
#[test]
fn backend_startup_failure_is_not_ready() {
    let l = TcpListener::bind("127.0.0.1:0").unwrap();
    let result = server::serve(
        l,
        Config::from_values(|_| None).unwrap(),
        Arc::new(AtomicBool::new(false)),
        || {
            Err(nemotron_unified_rust_wyoming::Error::Runtime(
                "model test failure".into(),
            ))
        },
    );
    assert!(result
        .unwrap_err()
        .to_string()
        .contains("model test failure"));
}
#[test]
fn empty_model_file_is_reported_before_native_loading() {
    let dir =
        std::env::temp_dir().join(format!("nemotron-empty-model-test-{}", std::process::id()));
    std::fs::create_dir(&dir).unwrap();
    std::fs::write(dir.join("encoder.int8.onnx"), []).unwrap();
    let c = SessionConfig {
        model_dir: dir.clone(),
        language: "de".into(),
        threads: 2,
        ..SessionConfig::default()
    };
    let error = c.validate().unwrap_err().to_string();
    std::fs::remove_dir_all(dir).unwrap();
    assert!(error.contains("empty model file"));
}
