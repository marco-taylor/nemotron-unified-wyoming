# Phase 6 – neue Icons und Abschluss der Veröffentlichung

Stand: 02.11.2026. Hauptprojekt: /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming. Relative Pfade beziehen sich auf dieses Projekt.

## Aktueller Status

Die neuen Nemotron-STT-Icons sind geprüft und im aktuellen Projektstand ersetzt. Das neu angelegte öffentliche Repository https://github.com/marco-taylor/nemotron-unified-rust-wyoming ist erreichbar (HTTP 200), öffentlich und noch leer. Branch lokal main, origin unverändert git@github.com:marco-taylor/nemotron-unified-rust-wyoming.git. Der vorhandene SSH-Zugang funktioniert; die GitHub-Anbindung meldet Admin-/Push-Rechte.

**Vor dem ersten Push ist eine Historienentscheidung erforderlich.** Die lokalen Phase6-Commits enthalten die alten NVIDIA-Logo-Bilder. Ein neuer Icon-Commit allein entfernt sie nicht aus früheren öffentlich abrufbaren Commits. Gleichzeitig verlangt der Auftrag den Erhalt der bisherigen Historie und keine alten Logos im öffentlichen Projekt. Ohne ausdrückliche Entscheidung wird weder die Historie umgeschrieben noch der alte Logo-Bestand mitveröffentlicht. Eine Rückfrage dazu wurde gestellt. Kein Force-Push und kein offizieller Release.

## Neue Icons

| Variante | Unveränderte Quelldatei | Aktuelle Repositorydatei | Größe | Format / Abmessungen | Transparenz |
|---|---|---|---:|---|---|
| HQ | icons/nemotron-stt-hq.png | assets/icons/nemotron-hq.png | 1.560.271 Byte | PNG RGBA, 1254 × 1254 | ja, Alpha bis 0 |
| Low-Q | icons/nemotron-stt-lowq.png | assets/icons/nemotron-lowq.png | 82.756 Byte | PNG RGBA, 256 × 256 | ja, Alpha bis 0 |

Beide Grafiken visuell geprüft: Mikrofon, Audiosignal, grüne Dekoration und „Nemotron STT“. Kein NVIDIA-Augenlogo, NVIDIA-Schriftzug oder ®-/™-Symbol erkennbar. Die Bezeichnung Nemotron dient der Modellzuordnung, ohne behauptete NVIDIA-Unterstützung. Die visuelle Prüfung ist keine pauschale Garantie über sämtliche möglichen Markenrechte; der Nutzer hat diese Ersatzgrafiken zur Veröffentlichung bereitgestellt.

Bildintegrität: PNG-Signatur, sämtliche Chunk-CRCs, zlib-Dekompression, Scanline-Längen und PNG-Filterrekonstruktion erfolgreich. Kopien sind byteidentisch mit den neuen Quelldateien; diese bleiben unverändert. Low-Q liegt unter 100 KB und hat die bevorzugten 256 × 256 Pixel, daher keine erneute Komprimierung.

SHA256 HQ: `ebc6f304d492a6523d5afebf8d21faf87f9a6d10d5ee362e924bfa2ead1a5b25`.
SHA256 Low-Q: `242a931bd2c14dfc05a8bbbee544120ede39845a97350146a11c552c299d077b`.

**Ausschließlich Low-Q** ist in config/unraid-template.xml und im Docker-Image-Label net.unraid.docker.icon als Standard eingetragen. HQ ist nur zusätzliche Grafik. Alle aktiven Iconreferenzen verwenden die bestehenden kanonischen Pfade; keine neue NVIDIA-Logo-Datei wird in den aktuellen Git-Index aufgenommen. Der lokale Originalordner icons/ bleibt ignoriert.

Konfigurierte Low-Q-URL, erst nach dem Push öffentlich verfügbar:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/assets/icons/nemotron-lowq.png

HQ-Alternative:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/assets/icons/nemotron-hq.png

Öffentliche Vorlage:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/config/unraid-template.xml

Die Migration bestehender Unraid-Iconmetadaten ist in docs/UNRAID.md beschrieben. Im Auftrag wurden keine produktiven Metadaten, Caches, Container oder Vorlagen außerhalb des Projekts verändert. CA-Aufnahme ist ein zusätzlicher Vorgang, keine automatische Folge eines GitHub-Pushs.

## Erhaltene Historie und Audit

Unverändert vorhandene lokale Ausgangscommits:

- `40a5730519edc03b32b00f72936902d092cadceb` – ursprünglicher auditierter Projektstand.
- `00dc22118d986d1c03d9d10a002661213a49e107` – Phase6-Quell-/Icon-/Identitätsänderungen mit den alten Bildern.
- `8b2e80dc0dae772dfa4aaa5f4ab91a3c06cdf5ba` – Phase6-Berichtscommit.

