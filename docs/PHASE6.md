# Phase 6 – geprüfte Sicherung und erfolgreiche Veröffentlichung

Stand: 02.11.2026. Hauptprojekt: /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming. Relative Pfade beziehen sich auf dieses Projekt.

**Abgeschlossen:** vollständige lokale Historie gesichert und wiederhergestellt geprüft, bereinigte öffentliche main-Historie veröffentlicht, beide GitHub-Actions-Läufe erfolgreich, GHCR-dev-Image anonym heruntergeladen und tatsächlich mit vorhandenen Modellen getestet. Kein offizieller v1.0.0-Release, kein Force-Push und keine Änderung produktiver Container.

## GitHub, alter und neuer Commit

Repository: https://github.com/marco-taylor/nemotron-unified-rust-wyoming

| Stand | Vollständige SHA / Referenz |
|---|---|
| Alter lokaler Ausgangscommit | `c5da1bed933b417bcf4e59478240285eae717f05` |
| Neue öffentliche Wurzel ohne Eltern | `e62d4dab329e49e00a041e09912133fe77999c9d` |
| Öffentlich geprüfter Image-Quellcommit | `6e2cd9e4112e5211f0c934483e65fca21c12ae13` |
| Ausschließlich lokaler Archivbranch | `archive/phase6-before-public` → alter Ausgangscommit |

Die neue Wurzel hat exakt denselben Git-Tree wie der freigegebene Ausgangscommit: alle 114 geprüften Dateien einschließlich Quellen, Cargo-Dateien, Docker-/Unraid-Konfiguration, Dokumentation, Skripten und neuen Icons sind erhalten. Alte Logo-Bilder waren dort bereits ersetzt. Die neue Wurzel übernimmt keine Eltern und damit keine früheren Bildversionen. Die alten fünf Commits wurden nicht gelöscht.

Veröffentlicht wurde ausschließlich refs/heads/main mit normalem Push. Auf GitHub gibt es keinen Archivbranch und keine Release-Tags. Ein frisch von GitHub geklontes Mirror-Repository bestand git fsck und den vollständigen HEAD-Historienaudit ohne Treffer. Die öffentliche GitHub-API findet den alten Ausgangscommit nicht („No commit found for SHA“). Nachfolgende reine Berichtsänderungen bauen auf der sauberen öffentlichen Historie auf; der Image-Quellcommit bleibt der oben genannte erfolgreich geprüfte Stand. Der abschließende Berichtscommit verwendet [skip ci], da keine Image-/Runtime-Quelle geändert wird.

## Vollständiges Backup und Wiederherstellungsprüfung

Git-Bundle außerhalb des Projektverzeichnisses:

`/mnt/nvme/appdata/codex-workspace/nemotron-phase6-git-backup-qzC0ZgJz/history.bundle`

SHA256: `99802f1ce1ff375a16a3af5edf4e3925ecfa7fa8b12d7f7caac8f9b87bf528eb`.

Vor jeder main-Umstellung sicherte git bundle create --all sämtliche damaligen Branches, Tags und alle fünf erreichbaren Commits einschließlich der Phase6-Commits. Es gab einen Branch main und keine Tags. git bundle verify bestätigte vollständige Historie ohne Voraussetzungen.

Wiederhergestellt als separates Mirror-Repository:

`/mnt/nvme/appdata/codex-workspace/nemotron-phase6-git-backup-qzC0ZgJz/restore-check.git`

Git fsck erfolgreich. Vollständige Referenzlisten und gesamte erreichbare Commitlisten zwischen Quelle und Wiederherstellung sind exakt gleich; der wiederhergestellte main zeigt auf c5da1bed933b417bcf4e59478240285eae717f05. Referenzlisten, Commitlisten, Prüflogs und Bundle-Prüfsumme liegen im selben Backupverzeichnis. Die Sicherung wurde vor der Umstellung geprüft; zusätzlich bleibt die ursprüngliche Historie im lokalen Archivbranch erhalten. Weder Bundle noch Archivbranch wurden veröffentlicht.

## Neue Icons und Low-Q-Standard

