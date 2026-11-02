# Phase 3 – Rust-Build, Wyoming und echter Inferenztest vorbereitet

Stand: 31.10.2026. Projektwurzel:
/mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming.
Alle relativen Dateipfade in diesem Dokument beziehen sich auf diese Wurzel.

## Umfang und Status

Rust-Code, Protokolltests, CPU-Backend-Anbindung, Docker-Build und Benchmark-
Runner sind implementiert. Es wurden keine Modellgewichte geladen und keine
Nemotron-Erkennung oder Qualitäts-/Geschwindigkeitsmessung behauptet. Der
nächste echte Inferenzlauf bleibt durch fehlende freigegebene ONNX-Dateien
blockiert. Kein produktiver Containerstart, keine Ports für einen Dienst
veröffentlicht, keine Home-Assistant-Änderung, kein GitHub-/GHCR-Publish.

## Abschließender Buildstatus

| Prüfung | Ergebnis |
|---|---|
| Nativer PR-Build | Erfolgreich, CPU-ONNX-Runtime 1.28.2 |
| Rust Release mit Feature sherpa | Erfolgreich, native Bibliothek verlinkt |
| Tests mit Feature sherpa | **15 bestanden**, 0 fehlgeschlagen, 0 ignoriert |
| Clippy, alle Targets, Warnungen als Fehler | Erfolgreich |
| cargo fmt --check | Erfolgreich |
| Finales Image --help | Exit 0, ausgeführt ohne Netzwerk/Ports |
| Serveraufruf ohne Modelle | Erwartet Exit 2; kein Listener, kein Transkript |
| Echter Nemotron-WAV-Test | Nicht ausgeführt: kein freigegebenes Modell |

Finales lokales Image: `nemotron-unified-rust-wyoming:phase3`, ID
`sha256:f1e1794f5c7227cfc5acd121d7632b8263201493f6cae2bdc31123cf99b18dbd`, 116382563 Byte.
Der Release-Build wurde in ca. 1 min 34 s abgeschlossen; der native Erstbuild
brauchte ca. 8 min 38 s, anschließend reiner Versionspatch/Relink. Das sind
Buildzeiten, keine Inferenzmessungen. Das Image läuft als UID/GID 65534.
Aus dem geprüften Image wurde derselbe Rust-Binary nach
./target/release/nemotron-unified-rust-wyoming kopiert. Hash:
./docs/evidence/release-binary.sha256. Er benötigt die Image-Bibliotheken und
ist kein eigenständig auf dem Unraid-Host getestetes statisches Binary.

Protokolle: ./docs/evidence/docker-release-build.log,
./docs/evidence/native-runtime-version.json, ./docs/evidence/format-final.log,
./docs/evidence/release-help.log, ./docs/evidence/release-no-model.log.
Die CLI-Smoke-Container wurden jeweils mit `--rm --network none` ausgeführt
und sind beendet. Kein Projektcontainer bleibt als Dienst aktiv.

## Tatsächlich verwendeter Upstream

