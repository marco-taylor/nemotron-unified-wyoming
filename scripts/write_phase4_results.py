import datetime,json,statistics
from pathlib import Path
base=Path.cwd()
host=Path('/mnt/nvme/appdata/codex-workspace/nemotron-unified-wyoming')
def link(rel,label=None):return '['+(label or rel)+']('+str(host/rel)+')'
rows=[json.loads(l) for l in (base/'benchmarks/results/n100-l37-real-v1.jsonl').read_text().splitlines()]
audit=json.loads((base/'export/reports/final-bundle-audit.json').read_text())
assert len(rows)==18 and all(r['status']=='ok' for r in rows)
assert all(r['hypothesis']=='Einsteigen bitte.' for r in rows)
lines=['# Phase 4 – Ergebnisse: echter deutscher Nemotron-Unified-Benchmark','',
'Stand: '+datetime.datetime.now(datetime.timezone.utc).isoformat()+'.', '',
'**Ergebnis: L37 wurde auf dem Intel N100 erfolgreich auf CPU exportiert und partiell INT8-quantisiert.** '
'Die vorhandene Rust-/sherpa-Runtime hat eine echte menschliche deutsche Aufnahme in allen 18 Messläufen korrekt auf Wortebene transkribiert. '
'Kein produktiver Container, keine Home-Assistant-Integration und keine Veröffentlichung.', '',
'## Tatsächliches Transkript und Aussagegrenze','',
'- Menschliche Referenz: **„Einsteigen bitte!“**',
'- Tatsächliche Ausgabe in allen 18 Läufen: **„Einsteigen bitte.“**',
'- Nach der festgelegten Normalisierung: 0 Wortfehler / 2 Referenzwörter; rohe Interpunktion unterscheidet sich.',
'- Aufnahme: **1,50025 s**, mono PCM16 / 16 kHz; keine TTS-Erzeugung, keine aus der Referenz eingesetzte Hypothese.',
'- **Ein Sprecher und zwei Wörter sind ein Funktionstest, kein repräsentativer deutscher WER-/HA-Korpus.** '
'Wiederholungen sind keine zusätzlichen unabhängigen Sprachproben.', '',
'Die Aufnahme stammt von Daniel Mietchen (Lingua Libre), aufgenommen am 02.03.2023. '
'Quelle und veröffentlichtes Referenztranskript: '
'[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:LL-Q188_(deu)-Daniel_Mietchen-Einsteigen_bitte!.wav), '
'Lizenz [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). '
'Originalformat: 44,1 kHz, mono PCM16; Resampling mit Python 3.11 audioop.ratecv, ohne Beschneiden. '
'Metadaten und Vorverarbeitung: '+link('benchmarks/audio/source-metadata.json')+', '+link('benchmarks/manifest.real.jsonl')+'.', '',
'Original-SHA256: `69c206fb2c773b34edcd25d463ef8e6223cc8c3b3c2773e2a0b92b794010a1a6`. '
'16-kHz-SHA256: `4cd5c09c2680e15f534dad37cf317ffda9f350130e104c8d097071e44b015275`.', '',
'## CPU-Benchmark','',
'Je drei Wiederholungen pro Threadzahl und Zuführungsmodus, rotierende Threadreihenfolge. '
'Jeder Prozess lädt das Modell, führt einen ungemessenen Warm-up aus und verwendet dann einen neuen Stream. '
'Vier CPUs und 4 GiB RAM als Containerobergrenze; kein Pinning/Governor-Wechsel, bestehende Dienste liefen weiter. '
'Der N100 besitzt vier Kerne und AVX2/FMA/AVX-VNNI; kein GPU-Einsatz.', '',
'Die Threadzahl ist sherpas num_threads pro ONNX-Session, kein hartes Gesamtprozess-Threadlimit. '
'Der Prozess verwendet mehrere Threadpools; daher können zwei konfigurierte Threads mehr als 200 % Prozess-CPU verursachen. '
'Alle drei Gruppen durften dieselben vier CPUs nutzen. Der vorherige einzelne Zwei-Thread-Smoke-Test war dagegen auf zwei CPUs begrenzt.', '',
'RTF = aktive Verarbeitungszeit einschließlich Featureberechnung, Decoder und EOF-Flush / Audiodauer; '
'Modellladen, Warm-up, Hashing und absichtliche Pacingpausen sind darin ausgeschlossen. '
'„Compute s“ ist die gemittelte aktive Erkennungsdauer. RAM ist der höchste Prozess-VmHWM der drei Läufe einschließlich Laden/Warm-up, vor dem Hashing gemessen.', '',
'**CPU % erfasst dagegen den gesamten Kindprozess**, einschließlich Laden, Warm-up und Hashing. '
'Zeitgewichteter Wert aus Nutzer-/Systemzeit geteilt durch Prozess-Walltime; 100 % entspricht einem Kern. '
'Das ist keine isolierte CPU-Auslastung nur während des Erkennungsabschnitts.', '',
'| Zuführung | Threads | RTF Ø | Compute s Ø | CPU % Prozess | Peak-RAM MiB | Final ab Start s Ø | Final nach audio-stop ms Median |',
'|---|---:|---:|---:|---:|---:|---:|---:|']
for paced in [False,True]:
    for t in [1,2,4]:
        g=[r for r in rows if r['paced']==paced and r['threads']==t]
        cpu=100*sum(r['process_cpu_user_seconds']+r['process_cpu_system_seconds'] for r in g)/sum(r['process_wall_seconds'] for r in g)
        lines.append(f'| {"Echtzeit-Pacing" if paced else "Ohne Pacing"} | {t} | {statistics.mean(r["rtf"] for r in g):.3f} | {statistics.mean(r["compute_seconds"] for r in g):.3f} | {cpu:.1f} | {max(r["peak_rss_bytes"] for r in g)/1024**2:.1f} | {statistics.mean(r["final_from_start_ms"] for r in g)/1000:.3f} | {statistics.median(r["final_after_audio_stop_ms"] for r in g):.1f} |')
