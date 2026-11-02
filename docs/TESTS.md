# Tests

Aktueller Ergebnisbericht: docs/PHASE5.md. Historische Phase4-Inferenz: docs/PHASE4_RESULTS.md. Reine Protokollfixtures sind ausdrücklich keine Spracherkennung.

```sh
cd /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming
sh scripts/check.sh
```

./Dockerfile baut im Buildstage mit Rust1.91.1 und festem ./Cargo.lock; prüft `cargo fmt --check`, `cargo test --locked --features sherpa` und `cargo clippy --locked --all-targets --features sherpa -- -D warnings`. Einschließlich tatsächlicher nativer SHA-/Versionsprüfung, JSONL-/Payload-Grenzen, exakter PCM-Daten, Python/Rust-Codec-Interoperabilität, offizieller typisierter Info-/Fehlerantworten, mehrfacher TCP-Anfragen, paralleler Beschreibung, Sitzungsfreigabe, Timeouts, Verbindungs-/Audio-/Dateigrenzen und geordnetem Shutdown.

tests/reference enthält unveränderte MIT-Module aus dem tatsächlich geprüften offiziellen Wyoming-Commit; Python wird nur im Build/Test benötigt. Tests laden keine Gewichte und benötigen keine produktiven Container/Ports. Ohne `sherpa` testet Cargo Protokoll und Infrastruktur, stellt aber keine echte Inferenz bereit; Releasebuild immer mit Feature `sherpa`.

Der bevorzugte isolierte Modell-/Signaltest ist `sh scripts/test-release.sh`. Er benötigt das vorhandene Prüfimage `nemotron-unified-checks:1.91`; auf einem frischen System vorher mit `docker build --target checks -t nemotron-unified-checks:1.91 .` lokal bauen. Das Skript setzt die erforderliche Testkonfiguration selbst und räumt seine Container auf.

Der echte opt-in Integrationstest tests/real_server.py spricht TCP mit offiziellen Wyoming-Ereignisklassen und einem bereits gestarteten isolierten Testserver. Sein Testserver muss für den Dauergrenztest ausdrücklich `MAX_AUDIO_SECONDS=2` verwenden; ein normal konfigurierter produktiver Server ist kein geeignetes Testziel. Er benötigt die echte WAV-Aufnahme und schreibt die **empfangenen** Texte samt Anfragezeit in eine Ergebnisdatei. Kein künstliches Erfolgsresultat. Beispiel im Entwicklungscontainer, nachdem ein Testserver im selben Netzwerk ausdrücklich gestartet wurde:

```sh
PYTHONPATH=tests/reference python3 tests/real_server.py \
  --host 127.0.0.1 --port 10300 \
  --wav benchmarks/audio/einsteigen-bitte.wav \
  --output docs/evidence/phase5/real-server.json
```

Dieser Pythonaufruf gehört in einen isolierten Container, nicht auf den Unraid-Host. Das Runtime-Image enthält keinen Pythoninterpreter. Details des tatsächlich ausgeführten isolierten Docker-Tests und der Signalprüfung stehen in docs/PHASE5.md. Die gemessene Anfrage-RTF umfasst TCP/Client/Server; sie ist nicht identisch mit den reinen CLI-Inferenzwerten aus Phase4.

Vor Veröffentlichung zusätzlich manuell: Home-Assistant-Integration mit echtem Mikrofon/Satellite, längere deutsche Befehle, Hintergrundgeräusche, VAD-Ende, Neustart/Wiederverbindung, längerer Betrieb und RAM-Verhalten bei mehreren langen Streams. Ohne diese Tests keine Behauptung eines abgenommenen produktiven Betriebs.

Phase5.1 ergänzt tests/configuration.rs mit Parser-/Default-/Grenzwert-/Pfad-/Logging-/Datenschutz-/Variablenparitätstests. Der isolierte Nichtstandard-Konfigurationstest ist `sh scripts/test-configured-release.sh` (Image standardmäßig `nemotron-unified-rust-wyoming:phase5.1`). Er prüft Port10444, Loopback, vier explizite Modellpfade, 1 Thread, native 80-ms-Zuführung aus 160-ms-Netzwerkchunks, ein angepasstes Payloadlimit, Debug-/Transkriptlogs, echte deutsche Inferenz und Shutdown. Ergebnisse separat unter docs/evidence/phase5_1; historische Phase5-Nachweise bleiben erhalten. Keine Hostports werden veröffentlicht.

Phase5.2 ergänzt den tatsächlichen Docker-Identitätstest scripts/test-identity.sh. Er prüft UID/GID und Capabilities von PID1, Default99:100, andere ausschließlich per Umgebung gewählte IDs, den vollständig unprivilegierten Modus, ungültige IDs, einen unzugänglichen Modellpfad, echte deutsche Inferenz sowie Shutdown. Verwendet ausschließlich separate Container ohne Hostports. Der erweiterte Konfigurations-/Signaltest lässt seine Ergebnisdateien über TEST_RESULTS_DIR getrennt ablegen; Beispiel: IMAGE=nemotron-unified-rust-wyoming:phase5.2 CLIENT_IMAGE=nemotron-unified-checks:phase5.2 TEST_RESULTS_DIR=docs/evidence/phase5_2/configured sh scripts/test-configured-release.sh. Alle bisherigen17 Rust-Variablen bleiben geprüft; PUID/PGID werden bewusst durch den Entrypoint und separate Docker-Tests validiert.

## Phase 6

Aktuelle Ergebnisse: docs/PHASE6.md. Isolierter Build mit `docker build --platform linux/amd64 --target runtime -t nemotron-unified-rust-wyoming:phase6-verified .`; explizite Rust-Prüfungen im build-Stage-Image. Integration über scripts/test-identity.sh, scripts/test-configured-release.sh und scripts/runtime-preflight-tests.sh mit IMAGE auf den geprüften Tag. TEST_RESULTS_DIR trennt neue Prüfergebnisse von historischen Belegen. Keine Hostports und keine Änderungen an Bestandscontainern. Konfiguration prüft scripts/validate_configs.py (Compose-Schema, XML, alle 19 Variablen, Workflows und ausschließlich Low-Q als Icon).
