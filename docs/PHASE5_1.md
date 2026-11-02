# Phase 5.1 – vollständige Docker-Konfiguration

Stand 01.11.2026. Projekt: `/mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming`. Relative Pfade beziehen sich auf dieses Projekt. Keine bestehende STT-Konfiguration verändert, kein produktives Deployment, kein Push/Publishing und kein Modelldownload.

## Unterstützte Variablen

Alle folgenden Variablen werden tatsächlich im Rust-Parser gelesen, auf Wertebereiche geprüft und an die angegebene Funktion weitergereicht. Numerische Werte sind ganze Dezimalzahlen. Fehlermeldungen nennen die Variable. Die vier optionalen Einzelpfade dürfen fehlen oder leer sein; andere leere Werte werden abgewiesen. Nicht UTF-8-kodierte Werte unterstützter Variablen werden nicht stillschweigend durch Defaults ersetzt.

| Variable | Standard | Validierung | Tatsächliche Wirkung |
|---|---|---|---|
| `WYOMING_HOST` | `0.0.0.0` | IPv4 oder IPv6; IPv6 auch mit Klammern | Adresse für TCP-Listener und Healthcheck. Keine DNS-Namen für die Bind-Adresse. |
| `WYOMING_PORT` | `10300` | 1–65535 | TCP-Port des Listeners und Healthchecks im Container. |
| `LANGUAGE` | `de` | ausschließlich `de` | Validiert den deutschen Dienst; jede native Sitzung setzt die deutsche Sprachkonditionierung. Andere Sprachen sind in diesem Server nicht integriert. |
| `STT_DEVICE` | `cpu` | ausschließlich `cpu` | Setzt den sherpa-Ausführungsprovider. Dieses Image hat keine GPU-Runtime. |
| `MODEL_DIR` | `/models` | nicht leer, UTF-8, kein NUL; ausgewählte Dateien müssen existieren und lesbar/nicht leer sein | Basisverzeichnis für Standarddateinamen und relative Einzelpfade. |
| `ENCODER_PATH` | leer → `MODEL_DIR/encoder.int8.onnx` | optional; kein NUL; Dateiprüfung und L37-Metadatenprüfung | Ausgewählter INT8-Encoder wird tatsächlich von ORT geladen. |
| `DECODER_PATH` | leer → `MODEL_DIR/decoder.onnx` | optional; kein NUL; Dateiprüfung, ORT lädt Graph | Pfad des RNN-T-Predictors. |
| `JOINER_PATH` | leer → `MODEL_DIR/joiner.onnx` | optional; kein NUL; Dateiprüfung, ORT lädt Graph | Pfad des Joint Networks. |
| `TOKENS_PATH` | leer → `MODEL_DIR/tokens.txt` | optional; kein NUL; Dateiprüfung, sherpa lädt Tokenliste | Zum Export gehörende Tokenliste. |
| `THREADS` | `2` | 1, 2 oder 4 | ORT-Threads pro Sessionkonfiguration; kein hartes Gesamtprozess-Threadlimit. Alter Name bleibt erhalten. |
| `MAX_AUDIO_SECONDS` | `120` | 1–120 | Obergrenze der Samples je Erkennungsanfrage und Bestandteil der Sitzungsfrist. Überschreitung verwirft den Stream. |
| `MAX_AUDIO_CHUNK_BYTES` | `320000` | gerade Zahl, 640–320000 | Maximale binäre Payload je eingehendem Frame; Ablehnung anhand der Headerlänge **vor** Payload-Allokation. Default entspricht maximal 10 s PCM16/16 kHz/Mono pro Frame. Kürzere Chunks sind erlaubt. |
| `MAX_CONNECTIONS` | `8` | 1–32 | Anzahl Verbindungsthreads/Sitzungen; Inferenzqueue höchstens doppelt so groß. Native Inferenz bleibt serialisiert. |
| `CLIENT_TIMEOUT_SECONDS` | `30` | 1–300 | Absolute Frist für vollständigen Frame, Socket-Schreibtimeout; Gesamtfrist aktiver Sitzung zusätzlich maximale Audiodauer. |
| `INFERENCE_CHUNK_MS` | `20` | 10–560 | Maximalgröße der Teilstücke bei nativer Audiozuführung: Wert × 16 Samples, Decode-Drain nach jedem Teilstück. Teilt größere eingehende Chunks auf, sammelt kleine Chunks **nicht** bis zur Zielgröße. Kein Pacing/Sleep, kein neuer Modellkontext. |
| `LOG_LEVEL` | `info` | `error`, `warn`, `warning`, `info`, `debug`, Groß-/Kleinschreibung erlaubt | Filtert Rust-Serverlogs: error = nur fatale Fehler; warn zusätzlich Clientfehler; info zusätzlich Bereitschaft/Shutdown; debug zusätzlich Ereignistyp und Payloadlänge, niemals rohe Audioinhalte. Native sherpa-/ORT-Fehlerausgaben sind separat und bleiben sichtbar. |
| `LOG_TRANSCRIPTS` | `false` | exakt `true` oder `false` | Opt-in für finale erkannte Texte in Rust-Logs, nur bei info/debug. JSON-kodiert; auch Steuerzeichen werden escaped. Enthält eventuell persönliche Inhalte. |