lines += ['',
'Vor EOF erschien in **keinem** Lauf eine nichtleere Teilhypothese: First-partial bleibt `null`/nicht verfügbar. '
'Dies ist keine gemessene Latenz von null Millisekunden. Die kurze Aufnahme reicht für einen belastbaren Streaming-Partial-Latenztest nicht aus. '
'„Final nach audio-stop“ beginnt nach der letzten PCM-Verarbeitung; bei Backlog kann dieser Zeitpunkt später als das nominelle Audioende liegen.', '',
'**Vier Threads sind hier deutlich langsamer und verfehlen RTF < 1.** '
'Die Ursache wurde nicht profiliert; aus diesem kleinen Versuch lässt sich weder lineare Skalierung noch langfristige Echtzeitfähigkeit ableiten. '
'Ein und zwei Threads liegen in dieser Stichprobe unter RTF 1; längere Aufnahmen und realistische HA-Befehle bleiben nötig.', '',
'Rohdaten mit Hypothesen, Referenzen, Hashes, Zeiten und CPU-Zählern: '+link('benchmarks/results/n100-l37-real-v1.jsonl')+'. '
'Zusammenfassung: '+link('benchmarks/results/n100-l37-real-v1.summary.json')+'. '
'Der vorherige einzelne Zwei-Thread-Smoke-Test ist separat unter '+link('docs/evidence/phase4-first-real-inference.json')+' gespeichert und nicht in die 18er-Matrix gemischt.', '',
'## Export, Versionen und Kompatibilität','',
'- sherpa PR #4141 / Exporter: `31ba0e438f8065189a8e5589d84dfd7faf516d3d`; bei letzter Prüfung offen. '
'[Upstream-Exporter](https://github.com/k2-fsa/sherpa-onnx/blob/31ba0e438f8065189a8e5589d84dfd7faf516d3d/scripts/nemo/nemotron-labs-unified-asr-0.6b/export_onnx.py).',
'- NeMo: `43dd97ddf50dc3b3104cc22471f6e30407d1b18c`, installiert als 3.1.0.',
'- Export: CPython **3.11.14**, Torch **2.7.1+cpu**, NumPy **2.2.6**, ONNX **1.18.0**, Python ORT **1.23.2**.',
'- Zielruntime: vorhandenes Rust-Release / sherpa **2.0.1**, native ORT **1.28.2**, CPU-Provider, greedy_search, Sprache explizit `de`.',
'- Native Version-Metadatenkorrektur aus Phase 3 unverändert; kein neuer RNN-T-Decoder und keine Änderung an der Rust-Inferenzlogik.',
'- L37: 37 × 80 ms = **2,96 s links**, 0,56 s Chunk, 0,56 s rechts, **1,12 s algorithmische Latenz**. Buffered Streaming mit erneutem Linkskontext, kein Nemotron-3.5-Ersatz.',
'- Deutsche Prompt-ID aus den tatsächlichen Gewichten: **9**; Mel-Features **128**; Predictor **2 × 1 × 640** Zustände; **4095** SentencePiece-Tokens plus Blank-ID **4095**, insgesamt **4096** Joint-Ausgänge.', '',
'Der originale Exporter lief ohne funktionale Modell-/Exportpatches auf CPU erfolgreich durch. '
'Der erfolgreiche Job inklusive Graphdiagnose dauerte **2:43,01 min**, maximale RSS **10.754.496 KiB ≈ 10,26 GiB**, '
'138,02 s Nutzerzeit + 23,13 s Systemzeit, 0 Swaps, unter der 12-GiB-Grenze. '
'Protokoll: '+link('docs/evidence/phase4-export-job-cpu.log')+'; Exportdetails: '+link('models/L37-cpu/export.log')+'. '
'Der Status „exported-awaiting-validation“ im unveränderten Wrapper-Status beschreibt den Zwischenstand; die anschließende Diagnose und echte Runtime-Messung sind separat nachgewiesen.', '',
'| Komponente | Tatsächlich geprüft | Ergebnis |',
'|---|---|---|',
'| Encoder | ONNX-Checker, CPU-Ausführung, Feature-/Längen-/Prompt-Eingänge, L37-Metadaten, Rust-Inferenz auf echter Aufnahme | Bestanden |',
'| Predictor | ONNX-Checker, int32-Targets/-Längen, zwei Float-Zustände, endliche Ausgaben; zusätzlich echte Rust-Decodierung | Bestanden |',
'| Joiner | ONNX-Checker, CPU-Ausführung, 4096 Ausgänge; echte Decodierung | Bestanden |',
'| Tokenizer | Original-SentencePiece gegen alle Checkpoint-Vokabulareinträge und exportierte Tokenliste; Referenz-Roundtrip | Identisch |',
'| Sprache de | Prompt-ID 9 aus Checkpoint und Exportmetadaten; per-stream de in Rust | Bestanden |',
'| Rust-/C-Runtime | Metadatenprüfung und 18 vollständige echte STT-Läufe | Bestanden für diese Aufnahme |', '',
'Graphdiagnose: '+link('models/L37-cpu/component-diagnostics.json')+'. '
'Tokenizer-/Dateiaudit: '+link('docs/evidence/phase4-final-bundle-audit.log')+'. '
'Die Null-Feature-Komponentendiagnose allein wurde nicht als Sprache ausgegeben; der STT-Nachweis stammt ausschließlich aus der echten Aufnahme. '
'Eine vollständige numerische NeMo/ONNX-Paritätsprüfung über viele Fenster, längere Streaming-Sitzungen und ein FP32-vs-INT8-WER-Vergleich wurden nicht ausgeführt.', '',
'## INT8 und verwendbares Modellpaket','',
'**INT8 ist nicht nur vorbereitet, sondern erfolgreich erzeugt und verwendet.** '
'Der Graph enthält **265 MatMulInteger-Knoten** und **608.617.472 UINT8-Initializer-Elemente**. '
'Der Encoder hat weiterhin Float-Komponenten; Predictor und Joiner sind FP32. '
'Quantisierung gemäß PR: dynamisch, MatMul-Gewichte per-channel QUInt8. Ein Qualitätsdelta gegenüber FP32 wurde nicht gemessen.', '',
'Die vier Laufzeitdateien liegen unter '+link('models/L37-runtime','models/L37-runtime/')+'. '
'Sie sind Hardlinks zu den geprüften Exportdateien, keine zweite große Kopie. '
'Der INT8-Encoder benötigt keine externen Gewichtsdateien. Die FP32-Zwischendateien dagegen bleiben mit ihren externen Gewichten erhalten.', '',
'| Artefakt | Byte | SHA256 |','|---|---:|---|']
for name,info in audit['files'].items():lines.append(f'| {link("models/L37-runtime/"+name)} | {info["bytes"]} | `{info["sha256"]}` |')
lines += ['',f'Gesamt: **{audit["total_runtime_bytes"]:,} Byte / {audit["total_runtime_bytes"]/1024**2:.1f} MiB**. '
'Originalmodell und abgeleitete Dateien unterliegen **OpenMDW 1.1**; Lizenzkopie im Laufzeitverzeichnis. Keine Weiterveröffentlichung.', '',
'## Downloadbudget und tatsächlicher Speicherverbrauch','',
'- Originalmodell: exakt **2.507.735.040 Byte ≈ 2,336 GiB**, SHA256 '
'`1718cc1b44fb8597b2356328d706a8d89f31c389ca6f2256c2e3f743c0246936`; verifiziert, unter 2,34 GiB.',
'- Vor Wheel-Downloads alle 164 Paketgrößen geprüft: ursprünglicher Plan **532.436.580 Byte**. '
'Pakete einzeln auf Größe/SHA256 geprüft; keine ungeprüften großen Pip-Downloads.',
'- Mit Bootstrap/NeMo-Quellarchiv/zusätzlichem NumPy-Wheel sind rund **611,5 MB** Datei-Artefakte konservativ erfasst '
'(enthält auch lokale Kopien/gebautes ANTLR-Wheel). Zusätzlich Python-Image-Layer höchstens **47.685.311 Byte** komprimiert, vorab per Registry-Manifest geprüft.',
'- Mit weiteren **128 MiB Reserve** für Index-/Metadatenabrufe und kleinen Kompatibilitätsquelltexten bleibt die konservative Downloadrechnung bei rund **0,74 GiB**, deutlich unter 3 GiB. '
'Die tatsächliche komprimierte Netzübertragung wurde nicht paketgenau am Interface gemessen; Artefaktgrößen, Hashes und Reserve sind der Budgetnachweis.',
'- Entpackte Pakete und Exportdateien sind größer als Downloads: etwa **8,925 GB Modelle** und **2,994 GB Exportumgebung** logisch. '
'Dateisystembelegung der beiden Projektbereiche zusammen etwa **11,02 GB / 10,26 GiB** laut du; Hardlinks einmal gezählt.',
'- Freier Poolplatz nach Abschluss rund **329,2 GB / 306,6 GiB**. '
'Poolbelegung gegenüber der ersten Beobachtung um etwa **10,97 GB** gestiegen; diese Differenz enthält auch normalen Hintergrundbetrieb und ist keine exakte Alleinzuordnung.',
'- Keine unerwartete Eskalation des Speicherbedarfs; unter der zuvor angesetzten 40-GiB-Planungsreserve. '
'Originalgewichte, Fehlversuchslogs, Zwischengraphen und Downloadartefakte wurden nicht gelöscht.', '',
'Nachweise: '+link('export/reports/download-size-plan.json')+', '+link('export/reports/extra-downloads.jsonl')+', '
+link('export/reports/python-image-size.json')+', '+link('docs/evidence/phase4-resource-history.jsonl')+'.', '',
'## Aufgetretene Probleme und sichtbare Einschränkungen','',
'| Problem | Behandlung / tatsächlicher Status |','|---|---|',
'| ANTLR4 4.9.3 hat kein passendes fertiges Wheel | Kleines geprüftes Quellpaket (117.034 Byte) lokal im Container zum Wheel gebaut. |',
'| Metadatenresolver wollte einen Wheel-Body vom allgemeinen CPU-Index lesen | Guard blockierte dies; CPU-Findlinks auf Torch/Torchaudio beschränkt, übrige Pakete über PyPI-Metadaten. |',
'| PyArrow 26 mit NumPy 1.26 | Pip-Check war grün, tatsächlicher Import schlug fehl. NumPy 2.2.6 installiert und Lock/Freeze korrigiert; CPU-Import danach erfolgreich. |',
'| Python 3.11.2 unterstützt NeMos tarfile filter=data nicht | Erster Export vor Gewichts-Restore abgebrochen. Ein einzelner neuer tarfile-Modulversuch scheiterte ebenfalls an fehlendem os.path.ALLOW_MISSING. Beide Versuche erhalten. |',
'| Python-Kompatibilität | Vollständiges offizielles CPython 3.11.14 in separatem Exportimage; Traversal-Ablehnung und sichere Extraktion getestet. Keine Filterabschwächung im erfolgreichen Export. |',
'| NeMo warnt, dass [37,7,7] nicht in der Default-Lookahead-Liste [-1,-1,-1] steht | Setter übernimmt den Kontext trotzdem; entspricht dem PR-Exporter. L37-Metadaten und echte Erkennung geprüft, langfristige Streaming-Parität offen. |',
'| ONNX-Warnungen zu dynamischen Achsennamen, LSTM-Batch und Quantisierungs-Preprocessing | Keine unterdrückten Fehler: Batch 1 mit expliziten Zuständen und tatsächliche Runtime erfolgreich geprüft; keine Batch>1-Zusage. |',
'| Docker meldet fehlende Swap-Limit-Fähigkeit | RAM-Limit wirksam, Host ohne Swap und Job meldet 0 Swaps. Keine RAM-Grenze automatisch erhöht. |',
'| Vier Threads langsamer | Tatsächliche Messung, nicht herausgefiltert. Ursachenprofil und längere Audios offen. |',
'| Erste Teilhypothese fehlt | In allen 18 Läufen null; ausdrücklich keine erfundene Teiltranskript-Latenz. |', '',
'Fehler-/Prüfprotokolle: '+link('docs/evidence/phase4-offline-install.log')+', '
+link('docs/evidence/phase4-cpu-import-second.log')+', '+link('models/L37/export.log')+', '
+link('models/L37-attempt2/export.log')+', '+link('docs/evidence/phase4-python-upgrade-test.log')+'.', '',
'## Reproduktion und nächster sinnvoller Schritt','',
'Alle Downloads, venv und Quellen befinden sich im Projekt bzw. isolierten Docker-Layern. '
'Hostpakete, bestehende STT-Projekte/-Container und Home Assistant wurden nicht verändert. '
'Alle Jobcontainer sind beendet; es bleibt kein produktiver Dienst. '
'Die STT-Messung läuft über die Rust-CLI; eine reale Wyoming-Netzwerk-/HA-Integration wurde nicht getestet.', '',
'Erfolgreiches Exportimage: `nemotron-unified-export:phase4`, '
'`sha256:22f14cdb4aeac83c6370d4c849dc6fe4757989bd5f747dc9e8f2ea0531d4a1d0`. '
'Runtime weiterhin `nemotron-unified-wyoming:phase3`. '
'Reproduktionsdateien: '+link('export/Dockerfile')+', '+link('export/requirements.lock')+', '
+link('export/reports/installed.freeze.txt')+', '+link('export/run-export.sh')+'. '
'Die venv-Pakete werden beim Export read-only über den Projektpfad gefunden; das Image enthält nicht nochmals alle Pakete.', '',
'Den Benchmark aus der Projektwurzel mit einem **neuen** Ergebnisnamen wiederholen:', '',
'```sh',
'docker run --rm --network none --cpus 4 --memory 4g \\',
'  -v "$PWD:/work" -w /work nemotron-unified-development:pr4141 \\',
'  python3 scripts/benchmark.py --model /work/models/L37-runtime \\',
'  --manifest benchmarks/manifest.real.jsonl \\',
'  --output benchmarks/results/n100-l37-next.jsonl --repeats 3',
'```','',
'Für einen erneuten Export muss OUTPUT_DIR auf ein **neues** Unterverzeichnis gesetzt werden; der Wrapper verweigert vorhandene Ergebnisse. '
'Keine automatischen erneuten Modell-/Paketdownloads. Sinnvoll als nächster separater Schritt: mehrere längere menschliche deutsche Aufnahmen '
'und echte HA-Befehle, belastbare Streaming-Partial-Messung, FP32-/INT8-Qualitätsvergleich und Ursachenprofil für vier Threads. '
'Hier endet die Arbeit nach dem ersten echten Benchmark ohne produktive Bereitstellung.', '',
'## Alle 18 Einzelmessungen','',
'| Wiederholung | Threads | Pacing | RTF | Compute s | CPU % Prozess | Peak MiB | Transkript |',
'|---:|---:|---|---:|---:|---:|---:|---|']
for r in rows:
    lines.append(f'| {r["repeat"]+1} | {r["threads"]} | {"ja" if r["paced"] else "nein"} | {r["rtf"]:.3f} | {r["compute_seconds"]:.3f} | {r["process_cpu_percent_one_core_100"]:.1f} | {r["peak_rss_bytes"]/1024**2:.1f} | {r["hypothesis"]} |')
(base/'docs/PHASE4_RESULTS.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[lines.index('| Zuführung | Threads | RTF Ø | Compute s Ø | CPU % Prozess | Peak-RAM MiB | Final ab Start s Ø | Final nach audio-stop ms Median |'):][:8]))
