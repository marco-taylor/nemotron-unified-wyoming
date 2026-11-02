# Machbarkeit: Nemotron Labs Unified ASR 0.6B, Rust Wyoming, Deutsch

Stand: 31.10.2026. Ergebnis: bedingt machbar; CPU-Echtzeit auf dem N100 ist
unbewiesen. Kein produktionsfähiges Modell integriert. Phase 1/2 endet hier.

## 1. Technischer Architekturvergleich

Das Ziel ist ein FastConformer-RNN-T, kein TDT- oder CTC-Modell. Decoder von
Parakeet TDT oder Kroko können deshalb nicht unverändert übernommen werden.
Ein gemeinsamer Checkpoint deckt Offline- und Streaming-Betrieb ab. Details
und Kontextvorgaben: [offizielle Modellkarte](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b).

| Teil | Zielmodell | Konsequenz für Rust |
|---|---|---|
| Akustik | 24 FastConformer-Schichten, 8-faches Subsampling | Encoder möglichst als ONNX ausführen |
| Offline | Vollkontext, nichtkausale Faltungen | Eigener Offline-Export/-Modus und Längentests |
| Streaming | Chunk-Attention und Dynamic Chunk Convolution | Masken, Padding und gültige zentrale Frames exakt übernehmen |
| Predictor | Zustandsbehaftetes rekurrentes RNN-T-Netz | Zustand pro Verbindung; Dimensionen aus Exportmetadaten |
| Joint | Verknüpft Akustik und Predictor zu Token-/Blank-Scores | Kein TDT-Duration-Head; wiederholte Token pro Frame möglich |
| Sprache | One-hot-Prompt mit Encoder-Ausgabe fusioniert und projiziert | `de` nach Modellwörterbuch in Prompt-ID übersetzen |
| Tokenizer | Gemeinsames mehrsprachiges SentencePiece | Originalvokabular, IDs und Blank bewahren |

