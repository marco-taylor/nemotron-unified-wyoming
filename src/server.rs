//! Bounded connection workers and one inference owner. No native recognizer crosses threads.
use crate::{
    config::{Config, LogLevel},
    inference::Backend,
    wyoming::{self, Event, Handler},
    Error, Result,
};
use serde_json::json;
use std::{
    collections::HashMap,
    io::{BufReader, Read},
    net::{Shutdown, TcpListener, TcpStream, ToSocketAddrs},
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc::{self, Sender},
        Arc,
    },
    thread,
    time::{Duration, Instant},
};

type Reply = (Vec<Event>, bool);
enum Command {
    Event(u64, Event, Sender<Reply>),
    Disconnect(u64),
}
struct Client {
    socket: TcpStream,
    thread: thread::JoinHandle<()>,
}
/// Absolute per-frame deadline prevents a slowly trickled header from retaining a slot forever.
struct DeadlineReader {
    socket: TcpStream,
    deadline: Instant,
}
impl Read for DeadlineReader {
    fn read(&mut self, bytes: &mut [u8]) -> std::io::Result<usize> {
        let remaining = self
            .deadline
            .checked_duration_since(Instant::now())
            .ok_or_else(|| {
                std::io::Error::new(
                    std::io::ErrorKind::TimedOut,
                    "frame/session deadline exceeded",
                )
            })?;
        self.socket
            .set_read_timeout(Some(remaining.max(Duration::from_millis(1))))?;
        self.socket.read(bytes)
    }
}
fn error(code: &str, text: impl ToString) -> Event {
    Event::new("error", json!({"code":code,"text":text.to_string()}))
}
fn client(
    mut socket: TcpStream,
    id: u64,
    tx: mpsc::SyncSender<Command>,
    stop: Arc<AtomicBool>,
    config: Config,
    info: Event,
) -> Result<()> {
    socket.set_write_timeout(Some(config.client_timeout))?;
    let mut reader = BufReader::new(DeadlineReader {
        socket: socket.try_clone()?,
        deadline: Instant::now() + config.client_timeout,
    });
    let mut session_deadline: Option<Instant> = None;
    let result = (|| -> Result<()> {
        while !stop.load(Ordering::Relaxed) {
            if session_deadline.is_some_and(|d| Instant::now() >= d) {
                wyoming::write_event(&mut socket, &error("timeout", "session deadline exceeded"))?;
                return Ok(());
            }
            reader.get_mut().deadline = (Instant::now() + config.client_timeout)
                .min(session_deadline.unwrap_or(Instant::now() + config.client_timeout));
            let event =
                match wyoming::read_event_with_limit(&mut reader, config.max_audio_chunk_bytes) {
                    Ok(Some(e)) => e,
                    Ok(None) => return Ok(()),
                    Err(e) => {
                        if !stop.load(Ordering::Relaxed) {
                            let _ = wyoming::write_event(&mut socket, &error("invalid-frame", &e));
                        }
                        return Err(e);
                    }
                };
            if config.log_level.enabled(LogLevel::Debug) {
                eprintln!(
                    "debug: client {id}: event={} payload_bytes={}",
                    event.kind,
                    event.payload.len()
                );
            }
            if event.kind == "describe" && event.payload.is_empty() {
                wyoming::write_event(&mut socket, &info)?;
                continue;
            }
            let (reply, responses) = mpsc::channel();
            tx.send(Command::Event(id, event, reply))
                .map_err(|_| Error::Runtime("inference worker unavailable".into()))?;
            let (events, active) = loop {
                match responses.recv_timeout(Duration::from_millis(100)) {
                    Ok(r) => break r,
                    Err(mpsc::RecvTimeoutError::Timeout) if !stop.load(Ordering::Relaxed) => {
                        continue
                    }
                    _ => return Ok(()),
                }
            };
            if active {
                session_deadline.get_or_insert(
                    Instant::now()
                        + Duration::from_secs(config.max_audio_seconds as u64)
                        + config.client_timeout,
                );
            } else {
                session_deadline = None;
            }
            for response in events {
                wyoming::write_event(&mut socket, &response)?;
            }
        }
        Ok(())
    })();
    // At most one outstanding request per bounded client: queue is bounded by max_connections.
    let _ = tx.send(Command::Disconnect(id));
    let _ = socket.shutdown(Shutdown::Both);
    result
}
/// Bind before invocation (also permits an OS-assigned port in tests). Backend is loaded once,
/// inside its owner thread, before accepting clients or reporting readiness.
pub fn serve<F>(
    listener: TcpListener,
    config: Config,
    stop: Arc<AtomicBool>,
    factory: F,
) -> Result<()>
where
    F: FnOnce() -> Result<Box<dyn Backend>> + Send + 'static,
{
    listener.set_nonblocking(true)?;
    let (tx, rx) = mpsc::sync_channel::<Command>(config.max_connections * 2);
    let (ready_tx, ready_rx) = mpsc::channel();
    let worker_stop = stop.clone();
    let sample_limit = config.max_audio_seconds * 16_000;
    let worker_config = config.clone();
    let worker = thread::spawn(move || -> Result<()> {
        let backend = match factory() {
            Ok(b) => b,
            Err(e) => {
                let _ = ready_tx.send(Err(e.to_string()));
                return Err(e);
            }
        };
        let _ = ready_tx.send(Ok(wyoming::info(backend.name())));
        let mut sessions = HashMap::new();
        while !worker_stop.load(Ordering::Relaxed) {
            match rx.recv_timeout(Duration::from_millis(100)) {
                Ok(Command::Event(id, event, reply)) => {
                    let handler = sessions.entry(id).or_insert_with(|| {
                        Handler::with_sample_limit(backend.as_ref(), sample_limit)
                    });
                    let events = handler.handle(event);
                    let active = handler.active();
                    for event in &events {
                        if let Some(line) = worker_config.transcript_log(event) {
                            eprintln!("{line}");
                        }
                    }
                    let _ = reply.send((events, active));
                    if !active {
                        sessions.remove(&id);
                    }
                }
                Ok(Command::Disconnect(id)) => {
                    sessions.remove(&id);
                }
                Err(mpsc::RecvTimeoutError::Timeout) => (),
                Err(_) => break,
            }
        }
        Ok(())
    });
    let info = match ready_rx.recv() {
        Ok(Ok(i)) => i,
        other => {
            let _ = worker.join();
            return Err(Error::Runtime(format!("model startup failed: {other:?}")));
        }
    };
    if config.log_level.enabled(LogLevel::Info) {
        eprintln!(
            "ready: Wyoming {} / {} / threads={} / max_clients={} / max_audio={}s",
            listener.local_addr()?,
            env!("CARGO_PKG_VERSION"),
            config.model.threads,
            config.max_connections,
            config.max_audio_seconds
        );
    }
    let mut clients: Vec<Client> = Vec::new();
    let mut id = 0u64;
    let result = (|| -> Result<()> {
        while !stop.load(Ordering::Relaxed) {
            let mut i = 0;
            while i < clients.len() {
                if clients[i].thread.is_finished() {
                    let _ = clients.swap_remove(i).thread.join();
                } else {
                    i += 1;
                }
            }
            if worker.is_finished() {
                return Err(Error::Runtime(
                    "inference worker stopped unexpectedly".into(),
                ));
            }
            match listener.accept() {
                Ok((mut socket, _)) => {
                    if clients.len() >= config.max_connections {
                        socket.set_write_timeout(Some(Duration::from_millis(100)))?;
                        let _ = wyoming::write_event(
                            &mut socket,
                            &error("busy", "connection limit reached"),
                        );
                        continue;
                    }
                    id += 1;
                    let control = socket.try_clone()?;
                    let (tx, stop, config, info) =
                        (tx.clone(), stop.clone(), config.clone(), info.clone());
                    let handle = thread::spawn(move || {
                        if let Err(e) = client(socket, id, tx, stop.clone(), config.clone(), info) {
                            if !stop.load(Ordering::Relaxed)
                                && config.log_level.enabled(LogLevel::Warn)
                            {
                                eprintln!("client {id}: {e}");
                            }
                        }
                    });
                    clients.push(Client {
                        socket: control,
                        thread: handle,
                    });
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    thread::sleep(Duration::from_millis(20))
                }
                Err(e) => return Err(e.into()),
            }
        }
        Ok(())
    })();
    stop.store(true, Ordering::Relaxed);
    for c in &clients {
        let _ = c.socket.shutdown(Shutdown::Both);
    }
    // Worker finishes the current native call and then frees every session and the model.
    let worker_result = worker
        .join()
        .map_err(|_| Error::Runtime("inference worker panicked".into()))?;
    drop(tx);
    for c in clients {
        let _ = c.thread.join();
    }
    if config.log_level.enabled(LogLevel::Info) {
        eprintln!("shutdown complete");
    }
    result.and(worker_result)
}
/// Real Wyoming describe/info probe; never loads a second copy of the model.
pub fn healthcheck(bind: &str) -> Result<()> {
    let addr = bind
        .to_socket_addrs()?
        .next()
        .ok_or(Error::InvalidInput("invalid listen address"))?;
    let ip = if addr.ip().is_unspecified() {
        if addr.is_ipv4() {
            "127.0.0.1".parse().unwrap()
        } else {
            "::1".parse().unwrap()
        }
    } else {
        addr.ip()
    };
    let mut socket = TcpStream::connect_timeout(
        &std::net::SocketAddr::new(ip, addr.port()),
        Duration::from_secs(3),
    )?;
    socket.set_write_timeout(Some(Duration::from_secs(3)))?;
    wyoming::write_event(&mut socket, &Event::new("describe", json!({})))?;
    let reader = DeadlineReader {
        socket,
        deadline: Instant::now() + Duration::from_secs(3),
    };
    let response = wyoming::read_event(&mut BufReader::new(reader))?
        .ok_or(Error::InvalidInput("healthcheck EOF"))?;
    if response.kind != "info"
        || !response
            .data
            .get("asr")
            .and_then(|v| v.as_array())
            .is_some_and(|a| {
                a.iter().any(|p| {
                    p["installed"] == true
                        && p["models"].as_array().is_some_and(|m| {
                            m.iter().any(|m| {
                                m["installed"] == true
                                    && m["languages"]
                                        .as_array()
                                        .is_some_and(|l| l.iter().any(|v| v == "de"))
                            })
                        })
                })
            })
    {
        return Err(Error::InvalidInput(
            "healthcheck: no installed German ASR model",
        ));
    }
    Ok(())
}