Pfadauflösung: Absolute Einzelpfade werden unverändert verwendet. Relative Einzelpfade beziehen sich auf `MODEL_DIR`. Alle vier Dateien müssen zum selben geprüften Unified-L37-Export gehören. Metadatencheck, native Erstellung und bestehende CLI-Diagnose verwenden dieselbe Pfadauflösung; keine Rückkehr zu fest eingebauten Dateinamen nach der Vorprüfung.

Keine zusätzliche Pflichtkonfiguration: mit dem normalen Modellmount funktionieren die bisherigen Defaults unverändert. Die ursprünglichen Variablen bleiben kompatibel. Die Bind-Adresse wird nun vor dem Modellladen validiert; IPv6 wird korrekt mit Port geklammert. CLI `--model`, `--threads`, `--bind` überschreibt weiterhin die entsprechenden Werte, explizite Einzelpfade behalten Vorrang. Für den Docker-Healthcheck die Listenadresse über die Variablen setzen statt nur per `--bind`.

## Docker/Compose und Unraid

./docker-compose.yml reicht alle 17 Dienstvariablen weiter. Containerport und Portabbildung verwenden denselben `WYOMING_PORT`. In ./.env.example sowie config/unraid.env.example sind alle Werte mit deutschen Hinweisen vorhanden. config/unraid-template.xml zeigt alle Dienstvariablen unter „always“ mit deutschen Namen/Beschreibungen; Variablen sind nicht unnötig als Pflichtfelder markiert.

Compose-Hilfswerte, die **nicht** vom Rust-Prozess gelesen werden:

| Compose-Wert | Standard | Wirkung |
|---|---|---|
| `IMAGE` | `nemotron-unified-rust-wyoming:1.0.0` | lokales Image-Tag; nicht öffentlich veröffentlicht |
| `MODEL_DIR` in Compose-./.env | bestehender absoluter Hostpfad aus ./.env.example | Aus Kompatibilitätsgründen dort Host-Bind-Mount-Quelle; Compose setzt den Containerwert `MODEL_DIR=/models`. Bei direktem Docker/Unraid ist MODEL_DIR der Containerpfad. |
| `PUBLISH_ADDRESS` | `0.0.0.0` | Hostadresse für Portveröffentlichung |
| `HOST_PORT` | `10310` | Hostport, unabhängig vom Container-Wyoming-Port |

In Unraid die TCP-Portabbildung manuell anpassen, wenn der **Container**port geändert wird: XML-DockerMan-Vorlagen können Port-Target nicht dynamisch aus einer Umgebungsvariablen berechnen. Der Standard 10300 bleibt voreingestellt. `WYOMING_HOST=127.0.0.1` eignet sich für isolierte Tests im gemeinsamen Netzwerknamespace, nicht für die normale Bridge-Erreichbarkeit aus Home Assistant. Einzelpfade sind immer Containerpfade, keine ungemappten Unraid-Hostpfade.

Technische, geerbte Variablen: `SHERPA_ONNX_LIB_DIR` (Standard `/opt/sherpa/lib`) bezeichnet den Herkunftsstempel der nativen Runtime; `LD_LIBRARY_PATH` ist die dynamische Loader-Suchliste. Beides bleibt wie in Phase5 im Image gesetzt, wird nicht als Nutzer-Tuningoption beworben. Änderungen können die native Identitäts-/Ladeprüfung absichtlich scheitern lassen. Docker-Speicher-/CPU-/PID-Grenzen sind Engine-Einstellungen, keine wirkungslosen Rust-Umgebungsvariablen.

