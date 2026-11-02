use nemotron_unified_rust_wyoming::{benchmark, config::Config, inference, server, Error, Result};
use std::path::PathBuf;
fn main() -> std::process::ExitCode {
    match run() {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("{e}");
            std::process::ExitCode::from(2)
        }
    }
}
fn run() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.first().is_some_and(|s| s == "--version") {
        println!("nemotron-wyoming {}", env!("CARGO_PKG_VERSION"));
        return Ok(());
    }
    if args.first().is_some_and(|s| s == "--help") {
        println!("nemotron-wyoming [serve|check-model|healthcheck|benchmark] [--model DIR] [--threads 1|2|4] [--bind HOST:PORT]\nDefaults: MODEL_DIR=/models LANGUAGE=de THREADS=2 WYOMING_HOST=0.0.0.0 WYOMING_PORT=10300\nLimits: MAX_AUDIO_SECONDS=120 MAX_CONNECTIONS=8 CLIENT_TIMEOUT_SECONDS=30 MAX_AUDIO_CHUNK_BYTES=320000\nModel overrides: ENCODER_PATH DECODER_PATH JOINER_PATH TOKENS_PATH (optional, relative to MODEL_DIR or absolute)\nRuntime: STT_DEVICE=cpu INFERENCE_CHUNK_MS=20 LOG_LEVEL=info LOG_TRANSCRIPTS=false\nbenchmark diagnostic: --wav FILE --reference FILE [--paced]\nNo model download; requires separately provisioned L37 INT8 files and pinned native runtime.");
        return Ok(());
    }
    let mode = args.first().map(String::as_str).unwrap_or("serve");
    if !["serve", "benchmark", "check-model", "healthcheck"].contains(&mode) {
        return Err(Error::InvalidInput("unknown subcommand"));
    }
    let mut config = Config::from_env()?;
    let mut options = std::collections::BTreeMap::new();
    let mut paced = false;
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--paced" && mode == "benchmark" {
            paced = true;
            i += 1;
            continue;
        }
        if !["--model", "--threads", "--bind", "--wav", "--reference"].contains(&args[i].as_str())
            || i + 1 >= args.len()
        {
            return Err(Error::InvalidInput("unknown option or missing value"));
        }
        if options
            .insert(args[i].as_str(), args[i + 1].as_str())
            .is_some()
        {
            return Err(Error::InvalidInput("duplicate option"));
        }
        i += 2;
    }
    if let Some(p) = options.get("--model") {
        config.model.model_dir = PathBuf::from(p);
    }
    if let Some(n) = options.get("--threads") {
        config.model.threads = n
            .parse()
            .map_err(|_| Error::InvalidInput("invalid threads"))?;
    }
    if let Some(b) = options.get("--bind") {
        config.bind = b.to_string();
    }
    if mode == "healthcheck" {
        return server::healthcheck(&config.bind);
    }
    config.model.validate()?;
    let metadata = nemotron_unified_rust_wyoming::model::validate_l37(
        &config.model.path("encoder.int8.onnx"),
    )?;
    if mode == "check-model" {
        println!("{}", serde_json::to_string_pretty(&metadata)?);
        return Ok(());
    }
    if mode == "serve" {
        let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
        for signal in [signal_hook::consts::SIGINT, signal_hook::consts::SIGTERM] {
            signal_hook::flag::register(signal, stop.clone())?;
        }
        let listener = std::net::TcpListener::bind(&config.bind)?;
        let model = config.model.clone();
        return server::serve(listener, config, stop, move || {
            inference::load_backend(&model)
        });
    }
    let required = |key| {
        options
            .get(key)
            .copied()
            .ok_or(Error::InvalidInput("missing required option"))
    };
    let load = std::time::Instant::now();
    let backend = inference::load_backend(&config.model)?;
    let load_ms = load.elapsed().as_secs_f64() * 1000.0;
    let reference = std::fs::read_to_string(required("--reference")?)?;
    let record = benchmark::run(
        backend.as_ref(),
        &config.model,
        &PathBuf::from(required("--wav")?),
        &reference,
        paced,
        load_ms,
    )?;
    println!("{}", serde_json::to_string(&record)?);
    Ok(())
}