| Variante | Unveränderte Quelldatei | Öffentliche Datei | Größe | Eigenschaften |
|---|---|---|---:|---|
| Low-Q | icons/nemotron-stt-lowq.png | assets/icons/nemotron-lowq.png | 82.756 Byte | PNG RGBA, 256 × 256, transparent |
| HQ | icons/nemotron-stt-hq.png | assets/icons/nemotron-hq.png | 1.560.271 Byte | PNG RGBA, 1254 × 1254, transparent |

Beide Grafiken visuell geprüft: Mikrofon, Audiosignal, grüne Dekoration und „Nemotron STT“. Kein NVIDIA-Augenlogo, NVIDIA-Schriftzug oder ®-/™-Symbol erkennbar. Die Produktbezeichnung dient der Modellzuordnung; keine NVIDIA-Partnerschaft oder Unterstützung wird behauptet. Neue Quelldateien vom Nutzer zur Veröffentlichung bereitgestellt; unverändert lokal erhalten.

PNG-Signatur, alle Chunk-CRCs, zlib-Dekompression, Scanline-Längen und Filterrekonstruktion erfolgreich geprüft. Alpha erreicht bei beiden Bildern 0. Low-Q erfüllt unter 100 KB und mit 256 × 256 die Vorgaben; keine erneute Komprimierung. Original und Kopie stimmen jeweils bytegenau überein.

SHA256 Low-Q: `242a931bd2c14dfc05a8bbbee544120ede39845a97350146a11c552c299d077b`.
SHA256 HQ: `ebc6f304d492a6523d5afebf8d21faf87f9a6d10d5ee362e924bfa2ead1a5b25`.

**Low-Q ist der einzige Standard** in config/unraid-template.xml und im Docker-Image-Label net.unraid.docker.icon. Das heruntergeladene GHCR-Image wurde darauf geprüft. HQ bleibt ausschließlich zusätzliche Grafik.

Öffentliche Low-Q-URL:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/assets/icons/nemotron-lowq.png

HQ-Alternative:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/assets/icons/nemotron-hq.png

Unraid-Template:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/config/unraid-template.xml

Alle drei Raw-Dateien erfolgreich heruntergeladen und bytegenau mit dem lokalen Stand verglichen. Keine alten Bildpfade als aktive Standardreferenz. Migration gespeicherter Unraid-Iconmetadaten: docs/UNRAID.md. Keine bestehende Vorlage, kein DockerMan-Cache und kein Container wurden automatisch verändert. Eine Community-Applications-Aufnahme ist ein separater Vorgang und wird durch die Veröffentlichung nicht behauptet.

## Sicherheits- und Lizenzprüfung

scripts/audit_publication.py prüft aktuellen Index und sämtliche Blobs der veröffentlichten HEAD-Abstammung auf Secrets-/Key-/Tokenmuster, Modell-/Builddateien, verbotene Pfade, Binärdateien und übergroße Dateien. Ausschließlich die zwei exakt per SHA256 geprüften neuen PNGs sind als Bildausnahme zugelassen. Die beiden alten NVIDIA-Logo-Hashes sind ausdrücklich gesperrt. Prüfung vor Push und erneute Prüfung eines frischen öffentlichen Klons ohne Treffer. Der lokale Archivbranch ist ausdrücklich nicht Teil der öffentlichen Abstammung.

./.gitignore schließt Modelle, Audio-/Benchmark-Rohdaten, Exportumgebungen, Buildprodukte, lokale Konfigurationen und Credentials aus. Der Originalordner icons/ bleibt lokal ignoriert. ./.dockerignore ist eine Positivliste und schließt Modelle, Git, Icons sowie lokale Auth-Dateien aus dem Buildkontext aus. Kein Credential wurde in Git oder Buildargumente übernommen.

Runtime-Audit des tatsächlich anonym heruntergeladenen GHCR-Images: **3.548 Dateien**, keine Modellgewichte, keine unbekannten Credentialmuster. Bekannte öffentliche GnuTLS-Selbsttestschlüssel sind nur für eine exakt per SHA256 geprüfte unveränderte Debian-Bibliothek ausgenommen. Die sechs PEM-Testblöcke wurden zuvor mit dem offiziellen Quelltext unter https://github.com/gnutls/gnutls/blob/3.7.9/lib/crypto-selftests-pk.c verglichen. Keine privaten Nutzer-/Deployment-Schlüssel. Musterprüfungen sind kein vollständiger externer CVE-/Security-Audit.