## Backend-Fähigkeiten und bewusst fehlende Schalter

Geprüft wurden die tatsächliche Rust-/C-API und die Unified-Implementierung unter Commit `31ba0e438f8065189a8e5589d84dfd7faf516d3d`, nicht eine ältere sherpa-Releaseversion. [Rust-API](https://github.com/k2-fsa/sherpa-onnx/blob/31ba0e438f8065189a8e5589d84dfd7faf516d3d/sherpa-onnx/rust/sherpa-onnx/src/online_asr.rs), [Unified-Modellimplementierung](https://github.com/k2-fsa/sherpa-onnx/blob/31ba0e438f8065189a8e5589d84dfd7faf516d3d/sherpa-onnx/csrc/online-transducer-nemo-parakeet-unified-model.cc). Lokaler Auszug: docs/evidence/phase5_1/backend-api.txt.

- **L37-Kontext/Latenz:** links37, Chunk7, rechts7 sind Metadaten des konkreten ONNX-Exports. Keine Variablen für links/rechts/560-ms-Modelllatenz; ein anderer Kontext benötigt einen passenden neuen Export und erneute Validierung. INFERENCE_CHUNK_MS verändert nur die Rust→sherpa-Zuführung, nicht die 1,12 s algorithmische Latenz.
- **Endpointing:** sherpas allgemeine Online-API besitzt Endpointing-Regeln. Der vorhandene Server wertet `is_endpoint` jedoch nicht aus und finalisiert ausschließlich über Wyoming `audio-stop`. Daher kein ENABLE_ENDPOINTING, keine Silence-/Rule-Schwellwerte und keine interne VAD angeboten. Das ist eine fehlende Serverintegration, kein pauschales Fehlen in sherpa. Home Assistant bleibt für das Sprachende zuständig.
- **Teiltranskripte:** Native Sessions können Hypothesen zurückgeben. Wyoming-Transcript-Streaming ist hier weiterhin nicht integriert; `supports_transcript_streaming=false`. Keine wirkungslose STREAMING=true-Option. Frühe nichtleere Hypothesen sind für die kurze Referenzaufnahme nicht garantiert.
- **Geräte:** sherpa besitzt allgemein weitere Provider, das gepinnte und gebaute Runtime-Image ist jedoch nur für CPU vorbereitet/geprüft. Kein CUDA/TensorRT/OpenVINO/CoreML-Schalter. STT_DEVICE weist solche Werte klar ab.
- **Threads:** die verwendete sichere Anbindung stellt num_threads bereit, keine getrennten wirksamen ORT-inter-/intra-op-Tuningvariablen dieses Projekts. Keine erfundenen zusätzlichen Threadvariablen.
- **Weitere Sprachen, Resampling, Beam-Suche, Hotwords und automatische Quantisierung:** nicht als konfigurierbare Serverfunktionen integriert. Der Export ist multilingual; der Dienst bleibt bewusst Deutsch mit greedy search und vorhandenem INT8-Encoder.

## Orientierung an bestehenden STT-Projekten

Moonshine-Konfiguration unter `/mnt/nvme/appdata/codex-workspace/moonshine-stt-wyoming/config/defaults.env` und zugehörige Vorlagen wurden nur gelesen. Dort vorhandene Namen wie WYOMING_HOST/PORT, STT_DEVICE, MAX_AUDIO_SECONDS, LOG_LEVEL, LOG_TRANSCRIPTS, CLIENT_TIMEOUT_SECONDS und MAX_CONNECTIONS wurden übernommen bzw. beibehalten. Kroko wurde ausschließlich per read-only Docker-Inspect seiner Umgebungsvariablen geprüft (unter anderem HOST, PORT, NUM_THREADS, MODEL_DIR, LANGUAGE, LOG_LEVEL). Kein Container wurde dabei geändert und keine Tokens/Auth-Verzeichnisse wurden gelesen. Projektspezifische MOONSHINE_-/KROKO_-Variablen und Auto-Downloads werden nicht als wirkungslose Aliasse eingeführt.

## Tests und tatsächlicher Stand

- **Release-Build erfolgreich**, Rust 1.91.1, Cargo-Lockfile unverändert, Feature sherpa, 1m24s Release-Kompilierung. Docker-Build führt Formatprüfung, alle Tests und Clippy mit -D warnings aus.
- **32 automatisierte Tests bestanden, 0 fehlgeschlagen**. Davon 7 neue Konfigurationstests: Defaults, alle Overrides, verständliche Fehler je Variable, konfiguriertes Frame-Limit vor Allokation, Logging-/Transkript-Privatsphäre, ausgewählte Modellpfade und dokumentierte Parser-/Default-Parität. Dazu alle bisherigen Protokoll-, nativen Identitäts-, Interoperabilitäts-, TCP- und Shutdown-Tests.
- Compose gegen das offizielle JSON-Schema geprüft; XML/YAML geparst. Alle 17 Variablen in Compose, XML und ./.env.example vollständig, alle XML-Variablen sichtbar und optional. Der Host hat weiterhin kein Compose-Plugin: kein docker compose up/config als tatsächlich ausgeführt behauptet. Validator nur in isoliertem Prüfcontainer, keine Hostinstallation.
- **Echter Nichtstandard-Integrationstest erfolgreich**: Listener 127.0.0.1:10444, THREADS=1, MODEL_DIR=/intentionally-unused, alle vier echten Modelldateien ausschließlich über explizite absolute Pfade ausgewählt. INFERENCE_CHUNK_MS=80 bei eingehenden 160-ms-Chunks, MAX_AUDIO_CHUNK_BYTES=128000, MAX_AUDIO_SECONDS=2, LOG_LEVEL=debug und LOG_TRANSCRIPTS=true. Gesundheit und Transkripte über offizielle Python-Wyoming-Ereignisklassen geprüft. Keine Hostports veröffentlicht, Netzwerkmodus none, read-only/rootless, 4-GiB-RAM-Limit.
- Drei Anfragen am selben Socket lieferten jeweils **„Einsteigen bitte.“** aus der echten menschlichen 1,50025-s-Referenzaufnahme. Anfragezeiten: 1.095 s, 1.125 s, 1.124 s. Die kurze Aufnahme belegt Integration, keine allgemeine deutsche Befehlsqualität.
- Geändertes Payloadlimit zusätzlich mit deklarierten 128002 Byte **ohne Payload** geprüft: sofortiges gerahmtes error statt Warten auf Daten; Debug-Ereignislogs und echte Transkriptlogs im Serverlog nachgewiesen. Ungültiges Format, Sprache, odd PCM, Dauerlimit, aktive Abbrüche und wiederholte Verbindungen bleiben geprüft.
- Docker-Healthcheck **healthy**, direkter Healthcheck auf dem geänderten Port erfolgreich. SIGTERM mit offenem Teilheader und aktiver nativer Sitzung: Server Exit 0, Prüfclient Exit 0; shutdown complete. Alle eigenen Testcontainer danach entfernt. OOMKilled=false. Docker weist wie zuvor auf fehlende Swap-Limit-Unterstützung dieses Kernels hin; RAM-Limit ist gesetzt.
- Lokales Image **117.489.023 Byte / 112.05 MiB**, ID sha256:d685ed597b569474c6a6b469c38bddaa2560103a299abd9f18cbaca6274571a6. Nach bestandenem Test zeigen die lokalen Tags phase5.1 und 1.0.0 auf diesen Build; der vorherige Phase5-Build bleibt unter Tag phase5 erhalten. Keine Registry-Aktion, kein Containerersatz.

Reproduktion: Docker-Releasebuild nach ./Dockerfile; Nichtstandardtest mit sh scripts/test-configured-release.sh und vorhandenem Prüfimage nemotron-unified-checks:1.91. Konfigurationsschema-Prüfung: scripts/validate_configs.py im isolierten Python-Validierungscontainer. Rohbelege: docs/evidence/phase5_1/docker-build.log, docs/evidence/phase5_1/config-validation.log, docs/evidence/phase5_1/real-server.json, docs/evidence/phase5_1/server.log, docs/evidence/phase5_1/image-inspect.json und docs/evidence/phase5_1/signal-client.json.

Der bisherige Phase5-Bericht bleibt historisch unter docs/PHASE5.md erhalten. Kein Home-Assistant-/Satellite-Abnahmetest und keine öffentliche Registry-Veröffentlichung in Phase5.1. Modellgewichte bleiben unverändert; kein neuer Download. Eigene isolierte Prüfcontainer werden nach Tests entfernt.
