# Lizenzen und Herkunft

Eigener Projektcode: MIT, siehe ./LICENSE. Modellgewichte sind kein Bestandteil des Images und unterliegen **nicht** dieser MIT-Lizenz.

- NVIDIA Nemotron Labs Unified ASR 0.6B: Open Model, Data, and Weights License 1.1 (OpenMDW-1.1), Originaltext in models/L37-runtime/LICENSE.md und docs/evidence/phase4-model-LICENSE.md. Bei Weitergabe von Original oder quantisierten/exportierten Gewichten Lizenztext, Copyright- und Herkunftshinweise erhalten. Export und Quantisierung zusätzlich als Projekt-Herkunftsnotiz dokumentieren. Keine NVIDIA-Unterstützung oder Markenrechte behaupten. Maßgeblich ist der vollständige Modelllizenztext.
- sherpa-onnx und Rust/C-API: Apache-2.0, Commit 31ba0e438f8065189a8e5589d84dfd7faf516d3d. Einzige lokale Änderung: Versionsmetadaten in sherpa-onnx/csrc/version.cc auf den tatsächlichen Commit korrigiert, siehe scripts/stamp_native_version.py und /opt/sherpa/lib/SOURCE_PATCH im Image. Inferenzcode unverändert.
- ONNX Runtime: MIT; native Build-Abhängigkeiten haben eigene Lizenzen, unter anderem Apache-2.0, MIT, BSD und MPL-2.0 für Eigen. Die beim Build vorhandenen Original-Lizenzdateien und ONNX-ThirdPartyNotices werden im Image unter /usr/share/licenses/nemotron-wyoming/native gesammelt. MPL-Dateien stammen unverändert aus dem über sherpa CMake bezogenen Eigen-Quellarchiv; die jeweiligen Quellorte bleiben über den gepinnten sherpa-Quellcode nachvollziehbar.
- Rust-Abhängigkeiten: tatsächliche Cargo-Paketversionen, SPDX-Lizenzangaben und Quellorte unter /usr/share/licenses/nemotron-wyoming/rust-dependencies.json, dazu Original-Lizenzdateien unter /usr/share/licenses/nemotron-wyoming/rust. Betriebssystempakete: /usr/share/doc/*/copyright im Debian-Image.
- Wyoming-Python-Referenz ausschließlich für Tests: OHF-Voice/wyoming, MIT, Commit 08a0c258df83fea6e1643bcfe67e86243f01cf31. Unveränderte Referenzmodule und Original-Lizenz in tests/reference. Keine Python-Laufzeitabhängigkeit des Servers.
- Compose-Spezifikationsschema ausschließlich für Konfigurationstests: compose-spec/compose-spec, Apache-2.0; Originaltext in tests/reference/compose-spec.LICENSE.
- Menschliche Referenzaufnahme „Einsteigen bitte!“: Daniel Mietchen, Lingua Libre/Wikimedia Commons, CC0. Herkunft und Prüfsummen in docs/PHASE4_RESULTS.md. Nicht im Runtime-Image enthalten.

Vor einer Veröffentlichung müssen Modell-Lizenzdateien bei einer getrennten Modellbereitstellung erhalten bleiben. Es gibt keinen automatischen Gewichtsdownload und kein behauptetes öffentliches Container-Repository.

## Bereitgestellte Projekticons

assets/icons/nemotron-lowq.png und assets/icons/nemotron-hq.png sind die neu vom Nutzer bereitgestellten Nemotron-STT-Grafiken. Originale: icons/nemotron-stt-lowq.png und icons/nemotron-stt-hq.png (lokal, nicht versioniert). Sie wurden byteidentisch übernommen und zeigen visuell kein NVIDIA-Augenlogo, keinen NVIDIA-Schriftzug und keine ®-/™-Symbole. Die Produktbezeichnung Nemotron dient der Modellzuordnung; keine NVIDIA-Unterstützung, Partnerschaft oder Übertragung fremder Markenrechte wird behauptet. Der Nutzer beauftragt ihre Veröffentlichung als Projektgrafiken. Die frühere NVIDIA-Logo-Variante wurde im aktuellen Dateistand ersetzt; ihre alten Git-Blobs dürfen ohne geklärte Historienentscheidung nicht mitveröffentlicht werden.