Der zweite Commit enthält weiterhin die alten Logo-Blobs. scripts/audit_publication.py akzeptiert im aktuellen Index ausschließlich die beiden neuen, exakt per SHA256 geprüften PNGs. Bekannte alte Bildhashes werden ausdrücklich als Veröffentlichungsfehler erkannt, auch unter einem anderen Dateipfad. --history prüft die tatsächlich zu veröffentlichende HEAD-Abstammung; --history --all-refs prüft zusätzlich alle lokalen Sicherungs-/Nebenrefs. Eine nur lokal gesicherte alte Historie darf nicht als zusätzliche Branch/Tag mitgepusht werden.

Secrets-/Key-/Tokenmuster, verbotene Dateitypen/-pfade, Binärdateien und übergroße Dateien werden geprüft. Ausnahme nur für die geprüften Iconkopien. Modelle, lokale Konfigurationen, Exportdownloads, Buildprodukte und rohe Prüfbelege bleiben ignoriert. ./.dockerignore ist eine Positivliste und schließt Git, Icons, Modelle und lokale Auth-Dateien aus dem Imagekontext aus.

Keine Gewichte oder Nutzer-Zugangsdaten im bisherigen Index-/Quellhistorienaudit gefunden. Der aktuelle Historienaudit muss wegen der bekannten alten Logos fehlschlagen, bis die Historienfrage geklärt ist. Der Audit wird nicht durch pauschales Zulassen der alten PNGs umgangen.

## Qualität und 19 Variablen

Rust-Quellen und Serverkonfiguration werden durch diesen Iconaustausch nicht verändert. Alle **19 wirksamen Variablen** bleiben erhalten: PUID, PGID, WYOMING_HOST, WYOMING_PORT, LANGUAGE, STT_DEVICE, MODEL_DIR, ENCODER_PATH, DECODER_PATH, JOINER_PATH, TOKENS_PATH, THREADS, MAX_AUDIO_SECONDS, MAX_AUDIO_CHUNK_BYTES, MAX_CONNECTIONS, CLIENT_TIMEOUT_SECONDS, INFERENCE_CHUNK_MS, LOG_LEVEL, LOG_TRANSCRIPTS.

17 Variablen verarbeitet Rust, PUID/PGID der echte Entrypoint. Defaults 99:100, CPU, Deutsch und zwei ORT-Threads bleiben unverändert. Keine neuen Tuningvariablen. Read-only-Modelle, NoNewPrivs, kein automatisches chown/chmod und der unprivilegierte Serverbetrieb bleiben erhalten.

Der vorherige Phase6-Stand bestand cargo fmt --check, strenges Clippy, 33 native Rust-Tests, zusätzlich 32 Tests ohne sherpa, Release-/Docker-Build, Konfigurationsvalidierung, PUID-/PGID-Tests, Runtime-Preflight, Wyoming-Integration und sechs echte L37-Transkriptionen „Einsteigen bitte.“. Belege unter docs/evidence/phase6-current/; keine vollständige neue Sprachqualitätsabnahme behauptet.

Für die neuen Grafiken werden Konfigurations-/Icon-Parität, Publikationsaudit und Docker-Build erneut geprüft. Der Docker-Build führt Release-Kompilierung, fmt, alle 33 Tests und strenges Clippy erneut aus. Da die Lizenzhinweise im Image aktualisiert werden, wird auch der Runtime-Preflight auf dem neuen Image wiederholt. Aktuelle Ergebnisse stehen im abschließenden lokalen Testnachweis unten. Keine Modellgewichte heruntergeladen.

## Lizenzen

Eigener Code MIT; sherpa-onnx Apache-2.0; ONNX Runtime MIT; Modell getrennt OpenMDW-1.1. Vollständige Hinweise in ./THIRD_PARTY_NOTICES.md und docs/MODELS.md. Beim vorherigen Audit 28 Rust-Pakete ohne fehlende Lizenzangaben; native Original-Lizenztexte und Debian-Copyrights bleiben im Image erhalten. Keine Modellgewichte werden verteilt. Die neuen Bilder ersetzen den früheren Logo-Rechteblocker im aktuellen Dateistand; der alte Logo-Bestand in der Git-Abstammung ist noch gesondert zu lösen.

## GitHub Actions und GHCR

Quellziel: https://github.com/marco-taylor/nemotron-unified-rust-wyoming.
Imageziel: `ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:dev`, Plattform linux/amd64. Zusätzlich geplanter reproduzierbarer `sha-COMMIT`-Tag. Kein latest-/v1.0.0-Tag und kein offizieller GitHub-Release.

