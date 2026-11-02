# Modellbeschaffung und ONNX-Export

Alle Pfade relativ zum Projektverzeichnis. Verwendet wird ausschließlich [NVIDIA Nemotron Labs Unified ASR 0.6B](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b), nicht Nemotron 3.5. Der funktionierende lokale Export und der zugehörige native Code stammen aus [sherpa-onnx PR #4141](https://github.com/k2-fsa/sherpa-onnx/pull/4141), exakt Commit `31ba0e438f8065189a8e5589d84dfd7faf516d3d`. Es wird absichtlich kein späteres ungeprüftes Releasepaket eingesetzt.

## Vorhandener Runtime-Satz

models/L37-runtime ist bereits vorhanden und benötigt keinen erneuten Download/Export. Vier zur Laufzeit benötigte Dateien:

| Datei unter models/L37-runtime | Byte | SHA256 |
|---|---:|---|
| encoder.int8.onnx | 675328677 | `8e1b140b85900dcaede7e5fc05c1adfd48d4a0585e3b55ec2a10cded7042c96d` |
| decoder.onnx | 36745480 | `e5281215d86116e425191324830090922ec7732a34b1f5203d3b5a3564a20d97` |
| joiner.onnx | 14768802 | `7abd80133827b59dbd3b57c47242d6001607ed14acda5db36ae28d64a3de8af8` |
| tokens.txt | 42928 | `94139a0b2134fd40664ca72260026fa8a073336bb2f062239c8ecde2c8031763` |

Lizenztext und Herkunft neben den Gewichten aufbewahren. OpenMDW-1.1 ist getrennt von der MIT-Code-Lizenz; siehe ./THIRD_PARTY_NOTICES.md. Das Image enthält keine Modellgewichte. Kein Serverkommando lädt Modelle nach.

L37 bedeutet links37 Encoderframes, Chunk7, rechts7 bei 80 ms Encoderframe: 2,96 s linker Kontext und 1,12 s algorithmische Chunk-/Rechtskontextlatenz. Die Aufnahme muss deshalb nicht gepolstert werden: `input_finished` und die echte Unified-Runtime erledigen EOF. Encoder teilweise QUInt8, 265 MatMulInteger-Knoten; Decoder/Joiner bleiben FP32. Kein behauptetes vollständig ganzzahliges Modell.

Startprüfung: vier nichtleere lesbare Dateien, gültige L37-/Unified-/Deutsch-Metadaten, tatsächlicher nativer Commit und SOURCE_COMMIT. ORT erstellt anschließend alle drei Graphsessions. Ein bereit gemeldeter Server hat das Modell geladen; `check-model` allein ist keine vollständige Graphprüfung. Grundlegende ONNX-/Tokenizer-Kompatibilität wurde in Phase4 separat geprüft und mit echter Inferenz bestätigt: export/reports/final-bundle-audit.json und docs/PHASE4_RESULTS.md.

## Reproduktion des Exports

Der Originalcheckpoint unter models/source/nemotron-labs-unified-asr-0.6b.nemo ist 2.507.735.040 Byte groß, SHA256 `1718cc1b44fb8597b2356328d706a8d89f31c389ca6f2256c2e3f743c0246936`. Er wurde mit Freigabe heruntergeladen. Größen-/Hashprüfung übernimmt scripts/download_bounded.py; vor neuen umfangreichen Downloads Größe, freien Speicher und Freigabe erneut prüfen. Kein erneuter Download in Phase5.

Der aktuelle CPU-Export funktioniert ohne NVIDIA-GPU. export/Dockerfile verwendet isoliertes CPython 3.11.14 und die projektbezogene Offline-venv. Reproduzierbare Abhängigkeiten: export/requirements.lock, export/reports/installed.freeze.txt und export/reports/working-artifacts.json; nicht ungebremst NeMo/torch samt CUDA nachinstallieren. Der vorbereitete Exportjob ist export/run-export.sh.

Wenn die vorhandenen Exportabhängigkeiten und das Exportimage bereits vorhanden sind, nur in ein **neues** Ziel exportieren:

```sh
cd /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming
OUTPUT_DIR=/work/models/L37-reproduction sh export/run-export.sh
```

Der Wrapper scripts/export_l37.py prüft Checkpointgröße/Hash und Exportercommit, verlangt konservativ 40 GiB freien Platz, verweigert bestehende Zielverzeichnisse und startet den tatsächlichen Exporter `scripts/nemo/nemotron-labs-unified-asr-0.6b/export_onnx.py` des gepinnten sherpa-Quellbaums mit `--left-context 37`. Netzwerk im Job ist ausgeschaltet. Der anschließende export/validate_bundle.py-Test prüft Graphen/ABI. Separater Tokenizertest: scripts/check_tokenizer.py, Bundle-/Quantisierungsprüfung: scripts/audit_int8_bundle.py. Deren tatsächliche Aufrufe/Ergebnisse sind in docs/PHASE4_RESULTS.md und export/reports dokumentiert.

Nicht aus derselben Konfiguration stammende Encoder, Decoder, Joiner und Tokenizer nicht mischen. Exportdateien nicht beim Serverstart erzeugen. Für einen anderen Host zuerst den vorhandenen Runtime-Satz mit Lizenz und Herkunft kopieren, Hashes prüfen und im finalen Image einen echten Sprachtest ausführen. Änderungen am Exporter oder nativen Commit benötigen erneute Kompatibilitäts- und Spracherkennungstests.