Wesentlicher Unterschied zu Nemotron 3.5: Das Unified-Modell verwendet derzeit
**buffered Streaming**. Der linke Kontext wird erneut berechnet; übliche
cache-aware Encoder-Zustände sind kein gleichwertiger Ersatz. Nichtkausales
Subsampling und Rechtskontext verhindern eine naive Übernahme von Cache-Logik.
Ein erzwungener Cache-Modus verändert die trainierten Bedingungen.
[Quelle: Streaming-Limitation der Modellkarte](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b#streaming-inference-limitation).

Audiovertrag: 16 kHz, mono; Wyoming-seitig zunächst signed PCM16 little endian.
PCM wird später in Float konvertiert. Modellgetreues Log-Mel-Preprocessing muss
Fenster/Hop, FFT, Mel-Bänke, Dither, Preemphasis, Log-Epsilon, Normalisierung,
Padding und gültige Längen aus der tatsächlichen NeMo-Konfiguration übernehmen.
Diese Parameter wurden ohne Archivdownload nicht vollständig verifiziert;
übliche ASR-Defaults dürfen sie nicht ersetzen. Features zuerst numerisch gegen
NeMo vergleichen, auch an Chunk-Grenzen. Tokenisierung benötigt den originalen
SentencePiece-/Token-ID-Vertrag einschließlich Wortgrenzen und Sonderzeichen.
Einfaches Zusammenkleben von Token-Strings genügt nicht als Nachweis.

Sprachkonditionierung sitzt hinter der akustischen Repräsentation. Der aktuelle
Exporter faltet `prompt_kernel` in den Encoder und führt `prompt_index` als
zusätzlichen int64-Eingang ein. `de` ist keine frei gewählte numerische Konstante.
Bei sherpa muss die per-stream Sprachoption auch aus Rust erreichbar sein;
andernfalls ist ein kleiner Binding-Zusatz oder der ort-Weg nötig.
[Exporter, festgelegter PR-Commit](https://github.com/k2-fsa/sherpa-onnx/blob/31ba0e438f8065189a8e5589d84dfd7faf516d3d/scripts/nemo/nemotron-labs-unified-asr-0.6b/export_onnx.py).

## 2. Verfügbare Inferenz-Backends

| Backend | Eignung | Stand und Aufwand |
|---|---|---|
| sherpa-onnx + Rust | Bevorzugter Kandidat bei stabilisiertem Upstream | Rust-API und native C/C++-Runtime vorhanden; Unterstützung genau dieses Modells noch offener PR; Sprachoption und ABI prüfen |
| ONNX Runtime + `ort` | Kontrollierbarer Ausweichweg | Encoder/Predictor/Joiner als Sessions, Greedy-Schleife in Rust; DSP und Streaming-Vertrag selbst verantworten |
| Candle | Technisch denkbar, für erste Umsetzung ungeeignet | Kein nachgewiesener fertiger Zielmodellpfad; FastConformer, Masken, Gewichtsimport und RNN-T würden erheblichen Portierungsaufwand erzeugen |
| NVIDIA NeMo Speech | Referenz für Korrektheit und Export | Offizieller Python/PyTorch-Pfad, Modellkarte nennt Speech 3.1.0; kein Rust-Backend und kein Beleg für N100-Echtzeit |

Quellen: [sherpa Rust-Beispiele](https://github.com/k2-fsa/sherpa-onnx/tree/master/rust-api-examples),
[ort](https://github.com/pykeio/ort), [Candle](https://github.com/huggingface/candle),
[NeMo-Streamingreferenz](https://github.com/NVIDIA-NeMo/Speech/blob/main/examples/asr/asr_chunked_inference/rnnt/speech_to_text_streaming_infer_rnnt.py).
Native Bibliotheken bleiben bei sherpa und ort erforderlich. Rust allein macht
Encoderberechnung nicht schneller; Kernel, Quantisierung und Kontextarbeit
bestimmen den Aufwand. Bestehende sherpa-Beispielskripte können Modelle oder
Bibliotheken automatisch laden und wurden deshalb nicht ausgeführt.

## 3. ONNX-Exportstatus

### Verifiziert

Das offizielle HF-Repository enthält am Modell-Commit
`023ce907267a09a308a5cb69239447cb3d0c1597` **keine ONNX-Dateien**. Das NeMo-Archiv
hat laut [HF-Metadaten-API](https://huggingface.co/api/models/nvidia/nemotron-labs-unified-asr-0.6b?blobs=true)
2.507.735.040 Byte (2,508 GB dezimal; ca. 2,336 GiB), SHA256
`1718cc1b44fb8597b2356328d706a8d89f31c389ca6f2256c2e3f743c0246936`.
Es wurde nicht heruntergeladen. Ein späterer Export braucht zusätzlichen Platz
für entpackte Gewichte, FP32-ONNX, externe Daten, Quantisierung und Python-Umgebung.
Vor Freigabe tatsächlichen freien Platz und vollständigen Downloadumfang prüfen.

Es existiert inzwischen ein **konkreter kompatibilitätsorientierter Exporter**:
[sherpa PR #4141](https://github.com/k2-fsa/sherpa-onnx/pull/4141), am Prüftag
laut GitHub-API offen und nicht gemergt, Head
`31ba0e438f8065189a8e5589d84dfd7faf516d3d`. Er baut auf dem ebenfalls offenen
[Streaming-Fix #4133](https://github.com/k2-fsa/sherpa-onnx/pull/4133) auf.
Dessen Berichte sind Upstream-Autorenangaben, keine hier reproduzierten Tests.
Die geplante Veröffentlichungs-Workflow-Ausführung war laut PR-Beschreibung noch
nicht erfolgt. Ein geprüftes fertiges Downloadpaket für dieses konkrete Modell
wurde in dieser Analyse nicht bestätigt. Das ist kein Nachweis, dass weltweit
keine Community-Artefakte existieren. Exporte für Nemotron 3.5 oder das englische
Parakeet Unified sind keine austauschbaren Zielmodell-Exporte.

### Umfang und Grenzen

Der Exporter erzeugt Encoder mit Sprachprojektion, Predictor (`decoder`) und
Joiner sowie Tokenliste. Damit sind die neuronalen Teile grundsätzlich nach
ONNX zerlegbar. Audio-DSP, RNN-T-Suchschleife, Chunk-Verwaltung und Textaufbereitung
bleiben Runtime-Aufgaben. Ein einzelner vollständiger Audio-zu-Text-ONNX-Graph
ist weder nötig noch hier nachgewiesen. FP32-Encoder benötigt externe Gewichte
wegen der Protobuf-Größengrenze; diese müssen gemeinsam versioniert werden.
[Exporter-Dokumentation](https://github.com/k2-fsa/sherpa-onnx/blob/31ba0e438f8065189a8e5589d84dfd7faf516d3d/scripts/nemo/nemotron-labs-unified-asr-0.6b/README.md).

Der Prompt-Teil exportiert dynamische Batch-/Zeitachsen mit Opset 17. Das
belegt keine beliebig veränderbaren Streaming-Kontexte: im aktuellen Exporter
ist Attention-Kontext `[L,7,7]` festgelegt. L70 und L37 entsprechen 5,60 bzw.
2,96 s links; beide nutzen 0,56 s Chunk plus 0,56 s rechts = 1,12 s.
Für 0,56 s algorithmische Latenz ist ein eigener geprüfter Export mit
0,16 s Chunk plus 0,40 s rechts erforderlich. Offline-Vollkontext ebenfalls
gesondert validieren. ONNX Runtime kann dynamische Eingaben und übliche
Maskenoperatoren ausführen; tatsächliche Operator-/Shape-Unterstützung muss
am exportierten Graph mit mehreren Längen, Erstchunk, EOF und Padding geprüft
werden. Tensorformen wurden hier nicht durch Inferenz bestätigt.

RNN-T in Rust ist realistisch: Predictor am Sequenzanfang initialisieren,
für jeden gültigen Encoderframe Joint ausführen, bei Blank Frame fortschalten,
bei Nichtblank Token übernehmen und Predictorzustand aktualisieren. Mehrere
Symbole pro Frame erlauben, Sicherheitsgrenze setzen, ausgeblendeten Rechts-
und Linkskontext nicht erneut decodieren. Blank-ID, Zustandsachsen, Startsymbol
und Tokenverarbeitung aus dem Modell ableiten. Bei Blank keinen spekulativen
Predictorzustand übernehmen. Greedy zuerst gegen NeMo vergleichen; Beam Search
ist eine spätere Erweiterung. Kein Decoder wurde hier portiert.

## 4. Quantisierung und N100

INT8 ist realistisch als **partielle** Quantisierung. Der PR quantisiert
Encoder-MatMul-Gewichte per-channel QUInt8; Prompt, Predictor und Joiner bleiben
FP32. Das ist kein vollständig quantisiertes Netz. Dynamische Quantisierung
braucht keine Kalibrierungsdaten, statische QDQ-Varianten dagegen repräsentative
deutsche Kalibrierung ohne Überschneidung mit dem Testset. Sättigungsprobleme
bei manchen U8S8-x86-Pfaden und möglicher Qualitätsverlust erfordern einen
FP32-Vergleich. [ORT-Quantisierung](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html).

Lokal read-only per `lscpu` festgestellt: Intel N100, 4 Kerne / 4 Threads,
AVX, AVX2, FMA, F16C, SSE4.1/4.2 und AVX-VNNI; kein AVX-512-Flag, kein AMX.
AVX-VNNI ist für Integer-Kernels interessant, garantiert aber nicht, dass der
gewählte Runtime-Build diese Instruktionen nutzt. F16C liefert Konvertierung,
keine Zusage schneller FP16-Arithmetik. CPU-Bericht liegt im neuen Projekt unter
./docs/evidence/lscpu.txt. Pfade in diesem Dokument sind relativ zum neuen Projekt.

Grobe Gewichtsrechnung: 600 Mio. Parameter ergeben FP32 etwa 2,4 GB, bei reinem
INT8 theoretisch 0,6 GB; reale Prozesse brauchen zusätzlich nichtquantisierte
Gewichte, Aktivierungen, Arenen und temporäre Puffer. Das sind keine RSS-Messwerte.
32 GB Gesamtspeicher reichen wahrscheinlich für Laufzeitexperimente, frei
verfügbarer RAM und konkurrierende HA-/Docker-Last müssen gesondert erfasst werden.
Ein Export kann deutlich mehr Ressourcen als die Inferenz benötigen.

Größtes Leistungsrisiko ist die Neuberechnung des linken Kontexts. Bei 0,56 s
Latenz wird alle 0,16 s ein neues Fenster verarbeitet. Fenster-/Schrittverhältnis
als grober Arbeitsindikator: 6,72/0,56 = 12 bei 1,12 s, 6,16/0,16 = 38,5 bei
0,56 s; das ist kein exaktes FLOP- oder RTF-Modell. Kürzerer Kontext kann helfen,
verändert jedoch die Qualität. CPU-Memory-Bandbreite, thermisches Limit und vier
konkurrierende Kerne machen lineare Threadskalierung unwahrscheinlich.
Keine belastbare N100-Latenz- oder WER-Prognose ohne Messung.

## 5. Rust-Wyoming und Implementierungsplan

Die [Rust-Crate wyoming 0.2.1](https://docs.rs/wyoming/0.2.1/wyoming/)
([Repository](https://github.com/zzjakub/wyoming)) bietet Sans-I/O-Protokolltypen,
Apache-2.0. Sie ist ein Kandidat für Eventdaten, kein fertiger HA-STT-Server.
Dokumentationsumfang ist gering; Framing, zusätzliche JSON-Datenblöcke,
Binärpayload, Teilreads und Fehler müssen gegen die
[offizielle Wyoming-Spezifikation](https://github.com/OHF-Voice/wyoming) geprüft
werden. Für diesen Bedarf wurde kein bereits validierter kompletter Rust-
Wyoming-STT-Server nachgewiesen. Entscheidung über Crate oder eigenen kleinen
Codec erst nach Kompatibilitätstests; noch keine Abhängigkeit eingebunden.

Geplante Events: describe/info, transcribe, audio-start/chunk/stop,
transcript/error. TCP benötigt Sessionzustand, begrenzte Header-/Daten-/Audio-
Größen, Timeouts und Backpressure. `language=de` explizit verwenden. Ein
unimplementiertes Backend darf kein funktionierendes ASR-Angebot annoncieren
und keine erfolgreiche leere Transkription vortäuschen.

1. **Jetzt abgeschlossen:** getrenntes Rust-Paket, sechs Module und klare
   NotImplemented-Grenzen; Dokumentation und Benchmark-Konzept. Kein Listener.
2. **Nächster freizugebender Arbeitsumfang:** Toolchain bereitstellen und
   Grundgerüst kompilieren. Upstream-Merge und Sprachoption im Rust-Binding prüfen.
   Vor Modellbezug Größe, Hash, Platz und Quelle erneut prüfen; Freigabe einholen.
3. **Nach Freigabe:** isolierte NeMo-Referenz und modellgetreue Features/Tokenizer
   sichern. Exporter an festen Commit binden; Offline-FP32 mit ORT validieren.
4. **Danach:** Prompt, Predictor und Joiner numerisch vergleichen; Greedy-Rust
   nur falls sherpa keinen passenden verifizierten Pfad bietet.
5. **Streaming:** erst 1,12 s, danach separaten 0,56-s-Export prüfen; EOF,
   Masken, Länge, Kontextversatz und Sitzungsisolation mit NeMo vergleichen.
6. **Optimierung:** partielle INT8-Version, Threads 1/2/4, Qualitätsverlust und
   CPU-Verbrauch messen; Kontextverkürzung als getrennte Variante.
7. **Protokoll:** Wyoming-Codec-/Sessiontests und lokaler Testclient. Erst nach
   weiterer Freigabe Docker/HA-Integration; kein Deployment aus diesem Auftrag.

## 6. Risiken, Blocker und Abbruchkriterien

| Punkt | Status / nötiger Nachweis |
|---|---|
| Zielmodell-Support | Offene PRs #4141/#4133; kein stabiler Integrationsnachweis |
| 0,56-s-Export | Im geprüften Exporter nicht vorbereitet; eigener Shape-/Maskentest nötig |
| Offline | Vollkontext nicht durch Streaming-Export abgedeckt |
| DSP/Tokenizer | Exakte Archivkonfiguration noch nicht extrahiert |
| N100-Echtzeit | Nicht gemessen; buffered Streaming kann RTF deutlich über 1 verursachen |
| Rust-Toolchain | `cargo`/`rustc` nicht im PATH oder üblichen Cargo-Verzeichnis gefunden; Build nicht ausgeführt |
| Qualität | Deutsche HA-Befehle und kurze Äußerungen noch nicht getestet |
| INT8 | Speed-up und WER-Erhalt auf tatsächlichem ORT-Build offen |
| Vergleichsmodelle | Moonshine-Small-DE-/Kroko-Versionen, Lizenz und Hash vor Messung festlegen |

Go/No-Go erst nach Referenzparität und gleichen Audios. Bleibt RTF bei der
gewählten Konfiguration >= 1 oder wächst die Streamingwarteschlange, ist
Echtzeitbetrieb damit nicht erreicht. Grenzwerte für akzeptable deutsche WER
und Endlatenz vor Messung festlegen; keine nachträgliche Auswahl schöner Werte.

## 7. Lizenz und Sicherheitsgrenzen

Gewichte: **OpenMDW 1.1**, keine pauschale Apache-Lizenz.
[Originaltext](https://github.com/OpenMDW/OpenMDW/blob/main/1.1/LICENSE.OpenMDW-1.1)
erlaubt Nutzung und Änderungen einschließlich kommerzieller Verwendung.
Bei Weitergabe von Modellmaterial müssen Lizenzkopie sowie anwendbare
Copyright-/Herkunftshinweise erhalten bleiben; das betrifft auch konvertierte
oder quantisierte Weitergaben. Die Lizenz enthält Beendigungsklauseln bei
bestimmten Patent-/Copyright-Klagen, Gewährleistungsausschluss und Verantwortung
für Dritt-/Einwilligungsrechte. Outputs haben daraus keine zusätzlichen
Nutzungs-/Weitergabepflichten. Code- und Dependency-Lizenzen separat prüfen,
vor allem vor Übernahme von Exportcode oder Veröffentlichung.

Es wurden ausschließlich neue lokale Dateien angelegt sowie öffentliche
Metadaten/kleine Quelltexte gelesen. Keine Containeraktionen, keine vorhandenen
Modelle verändert, keine HA-Konfiguration geändert, kein GitHub-Publish,
kein großes Modell geladen und keine vollständige Modellportierung begonnen.
Relay-Inbox war leer; es wurden keine Nachrichten an andere Workspaces gesendet.
