# Tests

Aktueller Ergebnisbericht: docs/PHASE5.md. Historische Phase4-Inferenz: docs/PHASE4_RESULTS.md. Reine Protokollfixtures sind ausdrücklich keine Spracherkennung.

```sh
cd /mnt/nvme/appdata/codex-workspace/nemotron-unified-wyoming
sh scripts/check.sh
```

./Dockerfile baut im Buildstage mit Rust1.91.1 und festem ./Cargo.lock; prüft `cargo fmt --check`, `cargo test --locked --features sherpa` und `cargo clippy --locked --all-targets --features sherpa -- -D warnings`. Einschließlich tatsächlicher nativer SHA-/Versionsprüfung, JSONL-/Payload-Grenzen, exakter PCM-Daten, Python/Rust-Codec-Interoperabilität, offizieller typisierter Info-/Fehlerantworten, mehrfacher TCP-Anfragen, paralleler Beschreibung, Sitzungsfreigabe, Timeouts, Verbindungs-/Audio-/Dateigrenzen und geordnetem Shutdown.

tests/reference enthält unveränderte MIT-Module aus dem tatsächlich geprüften offiziellen Wyoming-Commit; Seit Phase 11 verwendet auch die Containerinitialisierung Python; die eigentliche Inferenz bleibt Rust/native. Tests laden keine Gewichte und benötigen keine produktiven Container/Ports. Ohne `sherpa` testet Cargo Protokoll und Infrastruktur, stellt aber keine echte Inferenz bereit; Releasebuild immer mit Feature `sherpa`.

Der bevorzugte isolierte Modell-/Signaltest ist `sh scripts/test-release.sh`. Er benötigt das vorhandene Prüfimage `nemotron-unified-checks:1.91`; auf einem frischen System vorher mit `docker build --target checks -t nemotron-unified-checks:1.91 .` lokal bauen. Das Skript setzt die erforderliche Testkonfiguration selbst und räumt seine Container auf.

Der echte opt-in Integrationstest tests/real_server.py spricht TCP mit offiziellen Wyoming-Ereignisklassen und einem bereits gestarteten isolierten Testserver. Sein Testserver muss für den Dauergrenztest ausdrücklich `MAX_AUDIO_SECONDS=2` verwenden; ein normal konfigurierter produktiver Server ist kein geeignetes Testziel. Er benötigt die echte WAV-Aufnahme und schreibt die **empfangenen** Texte samt Anfragezeit in eine Ergebnisdatei. Kein künstliches Erfolgsresultat. Beispiel im Entwicklungscontainer, nachdem ein Testserver im selben Netzwerk ausdrücklich gestartet wurde:

```sh
PYTHONPATH=tests/reference python3 tests/real_server.py \
  --host 127.0.0.1 --port 10300 \
  --wav benchmarks/audio/einsteigen-bitte.wav \
  --output docs/evidence/phase5/real-server.json
```

Dieser Pythonaufruf gehört in einen isolierten Container, nicht auf den Unraid-Host. Das Runtime-Image enthält seit Phase 11 Python für die Modellinitialisierung. Details des tatsächlich ausgeführten isolierten Docker-Tests und der Signalprüfung stehen in docs/PHASE5.md. Die gemessene Anfrage-RTF umfasst TCP/Client/Server; sie ist nicht identisch mit den reinen CLI-Inferenzwerten aus Phase4.

Vor Veröffentlichung zusätzlich manuell: Home-Assistant-Integration mit echtem Mikrofon/Satellite, längere deutsche Befehle, Hintergrundgeräusche, VAD-Ende, Neustart/Wiederverbindung, längerer Betrieb und RAM-Verhalten bei mehreren langen Streams. Ohne diese Tests keine Behauptung eines abgenommenen produktiven Betriebs.

Phase5.1 ergänzt tests/configuration.rs mit Parser-/Default-/Grenzwert-/Pfad-/Logging-/Datenschutz-/Variablenparitätstests. Der isolierte Nichtstandard-Konfigurationstest ist `sh scripts/test-configured-release.sh` (Image über IMAGE wählbar, aktuell standardmäßig `ghcr.io/marco-taylor/nemotron-unified-wyoming:latest`). Er prüft Port10444, Loopback, vier explizite Modellpfade, 1 Thread, native 80-ms-Zuführung aus 160-ms-Netzwerkchunks, ein angepasstes Payloadlimit, Debug-/Transkriptlogs, echte deutsche Inferenz und Shutdown. Ergebnisse separat unter docs/evidence/phase5_1; historische Phase5-Nachweise bleiben erhalten. Keine Hostports werden veröffentlicht.

Phase5.2 ergänzt den tatsächlichen Docker-Identitätstest scripts/test-identity.sh. Er prüft UID/GID und Capabilities von PID1, Default99:100, andere ausschließlich per Umgebung gewählte IDs, den vollständig unprivilegierten Modus, ungültige IDs, einen unzugänglichen Modellpfad, echte deutsche Inferenz sowie Shutdown. Verwendet ausschließlich separate Container ohne Hostports. Der erweiterte Konfigurations-/Signaltest lässt seine Ergebnisdateien über TEST_RESULTS_DIR getrennt ablegen; Beispiel: IMAGE=nemotron-unified-wyoming:phase5.2 CLIENT_IMAGE=nemotron-unified-checks:phase5.2 TEST_RESULTS_DIR=docs/evidence/phase5_2/configured sh scripts/test-configured-release.sh. Alle bisherigen17 Rust-Variablen bleiben geprüft; PUID/PGID werden bewusst durch den Entrypoint und separate Docker-Tests validiert.

