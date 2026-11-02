# Phase 4 – ONNX-Export und echte Inferenz: Vorbereitung, Freigabestopp

**Historischer Vorbereitungsstand.** Nach der Downloadfreigabe wurde der
CPU-Export erfolgreich durchgeführt. Aktuelle Ergebnisse einschließlich
18 echter STT-Messläufe: ./docs/PHASE4_RESULTS.md.

Stand: 31.10.2026. Projekt:
/mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming.
Relative Pfade in diesem Dokument gelten innerhalb dieses Projekts.

**Tatsächlicher Stand:** öffentliche Quellen und Ressourcen erneut geprüft;
CPU-Exportumgebung und Prüfskripte vorbereitet. Kein großes Modell und keine
Export-Pythonpakete heruntergeladen. Kein ONNX-Export und keine echte deutsche
Erkennung ausgeführt. Der Arbeitsstopp folgt ausdrücklich der Download-
Freigaberegel aus dem Phase-4-Auftrag. Phase 4 ist damit noch nicht vollständig
abgeschlossen. Die 15 erfolgreichen Tests aus Phase 3 sind weiterhin
Protokoll-/Softwaretests und kein Nachweis für Nemotron-Spracherkennung.

## 1. PR und exakter Exportpfad

[PR #4141](https://github.com/k2-fsa/sherpa-onnx/pull/4141) laut erneut gelesener
GitHub-API weiterhin **offen, nicht gemergt**, Head:
`31ba0e438f8065189a8e5589d84dfd7faf516d3d`.
Dieser Commit bleibt identisch mit der vorhandenen Rust-/C++-Runtime.
Die darin enthaltene gestapelte Streamingkorrektur wird verwendet; der später
abweichende Head von PR #4133 wird nicht ungeprüft darübergelegt.

Exporter im Repository: `scripts/nemo/nemotron-labs-unified-asr-0.6b/export_onnx.py`.
Primärquelle: [Exportcode am festen Commit](https://github.com/k2-fsa/sherpa-onnx/blob/31ba0e438f8065189a8e5589d84dfd7faf516d3d/scripts/nemo/nemotron-labs-unified-asr-0.6b/export_onnx.py).
Lokale geprüfte Kopie: ./docs/evidence/phase4-export-onnx.py.
SHA256 des Quelltextes:
`2de6ac2dd5207fae6455bee95e6e32e1ae42afc96db378f45ef341edba74bea2`;
identisch mit der in Phase 3 gesicherten Kopie.

Das zugehörige Upstream-Skript ./docs/evidence/phase4-upstream-run.sh nennt
NeMo-Revision `43dd97ddf`, aufgelöst zu
`43dd97ddf50dc3b3104cc22471f6e30407d1b18c`.
Es installiert NeMo ASR, ONNX, ONNX Runtime und IPython ungepinnt für die letzten
drei Pakete. Außerdem lädt es automatisch Modelle/Testaudio. Deshalb wurde
es **nicht ausgeführt**. Stattdessen ist ./scripts/export_l37.py ein
Offline-Wrapper für den unveränderten eigentlichen Exporter im vorhandenen
Docker-Sourcecheckout.

### L37 ist hier tatsächlich korrekt

Der Exporter setzt `set_default_att_context_size([args.left_context, 7, 7])`.
Bei 80 ms pro Encoderframe ergibt `--left-context 37`:

| Anteil | Encoderframes | Zeit |
|---|---:|---:|
| Linkskontext | 37 | 2,96 s |
| Zentraler Chunk | 7 | 0,56 s |
| Rechtskontext | 7 | 0,56 s |
| Algorithmische Latenz | Chunk + rechts | **1,12 s** |

L37 ist keine 0,37-s-Latenz und kein cache-aware Nemotron-3.5-Modell. Bei
Subsampling 8 umfasst das Featurefenster 408 Featureframes. Die tatsächlichen
Feature-/State-/Promptdimensionen werden nach Export aus Metadaten gelesen.
INT8 betrifft nur Encoder-MatMul-Gewichte, per-channel **QUInt8**. Sprach-
projektion, Predictor und Joiner bleiben FP32. Der Exporter schreibt auch
FP32-Zwischendateien und externe Encodergewichte; diese brauchen zusätzlichen
Platz und werden nicht unbemerkt in vorhandenen Verzeichnissen überschrieben.

## 2. Fertige Modellpakete erneut geprüft

Metadatenabfrage ausgeführt mit ./scripts/probe_models.py im vorhandenen
Docker-Toolchain-Image. Vollständige Ergebnisse unter
./docs/evidence/phase4-model-availability.json.

| Quelle | Ergebnis |
|---|---|
| Offizielles NVIDIA Unified-Repository | NeMo-Archiv, keine ONNX-Dateien |
| sherpa Release asr-models | 498 Assets, kein passendes Unified-Paket |
| Tags asr-models-2 und asr-models-3 | HTTP 404 |
| Vom PR-Workflow vorgesehenes HF-Repository für L37 | HTTP 401, nicht öffentlich bestätigt |
| HF-Suche nach nemotron-labs-unified | NVIDIA, FluidInference, loom-ai-org |
| FluidInference | CoreML/CoreAI, kein kompatibles sherpa-ONNX-L37-Paket |
| loom-ai-org | GGUF, kein passendes ONNX-Paket |

Damit ist in den geprüften Quellen **kein öffentlich abrufbares kompatibles
Unified-L37-ONNX-Paket verifiziert**. HTTP 401 beweist nicht, dass ein privates
Repository fehlt. Eine weltweite Nichtexistenz anderer Konvertierungen wird
nicht behauptet. Nemotron-3.5-ONNX-Dateien werden nicht ersatzweise verwendet.

## 3. CPU oder zwingende NVIDIA-GPU?

Der tatsächliche Exportcode lädt den Checkpoint über
`ASRModel.restore_from(..., map_location="cpu")`, setzt eval und verwendet
CPU-Tensoren auch für den Sprach-Prompt. Er enthält keinen Aufruf von `.cuda()`
oder expliziter CUDA-Execution-Provider-Auswahl. Das Upstream-Workflow-Beispiel
sieht macOS vor. Aus diesen Quellen ergibt sich **kein nachgewiesener GPU-Zwang
für den Exportpfad**. Das ist eine Quellcodeprüfung, kein hier erfolgreich
absolvierter CPU-Export.

NeMo importiert umfangreiche ASR-Infrastruktur. Sein Linux-Paketplan enthält
`cuda-bindings`, obwohl CPU-PyTorch ausgewählt wird. Solche Python-Bindings
allein belegen keinen notwendigen GPU-Kernel; tatsächliche Import- und
Exportfähigkeit bleibt nach Installation zu prüfen. Es werden keine
CUDA-PyTorch-Wheels, GPU-Geräte oder NVIDIA-Container-Runtime angefordert.
Wenn Restore/Export trotzdem zwingend eine GPU voraussetzt, wird mit dem
konkreten Stacktrace gestoppt. Keine ungeprüften Eingriffe in NeMo-Kernel und
keine erzwungene Ersatzportierung.

## 4. Abhängigkeiten und reproduzierbare Umgebung

Maßgebliche Paketquelle ist NeMos ./pyproject.toml im oben festgelegten
Checkout, hier gesichert als ./docs/evidence/phase4-nemo-pyproject.toml.
Wichtige deklarierte Anforderungen: Python >=3.10, Torch >=2.7, NumPy >=1.22,
Hugging Face Hub >=0.24, ONNX sowie das ASR-Extra mit lhotse 2.0.0a6, librosa,
scipy, SentencePiece, datasets, pandas, hydra/omegaconf, Lightning <=2.4,
TorchMetrics und weiteren Logging-/Trainingspaketen.

./export/constraints-cpu.txt legt **Kandidaten**, noch keinen erfolgreich
aufgelösten vollständigen Lock, fest:

- Torch 2.7.1+cpu und Torchaudio 2.7.1+cpu, Python 3.11/x86_64-Wheels im
  offiziellen CPU-Index per Metadaten gefunden.
- NumPy 1.26.4 und ONNX 1.18.0, Existenz und Wheelgrößen per PyPI-Metadaten geprüft.
- Python ONNX Runtime 1.23.2, CP311-Linux-Wheel vorhanden, 17.372.080 Byte.
  **Python-Paket 1.28.2 liefert beim geprüften PyPI-Endpunkt HTTP 404.**
  Die vorhandene native sherpa-Runtime nutzt dagegen ORT 1.28.2. Diese Versions-
  differenz bleibt sichtbar; die erzeugten Graphen müssen später auch in der
  tatsächlichen Rust-/C-Runtime laufen.

Prüfnachweise: ./docs/evidence/phase4-dependency-metadata.json und
./docs/evidence/phase4-ort-candidate.json. Nur JSON/HTML-Metadaten wurden bezogen,
keine Wheels. Die vollständige transitive Lösung, gesamte Downloadgröße,
Importkompatibilität der Kandidaten und Hash-Lock sind noch offen. Ein
`pip freeze` nach erfolgreichem Aufbau allein ersetzt keinen vollständigen
Artefakt-/Hash-Lock. Nach Freigabe Paketlösung/Größenbudget prüfen und Freeze,
pip-check, Installationsprotokoll und Image-Digest sichern; erst dann gilt die
Exportumgebung als reproduzierbar validiert. Das bisherige Runtime-Image
wird nicht durch diesen experimentellen Exportaufbau ersetzt.

### Vorbereitete Dateien

- ./export/Dockerfile: separate venv im vorhandenen Entwicklungsimage; explizite
  Buildfreigabe vor Paketdownloads, CPU-PyTorch, NeMo am festen Commit,
  Importtest, pip-check und Freeze. Noch nicht als Exportimage fertig gebaut.
- ./scripts/export_l37.py: verlangt vorhandene lokale Modelldatei mit exakter
  Größe/SHA256, prüft Sourcecommit, verweigert vorhandenes Ausgabeverzeichnis,
  setzt Offline-Modus und startet den originalen Exporter mit L37.
- ./export/validate_bundle.py: vorbereitete Graph-/ABI-Diagnose an späteren
  echten Gewichten; ausgeführte Spracherkennung wird nie behauptet.

Der Wrapper verwendet `--model`, sodass der automatische HF-Downloadzweig des
Exporters nicht erreicht wird. Für Exportausführung ist `--network none`
vorgesehen. Fehlende zusätzliche Tokenizer-/Modellartefakte führen damit zu
einem sichtbaren Fehler statt einem versteckten Nachladen.

## 5. Speicher und Lizenz vor dem Download

Read-only erfasst:

- Projekt-Dateisystem: ungefähr **340,2 GB / 316,9 GiB verfügbar**.
- Docker-Dateisystem meldet ähnlich viel freien Platz; die Werte dürfen wegen
  möglichem gemeinsamem Pool nicht als zwei getrennte Budgets addiert werden.
- RAM gesamt rund 31,1 GiB, aktuell etwa **17,2 GiB verfügbar**, kein Swap.
- Snapshots: ./docs/evidence/phase4-disk.txt und ./docs/evidence/phase4-memory.txt.

Offizieller Originalcheckpoint, festgelegte HF-Revision
`023ce907267a09a308a5cb69239447cb3d0c1597`:

- Größe **2.507.735.040 Byte = ca. 2,34 GiB**.
- SHA256 `1718cc1b44fb8597b2356328d706a8d89f31c389ca6f2256c2e3f743c0246936`.
- URL: [Originalcheckpoint](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b/resolve/023ce907267a09a308a5cb69239447cb3d0c1597/nemotron-labs-unified-asr-0.6b.nemo).
- Nicht heruntergeladen.

Planungsreserve für Checkpoint, entpackte Daten, mehrfache FP32-Graphen,
Quantisierung, Pythonumgebung und Docker-Layer: **40 GiB freier Platz** als
konservative Untergrenze, keine gemessene Exportgröße. Der Wrapper prüft diese
Reserve am Ausgabe-Dateisystem. Die Gewichte allein beanspruchen FP32 etwa
2,5 GB; Graphkopien und Quantisierung erhöhen den Peak erheblich. Ein Peak von
12–24 GiB ist ein vorsichtiges Planungsrisiko, kein Messwert. Der erste
freigegebene Export soll auf zwei CPUs und **12 GiB RAM ohne zusätzlichen Swap**
begrenzt werden; er kann damit an OOM scheitern. Speichergrenzen werden nicht
zulasten bestehender Container automatisch erhöht.

Lizenz: **OpenMDW 1.1**, Original unter ./docs/evidence/phase4-OpenMDW-1.1.txt
sowie der gepinnten Modell-Lizenz unter ./docs/evidence/phase4-model-LICENSE.md
und [Primärquelle](https://github.com/OpenMDW/OpenMDW/blob/main/1.1/LICENSE.OpenMDW-1.1).
Nutzung/Änderung einschließlich kommerzieller Nutzung erlaubt. Bei Weitergabe
von Modellmaterial auch die Lizenz sowie anwendbare Copyright-/Herkunftshinweise
mitführen; das gilt auch für ONNX-/quantisierte Versionen. Weitere Rechte,
Gewährleistungsausschluss und Klage-/Beendigungsklausel beachten. Es erfolgt
keine Weitergabe/Veröffentlichung in dieser Phase.

## 6. Komponentenprüfung: tatsächlicher Status

| Komponente | Quell-/Vertragsprüfung jetzt | Ausführung mit echten Gewichten |
|---|---|---|
| Encoder | Drei Eingänge: Float-Features, int64-Länge, int64-Prompt; L37/7/7 und Sprachprojektion bestätigt | Nicht ausgeführt |
| Predictor/Decoder | Targets und Länge int32; zwei Float-LSTM-Zustände [L,1,H]; Export-/C++-Vertrag gelesen | Nicht ausgeführt |
| Joiner | Akustik + Predictor, Vokabular einschließlich Blank; C++-Vertrag geprüft | Nicht ausgeführt |
| Tokenizer | Originalexport schreibt NeMo-Vokabular/IDs, Blank-ID = vocab_size | Token-ID-/SentencePiece-Parität nicht geprüft |
| Sprache de | Prompt wird aus model_defaults.prompt_dictionary exportiert und per Stream gesetzt | Tatsächlicher de-Promptindex noch nicht aus Gewichten geprüft |
| Deutsche Ausgabe | Kein echtes Audio ausgewertet | Nicht ausgeführt |

Die vorbereitete Diagnose prüft nach dem Export ONNX-Checker, CPU-Sessions,
INT8-MatMul-Präsenz, Ein-/Ausgangsverträge, fortlaufende Token-IDs/Blank und den
de-Prompt. Ein Durchlauf mit Null-Features prüft lediglich Graphverdrahtung,
Zustandsformen und endliche numerische Ausgaben. Er ist **kein Erfolgsnachweis
für Spracherkennung**, keine WER-Messung und kein NeMo/ONNX-Paritätsnachweis.
Die JSON-Ausgabe trägt ausdrücklich `speech_recognition_validated=false`.

Zusätzlich erforderlich und noch offen: Original-SentencePiece gegen Tokenliste
abgleichen, echte Audiofeatures gegen NeMo vergleichen, Encoder-FP32 numerisch
gegen NeMo, danach INT8-Abweichung, Predictor-Zustandsfortschreibung und Joiner
gegen Referenztensoren prüfen. Die vorhandene sichere sherpa-Rust-Anbindung
bleibt der Decodingpfad; kein neuer RNN-T-Decoder wird implementiert.

## 7. Deutsche Referenz und CPU-Messung

Im Projekt liegt nur ./benchmarks/manifest.example.jsonl, kein echter deutscher
Referenzkorpus. Bei einer read-only Suche in naheliegenden Workspace-Testpfaden
wurde keine passende manuell geprüfte deutsche Aufnahme mit Referenz bestätigt.
Systemklänge und fremdsprachige Beispiel-WAVs werden dafür nicht verwendet.
Keine vorhandenen Audiodateien wurden geändert oder als deutsche Referenz
umdeklariert; es wurde auch keine TTS-Aufnahme als echter Sprecher ausgegeben.

Nach Modellfreigabe benötigt der erste Test eine echte Aufnahme: 16 kHz,
mono PCM16, 80 ms bis 120 s, menschlich geprüftes Referenztranskript und SHA256.
Zunächst zwei Threads, tatsächliche Hypothese/Fehler dokumentieren. Erst bei
funktionierender Erkennung die identische WAV mit Threads 1/2/4 und jeweils
drei Wiederholungen ausführen; dafür ist ./scripts/benchmark.py vorbereitet.

Neu ergänzt: CPU-Nutzer-/Systemzeit des jeweiligen Kindprozesses und mittlere
Auslastung `100 * CPU-Sekunden / Prozess-Walltime`. **100 % entspricht einem
Kern, 400 % vier Kernen.** Die Messung umfasst den gesamten Prozess mit Laden,
Warm-up und Hashing, nicht nur den Erkennungsabschnitt. Die bisherigen Rust-
Metriken trennen Compute-RTF, Zeit bis erster Hypothese, endgültiges Transkript,
Endlatenz und VmHWM. Transkripte, Referenzen und Wortfehler werden gespeichert.

Aktuelle Messergebnisse:

| Threads | RTF | Erkennungsdauer | Peak-RSS | CPU-Auslastung | Tatsächliche Transkription |
|---:|---|---|---|---|---|
| 1 | Nicht gemessen | Nicht gemessen | Nicht gemessen | Nicht gemessen | Keine |
| 2 | Nicht gemessen | Nicht gemessen | Nicht gemessen | Nicht gemessen | Keine |
| 4 | Nicht gemessen | Nicht gemessen | Nicht gemessen | Nicht gemessen | Keine |

## 8. In dieser Phase ausgeführte Prüfungen

- Metadatenabfragen zu PR, Modellpaketen und Paketversionen erfolgreich soweit
  oben angegeben; 401/404-Antworten explizit erhalten.
- Exportquelltext am festen Commit erneut bezogen und Hash mit Phase 3 verglichen.
- Python-Syntax und CLI-Hilfe für Wrapper/Diagnose im bestehenden Docker-Image
  geprüft, ohne ML-Pakete zu importieren. Auch das geänderte Benchmark-Harness
  ist syntaktisch geprüft. Kein Laufzeit-/Inferenztest daraus abgeleitet.
- Default-Build von ./export/Dockerfile endet **erwartet vor apt/pip** an der
  fehlenden Downloadfreigabe. Docker-Build Exit 1, innerer Guard Exit 2.
  Kein fertiges Exportimage gebaut. Keine großen Abhängigkeiten geladen.
- Nachweise: ./docs/evidence/phase4-preparation-checks.log und
  ./docs/evidence/phase4-export-approval-guard.log.

Rust-Code und das funktionierende Phase-3-Runtimeimage wurden nicht verändert
oder neu gebaut. Keine bestehenden Container gestoppt/verändert, kein
produktiver Dienst, keine HA-Integration und kein GitHub-/GHCR-Publish.

## 9. Konkreter nächster Schritt und Freigabeumfang

**Jetzt Freigabe für den 2,34-GiB-Originalcheckpoint einholen.** Für den separaten
CPU-Exportaufbau wird zusätzlich ein ausdrücklich begrenztes Paketdownload-
Budget benötigt; vorgeschlagen höchstens **3 GiB weitere Downloads**. Das ist
eine Freigabeobergrenze, keine behauptete exakte Summe. Die vollständige
Abhängigkeitslösung/Größenliste muss innerhalb dieses Budgets geprüft werden;
bei Überschreitung oder zwingender GPU-Anforderung erneut anhalten. Ohne
Freigabe wurde nichts davon gestartet.

Nach Freigabe: Pakete auflösen/Größen kontrollieren, Checkpoint-Hash prüfen,
CPU-Importtest, frisches L37-Ausgabeverzeichnis, originalen Exporter ausführen,
Komponenten/Tokenizer und NeMo-Parität prüfen, echtes deutsches WAV bei zwei
Threads, danach 1/2/4-Thread-Matrix. Fehlende Aufnahme/Referenz bleibt ein
zweiter unabhängiger Blocker für den Qualitätsnachweis.

Vorbereiteter Exportaufruf **erst nach Freigabe und erfolgreichem Imageaufbau**:

```sh
docker run --rm --network none --cpus 2 --memory 12g --memory-swap 12g \
  -v "$MODEL_DIR:/input:ro" -v "$OUTPUT_PARENT:/output" \
  nemotron-unified-export:phase4 \
  --model /input/nemotron-labs-unified-asr-0.6b.nemo \
  --output /output/L37-new
```

Die Shellvariablen sind dabei auf die später freigegebenen konkreten
Verzeichnisse zu setzen. Der Aufruf lädt keine Dateien und öffnet keine Ports.