Eigener Code MIT, sherpa-onnx Apache-2.0, ONNX Runtime MIT, Modell getrennt OpenMDW-1.1. Keine Modellgewichte werden verteilt. Original-Lizenztexte, Herkunft und native/Rust-Abhängigkeitslizenzen bleiben erhalten; 28 Rust-Pakete ohne fehlende Lizenzangaben im bisherigen Inventar. Eigen MPL-2.0 bleibt unverändert mit nachvollziehbarem Quellort. Einzelheiten: ./THIRD_PARTY_NOTICES.md und docs/MODELS.md. Keine verbleibende bekannte Lizenz-/Icon-Veröffentlichungssperre für diesen Umfang.

## Alle 19 wirksamen Variablen

PUID, PGID, WYOMING_HOST, WYOMING_PORT, LANGUAGE, STT_DEVICE, MODEL_DIR, ENCODER_PATH, DECODER_PATH, JOINER_PATH, TOKENS_PATH, THREADS, MAX_AUDIO_SECONDS, MAX_AUDIO_CHUNK_BYTES, MAX_CONNECTIONS, CLIENT_TIMEOUT_SECONDS, INFERENCE_CHUNK_MS, LOG_LEVEL, LOG_TRANSCRIPTS.

17 verarbeitet Rust, PUID/PGID der tatsächliche Entrypoint. Defaults 99:100, Deutsch, CPU, zwei ORT-Threads bleiben erhalten. Referenz: config/variables.json und docs/PHASE5_2.md. Compose-Schema, XML, beide Beispieldateien und alle 19 Felder wurden lokal sowie in GitHub CI geprüft. Keine neue wirkungslose Variable.

Das veröffentlichte Image wurde tatsächlich mit PUID=99/PGID=100 und Environment-only-Override 12345:23456 geprüft. Server-PID 1 standardmäßig in allen UID-/GID-Feldern 99:100, keine Zusatzgruppen, CapPrm/CapEff/CapAmb 0, NoNewPrivs=1. Bereits unprivilegierter Start mit passenden IDs ohne Capabilities funktioniert. Ungültige IDs und widersprüchlicher Docker-user liefern verständliche Fehler. Keine automatischen chown/chmod-Aktionen; Modelle read-only.

## GitHub Actions und Testergebnisse

Geprüfter Quellcommit beider Läufe: `6e2cd9e4112e5211f0c934483e65fca21c12ae13`.

| Workflow | Ergebnis | Öffentlicher Lauf |
|---|---|---|
| Build and test | erfolgreich | https://github.com/marco-taylor/nemotron-unified-rust-wyoming/actions/runs/41456410751 |
| GHCR development image (linux/amd64) | erfolgreich einschließlich Upload | https://github.com/marco-taylor/nemotron-unified-rust-wyoming/actions/runs/41456410692 |

Cloud-Ergebnisse: cargo fmt --check, cargo clippy --locked --all-targets --features sherpa -- -D warnings, **33 bestandene Rust-Tests**, Release-Build und Docker-Build erfolgreich. Darin Unit-/Konfigurations-/TCP-/offizielle Wyoming-Python-Interop-/Shutdownprüfungen. Schema-/XML-/Workflowvalidierung und Index-/Historienaudit grün. GHCR prüfte vor dem Upload Architektur, CLI und das vollständige Runtime-Dateisystem. GITHUB_TOKEN ausschließlich im Runner mit packages:write; kein Token im Repository oder Image.

Auf dem tatsächlich heruntergeladenen GHCR-Image erneut erfolgreich: scripts/runtime-preflight-tests.sh und scripts/test-identity.sh. CLI, fehlende Modelle, ungültige Threads/IDs, beschädigter Decoder, Zugriff-verweigert-Modellpfad, native Libraries/Lizenztexte, Identitätswechsel, Capabilities, Healthcheck und geordneter Shutdown geprüft.

Echte lokale L37-Inferenz mit vorhandenen read-only Modellgewichten unter 99:100: dreimal **„Einsteigen bitte.“** aus der vorhandenen menschlichen CC0-Aufnahme (1,50025 s). Anfragezeiten 1,695 / 2,087 / 1,637 s unter dem isolierten 2-CPU-Testlimit. Keine neuen Gewichte oder Audiodateien heruntergeladen. Dieser kurze Test belegt die technische Kette, keine allgemeine deutsche Befehlsqualität oder neue umfassende Performanceabnahme. Frühere Nichtstandard-Konfigurationstests und 32 Tests ohne sherpa bleiben in docs/PHASE5_2.md bzw. lokalen Phase6-Belegen dokumentiert.