./.github/workflows/ci.yml validiert Konfiguration/Index/Historie und baut/testet das Image. ./.github/workflows/publish-ghcr.yml prüft vor dem Push Architektur, CLI und das exportierte Runtime-Dateisystem, nutzt GITHUB_TOKEN mit packages:write und veröffentlicht dev plus Commit-Tag. Actions sind auf Commit-SHAs gepinnt. Der erste erlaubte Push nach main löst die Workflows aus. Bis zur Historienentscheidung wurde kein Push oder Cloudworkflow ausgelöst.

Nach dem Push zu prüfen: erfolgreicher Workflow, beide Raw-PNGs mit SHA256, XML mit ausschließlich Low-Q, öffentliches linux/amd64-Manifest, anonymer tatsächlicher Image-Pull und Runtime-Audit. Ein erfolgreiches Registry-Push allein beweist noch keine öffentliche Paketsichtbarkeit.

## Bereinigung aus der vorherigen Phase6-Ausführung

Der neue Iconauftrag löscht keine weiteren Cache-/Modell-/Forschungsdateien. Der erhaltene vollständige Lösch-Nachweis der vorherigen Ausführung steht in docs/PHASE6_CLEANUP.json: 3.394 regenerierbare Dateien, 1.074.053.320 Byte logische Größe und 447.635.456 Byte erfasste Dateiblockbelegung. Kein separat gemessener Netto-Poolgewinn; Snapshots/Kompression können abweichen. Der Release-Benchmark-Binärpfad bleibt erhalten. Keine Docker-Volumes oder Dateien anderer Projekte gelöscht.

## Offene Punkte

1. Entscheidung zur alten Icon-Historie: öffentlich bereinigte Abstammung mit unverändert lokaler Sicherung oder ausdrückliche neue Vorgabe für die Altbilder. Keine eigenmächtige Geschichtsänderung.
2. Danach Veröffentlichung nach main, Actions-/GHCR-Erfolg, echte Pullbarkeit und öffentliche Raw-Dateien bestätigen.
3. Vor Version 1.0.0: repräsentative deutsche Befehle, Assist-/Satellite-Abnahme, Langzeit-/Lasttest und mögliche CA-Einreichung. Internes Endpointing/VAD, Wyoming-Teiltranskripte, alternative L37-Kontexte und GPU sind weiterhin nicht implementiert.

Aktuelle Rohbelege lokal unter docs/evidence/phase6-icons/. Die unabhängigen lokalen Prüfungen sind abgeschlossen. Veröffentlichung bleibt bis zur Historienentscheidung gestoppt.

## Abschließender lokaler Testnachweis für die Ersatzicons

- Docker-Build linux/amd64 erfolgreich, einschließlich Release-Build, cargo fmt --check, 33 bestandenen Tests und Clippy mit -D warnings.
- Schema-/XML-/Workflowprüfung erfolgreich; alle 19 Variablen unverändert, Low-Q alleiniger Standard.
- Runtime-Preflight erfolgreich: CLI, fehlende Modelle, ungültige Konfiguration, beschädigter Decoder, native Libraries und Lizenztexte.
- Runtime-Audit: 3.548 Dateien, keine Modellgewichte, keine unbekannten Credentialmuster. Exakt geprüfte öffentliche GnuTLS-Selbsttestschlüssel weiterhin separat ausgewiesen.
- Serverbinärhash identisch zum zuvor erfolgreich auf PUID/PGID, Healthcheck und echter L37-Inferenz geprüften Stand: `4e01f66bb940238a5941272f59a7463d4275aa0f246c6114844db06881a5e260`.
- Aktueller Git-Index: 114 Dateien, keine Secrets/Modelle/Buildartefakte oder alten Logobilder. Historienaudit meldet ausdrücklich die zwei Altbilder in der bestehenden Abstammung und sperrt den Push.
- Alle 31 Bestandscontainer nach IDs, Konfiguration, Startzeiten und Restart-Zählern unverändert; nemotron-unified-stt weiterhin healthy. Eigene temporäre Prüfcontainer entfernt.

Lokales Image: `nemotron-unified-rust-wyoming:phase6-new-icons`, sha256:474faf489a4d3a398a6911b93b121805c370931f7d26dd8da3b3274e65fd694c, 117.491.819 Byte, linux/amd64. Der produktive Image-Tag wurde nicht verändert. Die Quelldateien und kopierten PNGs stimmen weiterhin bytegenau überein.

GitHub Actions: 0 Läufe im noch leeren Repository. Kein Workflow gestartet, kein GHCR-Push und kein anonymer Pull eines neuen dev-Images behauptet. Der frühere Repository-Erstellungsblocker ist behoben; verbleibender Blocker ist ausschließlich die widersprüchliche Vorgabe zur alten Logo-Historie.

Geprüfter lokaler Quellcommit der Ersatzicons: `ef5b6b6d548bf23f11e0d45a5dedda816bb950a1`. Ein folgender reiner Berichtscommit ergänzt diesen Nachweis. Noch kein veröffentlichter Commit und kein GHCR-Digest.