## Phase 6

Aktuelle Ergebnisse: docs/PHASE6.md. Isolierter Build mit `docker build --platform linux/amd64 --target runtime -t nemotron-unified-wyoming:local-check .`; explizite Rust-Prüfungen im build-Stage-Image. Integration über scripts/test-identity.sh, scripts/test-configured-release.sh und scripts/runtime-preflight-tests.sh mit IMAGE auf den geprüften Tag. TEST_RESULTS_DIR trennt neue Prüfergebnisse von historischen Belegen. Keine Hostports und keine Änderungen an Bestandscontainern. Konfiguration prüft scripts/validate_configs.py (Compose-Schema, XML, alle 19 Variablen, Workflows und ausschließlich Low-Q als Icon).

## Lokale Phase-10-Templateprüfung

Aktueller lokaler Bericht: docs/PHASE10_UNRAID_TEMPLATE.md. Die XML-Prüfung in scripts/validate_configs.py erwartet drei normale Config-Einträge, sieben erweiterte Variablen und elf ausgelassene Defaults. Die vollständige 19er-Parität bleibt für Compose, Beispiele und die Referenzliste erhalten; XML-Sichtbarkeit wird separat geprüft.

Auf Unraid lässt sich die tatsächlich installierte Parser-/Command-Erzeugung rein lesend prüfen:

```sh
xmllint --noout config/unraid-template.xml
php -d auto_prepend_file= -d short_open_tag=1 tests/unraid_template.php config/unraid-template.xml
```

Der PHP-Test führt die erzeugten Docker-Befehle **nicht** aus und ruft `xmlToCommand` mit `create_paths=false` auf. Das deaktivierte Auto-Prepend verhindert Unraids sonstige Änderung des Arbeitsverzeichnisses. Keine eigenen Benutzervorlagen werden gelesen oder geschrieben.

Echte Inferenz-/Port-/Berechtigungstests laufen ausschließlich mit eigenen Containern und freien Loopback-Hostports:

```sh
TEST_MODE=minimal TEST_RESULTS_DIR=docs/evidence/phase10/minimal sh scripts/test-unraid-minimal.sh
TEST_MODE=template TEST_RESULTS_DIR=docs/evidence/phase10/template sh scripts/test-unraid-minimal.sh
TEST_MODE=legacy TEST_RESULTS_DIR=docs/evidence/phase10/legacy sh scripts/test-unraid-minimal.sh
```

`minimal` setzt keine Variablen explizit. `template` setzt die acht verbliebenen Variablen mit ihren XML-Defaults. `legacy` setzt alle 19 bisherigen Variablen mit abweichenden Modellpfaden, Port 10444, UID/GID 12345:23456, Audiolimits und nativer 80-ms-Zuführung aus 160-ms-Netzwerkpaketen. Alle Modi prüfen drei echte deutsche Transkriptionen sowie Healthcheck, Netzwerkweg, Payloadgrenze und Shutdown. Tests/Client: tests/unraid_minimal.py verwendet die mitgelieferte offizielle Wyoming-Eventkodierung ohne die unter Python 3.14 entfallene Audio-Konvertierungsbibliothek.

`IMAGE` wählt ein bereits vorhandenes Runtime-Image. `CLIENT_IMAGE` wählt ein bereits vorhandenes Image mit Python 3; auf diesem Host wurde das vorhandene `ghcr.io/esphome/esphome:stable` ausschließlich als isolierter Testinterpreter benutzt. Bestehende ESPHome-Container oder Projekte werden nicht verwendet. Beide Images werden mit `--pull never` gestartet; kein neuer Build/Tag/Push. Modellgewichte sind immer read-only. Die komplette Schema-Prüfung benötigt zusätzlich die in .github/workflows/ci.yml gepinnten Python-Testpakete. Im Phase-10-Lauf wurden sie ausschließlich in einem temporären Containerdateisystem bereitgestellt.
# Phase-11-Ergänzung

scripts/model-init.py wird mit `python3 -m unittest discover -s tests -p model_init_test.py -v` getestet; kleine Transport-Fixtures sind keine Modellgewichte. Die Tests prüfen gezielte Downloads, Wiederverwendung, Hashfehler, Sicherung beschädigter Dateien, Unterbrechung, Konkurrenz, HTTPS-Regeln, Netzwerk-/Platzfehler und den vererbten seccomp-Schreibschutz. Der Docker-Build führt diese Tests zusätzlich zu den bestehenden Rust-Prüfungen aus. Runtime-Nachweise und die noch blockierte echte leere Erstinstallation stehen in docs/PHASE11_RENAME_AND_MODEL_DOWNLOAD.md.