Kernelwarnung über fehlende Swap-Limit-Unterstützung wie zuvor; RAM-Limit bleibt wirksam. Keine funktionale Abweichung gegenüber dem geprüften Phase5.2-/Ersatzicon-Stand festgestellt. Die Cloudbuilds sind nicht als bitidentische Offline-Rebuilds behauptet: Basis-/Cargo-/sherpa-Versionen sind gepinnt, apt und Validierungs-Transitivabhängigkeiten nicht vollständig eingefroren.

## GHCR-Veröffentlichung und tatsächlicher Download

Image: `ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:dev`.

Unveränderlicher Quelltag: `ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:sha-6e2cd9e4112e5211f0c934483e65fca21c12ae13`.

Beide Tags zeigen auf:

`sha256:7f758ff370c45ce07b55c9d761be13b1b422643748d423cd1535d1398a1caa6d`

**Beide Tags wurden anonym mit leerer Docker-Client-Konfiguration tatsächlich gepullt**, der dev-Tag einschließlich Layerdownload. Plattform linux/amd64 bestätigt. Image-ID sha256:1d7f7d5a309b2e15787a6f665f1fab8982c0d1a881d334458bdf53d39b71940d, lokale entpackte Imagegröße 116.748.638 Byte. Revisionlabel entspricht dem geprüften Quellcommit, Unraid-Iconlabel ausschließlich Low-Q. Keine Modellgewichte oder unbekannten Credentials im exportierten Image.

Keine bestehenden lokalen Produktiv-Image-Tags umgebogen. Kein produktiver Container neu erstellt oder neu gestartet, kein automatisches Deployment, kein GitHub-Release und kein v1.0.0-Tag.

## Containerkontrolle und Bereinigung

Alle **31 Bestandscontainer** wurden vor/nach Veröffentlichung und Tests nach ID, Config, HostConfig, Startzeit, Running-Status und Restart-Zähler verglichen: keine Änderungen. nemotron-unified-stt weiterhin **healthy**. Eigene eindeutig benannte Test-/Auditcontainer kontrolliert entfernt. Keine Hostports veröffentlicht, keine Docker-Volumes gelöscht und keine HA-Konfiguration geändert.

In diesem Veröffentlichungsauftrag keine zusätzlichen Projektdateien oder Modelle gelöscht. Die erhaltene frühere Bereinigungsbilanz steht vollständig in docs/PHASE6_CLEANUP.json: 3.394 regenerierbare Dateien, 1.074.053.320 Byte logische Größe, 447.635.456 Byte erfasste Dateiblockbelegung. Kein separat gemessener Netto-Poolgewinn; Kompression/Snapshots können abweichen. Release-Benchmark-Binärpfad, Forschungsdaten, alte lokale Belege und Modellbestände bleiben erhalten. Keine anderen Workspace-Projekte verändert. Das ausdrücklich angeforderte Backup liegt in einem eigenen neuen Verzeichnis außerhalb des Projekts.

## Noch offen vor Version 1.0.0

Keine verbleibenden Blocker für die hier geprüfte GitHub-/GHCR-dev-Veröffentlichung. Offen bleiben repräsentative deutsche Befehlsqualität, gemeinsame Home-Assistant-/Satellite-Abnahme, Langzeit-/Lasttest und eine gesonderte CA-Einreichung. Internes Endpointing/VAD, Wyoming-Teiltranskripte, alternative L37-Kontexte und GPU-Provider sind weiterhin nicht implementiert. Offizieller v1.0.0-Release nur nach gesondertem Auftrag.

Lokale, bewusst nicht veröffentlichte Rohbelege: docs/evidence/phase6-publication/ (Cloudlogs, frischer öffentlicher Historienaudit, Raw-Dateivergleich, anonyme Pulls, Imageaudit, Identitäts-/Inferenztests und Containervergleich). Frühere Belege bleiben unter docs/evidence/phase6-icons/ und docs/evidence/phase6-current/ erhalten. Die Backup-Wiederherstellungsbelege liegen neben dem Git-Bundle.