[PR #4141](https://github.com/k2-fsa/sherpa-onnx/pull/4141) ist bei erneuter
GitHub-API-Prüfung offen und nicht gemergt. Verwendet wird exakt
`31ba0e438f8065189a8e5589d84dfd7faf516d3d`, einschließlich der darin gestapelten
Streamingkorrekturen. Der separat offene [PR #4133](https://github.com/k2-fsa/sherpa-onnx/pull/4133)
hat inzwischen einen anderen Head; dieser wird nicht stillschweigend darüber
gelegt. Ein späteres Upstream-Update erfordert neue Build-/Korrektheitstests.
Metadaten, Status und Exporter sind in ./docs/evidence/phase3-model-availability.json,
./docs/evidence/phase3-export-onnx.py und ./docs/evidence/phase3-export-readme.md
festgehalten. Die Exportquellen wurden gelesen, nicht ausgeführt.

Der geprüfte Exporter integriert die Sprachprojektion in den Encoder,
übergibt `prompt_index` als int64 und legt das Sprachwörterbuch in ONNX-Metadaten
ab. L37 hat 37 Encoderframes links (2,96 s), sieben Chunkframes (0,56 s)
und sieben Rechtskontextframes (0,56 s), insgesamt 1,12 s algorithmische Latenz.
Encoder-MatMul-Gewichte werden per-channel QUInt8 quantisiert; Prompt, Predictor
und Joiner bleiben FP32. Es ist **partielles INT8**.

Die C-API stellt Streamoptionen und die sicheren Rust-Wrapper stellen
`OnlineStream::set_option`, `accept_waveform`, `input_finished`, `is_ready`,
`decode` und `get_result` bereit. Die Anbindung nutzt diese bestehende
Implementierung; kein eigener RNN-T-Decoder. Quellprüfungen:
./docs/evidence/pr-c-api.h, ./docs/evidence/pr-rust-online-asr.rs und
./docs/evidence/pr-sys-build.rs. sherpa-Code steht unter Apache-2.0;
Originaltext in ./docs/evidence/sherpa-LICENSE.
Ausführliche Laufhistorie einschließlich anfänglicher Fehler: ./docs/TESTS.md.

## Buildumgebung und Reproduzierbarkeit

Alle Compiler, Cargo, CMake, Python und Zusatzwerkzeuge laufen in Docker.
Der Unraid-Host erhielt keine Pakete. Basis ist Rust 1.91.1 / Debian Bookworm,
Image-Digest in ./Dockerfile festgelegt. Das native C/C++-Backend wird aus dem
PR-Commit gebaut; GPU, PortAudio, Websocket, Python-Binding, TTS und Diarization
sind deaktiviert. ONNX Runtime 1.28.2 wird durch den Upstream-Build als
CPU-Bibliothek bezogen. Das sind Build-/Runtime-Abhängigkeiten, keine
Modellgewichte. Native Kompilierung: zwei Jobs.

./Cargo.lock fixiert Rust-Abhängigkeiten einschließlich Git-Revision. Die
Rust-Crate verwendet `shared`, ohne automatische Release-Prebuilts:
`SHERPA_ONNX_LIB_DIR=/opt/sherpa/lib` zeigt auf den eigenen nativen Build.
Beim Laden werden sowohl die Git-SHA der tatsächlich geladenen Bibliothek als
auch deren ./SOURCE_COMMIT in diesem Bibliotheksverzeichnis geprüft. Somit
wird keine ältere sherpa-Releasebibliothek als Unified-Runtime ausgegeben.

Dabei wurde ein Upstream-Metadatenfehler entdeckt: ./sherpa-onnx/csrc/version.cc
im geprüften Commit enthält die veraltete feste SHA `96255a1b`, obwohl CMake
und Git den PR-Commit korrekt erkennen. Der erste native Identitätstest hat
deshalb absichtlich den Build abgebrochen; Protokoll unter
./docs/evidence/docker-release-first-native-identity-failure.log. Der Buildschritt
`stamped` korrigiert ausschließlich SHA-/Datums-Stringliterale dieser
Versionsauskunft anhand des verifizierten Git-Checkouts und linkt neu.
./scripts/stamp_native_version.py prüft vor dem Patch die erwarteten alten
Literale. Keine Änderung an Encoder, Sprach-Prompt, Decoding oder Streaming.
Die lokale Abweichung ist im Image unter `/opt/sherpa/lib/SOURCE_PATCH`
festgehalten. Der Test wird mit diesem Build erneut ausgeführt.

Buildbefehle aus der Projektwurzel:

```sh
sh scripts/check.sh
docker build --target development -t nemotron-unified-development:pr4141 .
docker build -t nemotron-unified-rust-wyoming:phase3 .
```

Der finale Docker-Build enthält `cargo build --locked --release --features sherpa`,
`cargo test --locked --features sherpa` und Clippy. Modelle sind weder im
Buildkontext noch im Image. Verwendete native Downloadrevisionen stehen im
CMake-Protokoll. Die Debian-Paketquellen und transitiven Downloadserver sind
nicht als vollständiger Offline-Snapshot gespiegelt; identischer Source-Commit
und Lockfile allein garantieren deshalb keine bitidentischen Image-Bytes.

## Wyoming-Implementierung und Tests

./src/wyoming.rs implementiert Wire-Framing gemäß der
[offiziellen Wyoming-Referenz](https://github.com/OHF-Voice/wyoming):
JSONL-Header, optionaler externer JSON-Datenblock, anschließend exakt angegebene
Binärpayload. Externe Daten überschreiben gleichnamige Inline-Felder.
Limits: 16 KiB Header, 64 KiB Daten, 320.000 Byte PCM pro Event, 120 s pro
Äußerung; Socket-Lese-/Schreibtimeout 30 s. Verarbeitet werden describe/info,
transcribe, audio-start/chunk/stop sowie transcript/error. Server bearbeitet
Clients sequentiell; keine implizite Mehrbenutzer-Leistungszusage.

Audio: 16 kHz mono signed PCM16 little endian; andere Formate werden mit
Protokollfehler abgelehnt. Falsche Reihenfolge und unvollständige Samples
liefern error. Nach Framingfehler wird die Verbindung beendet. Erfolgreiche
Transkripte stammen ausschließlich aus `RecognitionSession::finish`. Es gibt
kein Produktions-Mock und keinen Dummy-Fallback. Ohne Modell/Backend startet
der CLI-Server nicht. Testdoubles sind ausschließlich unter ./tests/protocol.rs
vorhanden und geben ausdrücklich „PROTOCOL FIXTURE – keine Erkennung“ aus.

Die Tests validieren:

- Roundtrips für Transcribe, AudioStart, AudioChunk, AudioStop und Transcript,
  einschließlich Unicode sowie binärer Newlines und signed PCM-Randwerten.
- Ein-Byte-Teilreads, aufeinanderfolgende Frames und externe JSON-Datenblöcke.
- Beschädigte Header, negative/zu große Längen, abgeschnittene Daten/Payloads,
  falsches Audioformat, fehlende Ereignisse und Fehler-Rücksetzung.
- Verbindung über echtes TCP auf einem zufälligen Loopback-Port **innerhalb des
  kurzlebigen Testcontainers**; dabei kein ASR-Modell und keine Host-Portfreigabe.
- Bidirektionalen Austausch mit dem unveränderten offiziellen Python-Wyoming-
  Codec, Commit `08a0c258df83fea6e1643bcfe67e86243f01cf31`, unter
  ./tests/reference/wyoming/event.py. Die lokale Paketmetadaten-Fixture dient
  nur dessen Versionsimport; Original-MIT-Lizenz liegt unter
  ./tests/reference/LICENSE.md. Das ist Protokollvalidierung, kein STT-Test.
- ONNX-Metadatenparser mit übersprungenen Graphbytes, Überlauf-/Trunkierungs-
  ablehnung sowie L37-/Deutschvertrag; diese winzigen Metadaten-Fixtures sind
  keine neuronalen Testmodelle.
- Deutschen WER-Scorer und leere Referenzen.

Der Server sendet zunächst ausschließlich das finale `transcript`. Partiell
verfügbare Hypothesen werden vom direkten Benchmark beobachtet. Wyoming-
`transcript-start/chunk/stop` sind noch nicht implementiert und werden nicht
als unterstützte Ausgabe beworben. HA-End-to-End-Kompatibilität wurde nicht
getestet.

## Inferenzschnittstelle und Grenzen

./src/inference.rs trennt Backend-Erzeugung von Sitzungen. Native Recognition-
Objekte bleiben über `Rc` am Leben; Streams werden vor dem letzten Recognizer-
Owner freigegeben und nie zwischen Clients geteilt. Das Projekt verwendet
keinen eigenen unsafe-FFI-Code, sondern den vorhandenen sherpa-Wrapper.
Deutsche Sprachoption wird vor dem ersten Audio gesetzt. PCM wird mit
`sample/32768` in Float gewandelt; DSP, Tokenizer und Decoding bleiben beim
modellkundigen nativen Unified-Pfad. Endpunktdetektion ist deaktiviert,
`audio-stop` bestimmt das Ende. EOF wird mit `input_finished` ohne erfundene
Stille geflusht. Für jede Äußerung wird ein neuer Stream erstellt.

Vor dem Laden prüft ./src/model.rs die tatsächlichen Encoder-Metadaten:
Unified buffered Streaming, L37, sieben Chunk-/Rechtsframes und vorhandener
`de`-Prompt. Der Parser liest nur Top-Level-Protobuf-Metadaten und überspringt
den großen Graph. Diese Prüfung ist kein vollständiger ONNX-Graphchecker,
keine Quantisierungsanalyse und keine kryptografische Herkunftsgarantie.
Modellhashes müssen nach einem freigegebenen Bezug zusätzlich gegen die Quelle
geprüft werden. Die native Bibliothek kann bei ungültigen Graphen fatal abbrechen;
wohlgeformte Metadaten allein garantieren keine ausführbaren Modelle.

## Verfügbarkeit der Modelle

Nur API-Metadaten wurden geladen. Reproduzierbare Abfrage:
./scripts/probe_models.py, Ergebnis ./docs/evidence/phase3-model-availability.json.

| Quelle | Verifiziertes Ergebnis |
|---|---|
| NVIDIA offizielles Repository | NeMo-Archiv, kein ONNX-Paket |
| sherpa asr-models Release | 498 gelistete Assets, kein passendes Nemotron-Labs-Unified-Paket |
| Release-Tags asr-models-2/-3 | API liefert 404 |
| Vom PR-Workflow vorgesehenes HF-L37-Repository | API liefert 401; öffentliches Downloadpaket nicht bestätigt |
| FluidInference | CoreML/CoreAI-Konvertierung, kein passendes ONNX-L37-Paket |
| loom-ai-org | GGUF-Dateien, kein sherpa-ONNX-L37-Paket |

Ein HTTP 401 beweist nicht die Nichtexistenz eines privaten Repositorys. Die
Abfragen beweisen auch nicht, dass weltweit kein weiteres Community-Paket
existiert. Es steht hier **kein verifiziertes öffentliches fertiges L37-Paket**
für den ersten Test bereit. Das PR-Workflow-Skript enthält Veröffentlichungs-
logik; daraus darf keine tatsächlich erfolgte Veröffentlichung abgeleitet werden.

Falls eigener Export nötig wird: offizielles NeMo-Archiv bei Revision
`023ce907267a09a308a5cb69239447cb3d0c1597`, 2.507.735.040 Byte
(ca. 2,34 GiB), SHA256
`1718cc1b44fb8597b2356328d706a8d89f31c389ca6f2256c2e3f743c0246936`.
Dazu kämen die vorher zu prüfenden NeMo/PyTorch-/ONNX-Abhängigkeiten und
zusätzlicher Exportplatz. Keine davon wurde für den Export installiert oder
als Modell heruntergeladen. Gewichte/konvertierte Gewichte unterliegen
OpenMDW 1.1; bei Weitergabe Lizenz und anwendbare Herkunftshinweise mitführen.

## Reproduzierbarer N100-Benchmark

./scripts/benchmark.py ruft den echten Rust-Backend-Benchmark auf und verweigert
./benchmarks/manifest.example.jsonl als bloßes Schema-Beispiel. Ein echter Korpus
benötigt pro WAV einen SHA256, ID und unveränderliche deutsche Referenz.
Audio ist für alle verglichenen Systeme identisch. Eingabedauer 80 ms bis
120 s. Manifestpfade dürfen das Korpusverzeichnis nicht verlassen.

Matrix: Threads 1/2/4, jeweils Compute-Lauf ohne Echtzeitpausen und Lauf mit
Echtzeit-Pacing. Pro Konfiguration/Datei drei Wiederholungen, rotierende
Threadreihenfolge. Jeder Prozess lädt das Modell, wärmt mit einer ungemessenen
Äußerung auf und verwendet einen neuen Stream für die Messung. Modellladezeit
wird getrennt erfasst. Das Verfahren misst geladene Erkennung, keinen dauerhaft
warm gehaltenen Dienst. Chunk-Zuführung: identische 160-ms-PCM-Pakete.

JSONL enthält echte Hypothese, Referenz, Wortfehlerzahl, Referenzwortzahl,
WER, False-positive bei Stille, WAV-/Modellhashes, Commit, Kontext und Threads.
RTF zählt `push_pcm` plus EOF-Decoding geteilt durch Audiodauer, ohne absichtliche
Pacingpausen. Erste nichtleere Hypothese ab Start bleibt `null`, wenn vor EOF
keine vorliegt. Finale Latenz wird ab Start und ab audio-stop erfasst.
Peak-RSS kommt aus `/proc/self/status` (VmHWM) und umfasst Prozess, Modellladen
und Warm-up; Ablesung vor anschließendem Modellhashing. Keine Umrechnung von
Dateigröße zu gemessenem RAM. Das Harness führt jeden Lauf in einem separaten
Prozess aus und protokolliert Fehler. Rohwerte bleiben erhalten; Summary enthält
aufsummierte Korpus-WER, audio-gewichtete RTF, p50/p95 und maximales Peak-RSS.

Die Normalisierung ist fest als `NFC-lower-alnum-spaces-v1` versioniert:
Unicode NFC, lowercase, Nicht-Buchstaben/-Ziffern durch Leerzeichen ersetzen,
Whitespace zusammenfassen; Umlaute und ß bleiben erhalten. Keine wechselnde
Zahlennormalisierung. Für Baselines dieselbe Regel verwenden. Der Benchmark
von Moonshine/Kroko selbst und echte HA-Befehlsaufnahmen sind weiterhin nicht
ausgeführt. Keine HA-Kommandos werden vom Harness ausgelöst.

Nach Modell-/Korpusfreigabe: ./scripts/benchmark-example.sh zeigt den isolierten
Docker-Aufruf ohne Netzwerk/Portfreigabe. Das Entwicklungsimage verwendet den bereits aus dem geprüften finalen Image
kopierten Release-Build unter ./target/release/nemotron-unified-rust-wyoming.
Alternativ lässt sich dieser im Projektverzeichnis neu bauen:

```sh
docker run --rm --cpus 2 --memory 8g \
  -v "$PWD:/work" -w /work nemotron-unified-development:pr4141 \
  cargo build --locked --release --features sherpa
```

Der spätere echte Test muss Sprachwahl, brauchbare deutsche Hypothesen,
EOF-Verhalten und fehlenden Audioverlust prüfen. Die N100-CPU stellt vier
Kerne sowie AVX2/FMA/AVX-VNNI bereit, kein AVX-512. Der Runtime-Build nutzt
CPU-Dispatch; konkrete Kernelwahl und Echtzeitfähigkeit sind nicht gemessen.
0,56-s-Latenz, Offline-Modus und FP32-Vergleich sind noch nicht in diesem
L37-Adapter implementiert. Verkürzter Linkskontext ist ein Qualitäts-/Speed-
Tradeoff und muss als eigene Variante berichtet werden.

## Unraid-Konfigurationsbeispiel

./config/unraid-template.xml (Unraid-Template), ./config/unraid.env.example und
./config/compose.example.yaml sind Beispiele,
kein gestartetes Deployment. Vorgaben: separates Modellverzeichnis read-only
auf `/models`, Bridge-Netzwerk, Hostport beispielhaft 10310 → Container 10300,
Threads 2 als Startwert, keine GPU, UID/GID 65534, zunächst Restart `no`.
Modellverzeichnis/-dateien müssen für diese UID lesbar sein. Kein PUID-/PGID-
Mechanismus implementiert. Beispielvariablen werden von Compose ersetzt,
der Rust-Prozess selbst liest CLI-Optionen. Vor einem genehmigten Start
Portbelegung und Modellrechte prüfen. Kein vorhandener STT-Container wird ersetzt.

## Nächster konkreter Schritt

Zuerst ein freigegebenes, nach Größe und Hash geprüftes L37-INT8-ONNX-Paket
bereitstellen. Falls keines veröffentlicht wird, den Bezug des oben genannten
2,34-GiB-NeMo-Archivs **und** eine separate Exportumgebung ausdrücklich
freigeben; deren Gesamtumfang vor Download prüfen. Danach Export aus dem
gepinnten PR, Metadatenprüfung, ein echtes deutsches WAV mit Referenz zunächst
bei zwei Threads und anschließend die vollständige 1/2/4-Thread-Matrix.
Hier endet die Arbeit vor diesem Modelldownload und vor jeder produktiven
Docker-Bereitstellung.
