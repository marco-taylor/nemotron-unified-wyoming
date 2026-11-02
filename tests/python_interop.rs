//! Runs the pinned official Python Wyoming codec in Docker (no host Python required).
use nemotron_unified_rust_wyoming::wyoming::{read_event, write_event};
use std::io::{Cursor, Write};
use std::process::{Command, Stdio};
#[test]
fn official_python_rust_bidirectional_wire_interop() {
    let output = Command::new("python3")
        .args(["tests/reference/interop.py", "write"])
        .output()
        .expect("Docker toolchain must include python3");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let mut reader = Cursor::new(output.stdout);
    let mut events = vec![];
    while let Some(e) = read_event(&mut reader).unwrap() {
        events.push(e);
    }
    assert_eq!(events.len(), 5);
    assert_eq!(events[2].payload, [0, 128, 255, 127, 10, 0]);
    assert_eq!(events[4].data["text"], "Öffne die Tür.");
    let mut wire = vec![];
    for e in events {
        write_event(&mut wire, &e).unwrap();
    }
    let mut python = Command::new("python3")
        .args(["tests/reference/interop.py", "read"])
        .stdin(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    python.stdin.take().unwrap().write_all(&wire).unwrap();
    let result = python.wait_with_output().unwrap();
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
}
#[test]
fn official_typed_info_and_error_parse_rust_responses() {
    use nemotron_unified_rust_wyoming::wyoming::{info, Event};
    let mut wire = vec![];
    write_event(&mut wire, &info("protocol-fixture-not-asr")).unwrap();
    write_event(
        &mut wire,
        &Event::new(
            "error",
            serde_json::json!({"text":"test-only error","code":"test"}),
        ),
    )
    .unwrap();
    let mut python = Command::new("python3")
        .args(["tests/reference/interop.py", "read-info"])
        .stdin(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    python.stdin.take().unwrap().write_all(&wire).unwrap();
    let result = python.wait_with_output().unwrap();
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
}
