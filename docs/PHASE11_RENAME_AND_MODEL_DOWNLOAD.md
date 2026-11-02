# Phase 11 – Projektumbenennung und Modellinitialisierung

Stand: 02.11.2026. Ausschließlich lokale Entwicklung, keine Veröffentlichungsfreigabe.

## Ausgangszustand und Sicherung

Basis-Commit und unverändertes main: `d7af454c269da902b220ea50d23d256220edb376`.
Arbeitsbranch: `feature/rename-model-download`.

Die Phase-9-Änderungen bleiben getrennt im Branch `feature/latency-optimization` und Stash `3c4b40dba63e722e205cea9d33742372eb5d7827`. Sie wurden nicht angewendet. Die Phase-10-Vereinfachung wurde ausdrücklich übernommen; ihre unveränderte Sicherung bleibt als Stash `1efe6ddae4ca1d3e107064af07d9b93d72b76f01` und im Branch `feature/unraid-template-simplification` erhalten. Keine Änderung an src/server.rs, src/inference.rs, src/streaming.rs, src/config.rs oder config/variables.json.

Sicherung außerhalb des Projekts: `/mnt/nvme/appdata/codex-workspace/nemotron-phase11-backups/all-history.bundle`. Enthält alle damaligen Branches, Tags/Refs und die Stash-Kette. `git bundle verify` erfolgreich; tatsächlicher Mirror-Restore unter `/mnt/nvme/appdata/codex-workspace/nemotron-phase11-backups/restore-check.git`, `git fsck --full` und Abruf beider Stash-Objekte erfolgreich. Zusätzlich `/mnt/nvme/appdata/codex-workspace/nemotron-phase11-backups/phase10.patch` und `/mnt/nvme/appdata/codex-workspace/nemotron-phase11-backups/phase10-untracked.tar.gz`, Archiv gegen Quelldateien geprüft. Backup-Verzeichnis privat (0700, Dateien 0600).

Der fertig vorbereitete lokale Phase-11-Branch wird zusätzlich unter `/mnt/nvme/appdata/codex-workspace/nemotron-phase11-backups/phase11-prepared.bundle` gesichert und geprüft. Der ursprüngliche Backupstand wird dabei nicht überschrieben. Die neue lokale Commit-ID liefert `git rev-parse feature/rename-model-download`; es gibt keinen veröffentlichten Phase-11-Commit.

Vorherige Containerkonfigurationen, gespeicherte Unraid-Vorlagen und Image-Identitäten wurden nur lesend protokolliert. Rohbelege liegen ignoriert unter docs/evidence/phase11 und werden nicht veröffentlicht.

## Lokale Umbenennung

Neues tatsächliches Verzeichnis: `/mnt/nvme/appdata/codex-workspace/nemotron-unified-wyoming`.
Der bisherige Pfad `/mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming` bleibt als relativer Kompatibilitäts-Symlink erhalten. Das Ziel existierte vorher nicht. Quelle und Ziel liegen auf demselben ZFS-Dateisystem (Device 49); die Umbenennung erhielt Directory- und Modell-Inodes. Keine Kopie, kein Überschreiben oder Löschen von Modellgewichten. Rund 299 GB freier Platz waren vorhanden; eine zweite Modellkopie war nicht erforderlich. SHA256 und tatsächliche Lesbarkeit mit UID 99/GID 100 wurden vor der Umbenennung geprüft.

Aktive Cargo-/Docker-/Compose-/Workflow-/Template-/Installationsreferenzen verwenden den neuen Projektnamen. Der stabile ausführbare Name bleibt `/usr/local/bin/nemotron-wyoming`. Rust, native L37-Verarbeitung und alle 19 Variablen bleiben erhalten. Historische Berichte und frühere Registry-Nachweise behalten den bisherigen Namen ausdrücklich als historische Information.

Geplantes GitHub-Ziel: https://github.com/marco-taylor/nemotron-unified-wyoming.
Geplantes Image: `ghcr.io/marco-taylor/nemotron-unified-wyoming:latest`.
Beides ist noch unveröffentlicht. `origin` bleibt für Rückverfolgung auf dem bisherigen Repository; zusätzlich existiert der rein lokale Remote `planned-public` für das geplante Ziel. Kein Remote-Push und keine Änderung am GitHub-Repository.

## Exakte Modelle und Quellenblocker

Verwendet wird NVIDIA Nemotron Labs Unified ASR 0.6B, eigener L37-Export mit linkem Kontext 37, Center 7, rechtem Kontext 7. Gepinnter sherpa-onnx-Commit `31ba0e438f8065189a8e5589d84dfd7faf516d3d`; teilweise QUInt8 im Encoder, FP32 in Decoder/Joiner. Vollständiges Manifest: config/model-manifest.json.

| Datei | Byte | SHA256 |
|---|---:|---|
| models/L37-runtime/encoder.int8.onnx | 675328677 | `8e1b140b85900dcaede7e5fc05c1adfd48d4a0585e3b55ec2a10cded7042c96d` |
| models/L37-runtime/decoder.onnx | 36745480 | `e5281215d86116e425191324830090922ec7732a34b1f5203d3b5a3564a20d97` |
| models/L37-runtime/joiner.onnx | 14768802 | `7abd80133827b59dbd3b57c47242d6001607ed14acda5db36ae28d64a3de8af8` |
| models/L37-runtime/tokens.txt | 42928 | `94139a0b2134fd40664ca72260026fa8a073336bb2f062239c8ecde2c8031763` |

Gesamt: 726.885.887 Byte. Vorhandene Dateien bleiben unverändert.

Die [offizielle NVIDIA-Dateiliste](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b/tree/main) und die Hugging-Face-Modellsuche wurden ohne erneuten Gewichtedownload geprüft. Die Quelle enthält den NeMo-Checkpoint (SHA256 `1718cc1b44fb8597b2356328d706a8d89f31c389ca6f2256c2e3f743c0246936`), aber nicht unseren exakten ONNX-Satz. Die Suche ergab zusätzlich CoreML-/GGUF-Varianten; diese sind kein zulässiger Ersatz. [sherpa-onnx PR #4141](https://github.com/k2-fsa/sherpa-onnx/pull/4141) ist offen und beschreibt Export/Packaging; daraus ist keine überprüfte öffentliche Bezugsquelle für unsere vier konkreten Hashes nachgewiesen.

**Blocker:** Es gibt noch keine verifizierte öffentliche Downloadquelle für die exakt benötigten Dateien. Die vier URL-Felder bleiben deshalb leer. Der Downloader ist vorbereitet und mit kontrollierten Transport-Fixtures getestet; eine echte automatische Neuinstallation mit leerem Verzeichnis funktioniert mit diesem Stand bewusst noch nicht. Fehlende/beschädigte Dateien führen zu verständlichem Abbruch statt zum Start mit falschen Gewichten. scripts/check_model_source.py blockiert die zukünftige GHCR-Veröffentlichung ebenfalls.

## Lizenz und zulässige Bereitstellung

Die [geprüfte OpenMDW-1.1-Modelllizenz](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b/blob/e141dff433df9ab1962eec4d8d494560f9a02009/LICENSE.md) erlaubt Nutzung, Bearbeitung und Weitergabe unter ihren Bedingungen. Bei Weitergabe müssen Lizenz sowie anwendbare Copyright- und Herkunftshinweise erhalten bleiben. Die Lizenz gewährt keine pauschale Freistellung von Rechten Dritter. Der Originaltext ist unter config/model-LICENSE.md enthalten; Code bleibt MIT, sherpa-onnx Apache-2.0 und weitere Komponenten behalten ihre eigenen Hinweise in ./THIRD_PARTY_NOTICES.md und im Runtime-Lizenzverzeichnis. Keine Herstellerpartnerschaft oder Markenlizenz wird behauptet.

Technisch geeignete spätere Bereitstellung: eigenes versioniertes Modellrepository auf Hugging Face oder separater Artefakt-Release, mit exakt den vier geprüften Dateien, vollständiger Lizenz, NVIDIA-Ursprung, Modellkarte/Herkunftshinweisen und Kennzeichnung der eigenen Export-/Quantisierungsschritte. Unveränderliche Commit-/Release-Adressen verwenden, jede öffentlich abgerufene Datei gegen dieses Manifest prüfen. Vorher keine URL eintragen. Kein Modell wurde hochgeladen und kein solcher Release angelegt. Weitere Origin-Notices des gepinnten NVIDIA-Modellstands vor einer tatsächlichen Bereitstellung vollständig beilegen.

## Ablauf und Persistenz

scripts/docker-entrypoint.sh validiert PUID/PGID und wechselt vor allen Modellzugriffen auf diese Identität. scripts/model-init.py prüft bei `serve` Größe und SHA256 der vier Dateien. Vollständige gültige Modelle benötigen weder Internet noch Schreibzugriff; CLI-Pfadüberschreibungen und alle bisherigen Einzelpfade bleiben wirksam. Healthcheck, Version, Hilfe und check-model initiieren keinen Download.

Wenn eine genehmigte Quelle konfiguriert ist: exklusiver flock im persistenten Verzeichnis, erneute Prüfung unter Sperre, nur fehlende/beschädigte Dateien laden. Temporäre Datei liegt auf demselben Dateisystem. Größenbegrenzung, TLS-/HTTPS-Regeln, Timeout, SHA256, fsync und atomare Übernahme verhindern ungeprüfte Inferenz. Beschädigte Originale bleiben über einen `.corrupt-*`-Hardlink erhalten; gültige Dateien werden nicht ersetzt. Unterbrochene `.part-*` gelten niemals als Modell. Nach hartem Abbruch können Reste bleiben; keine pauschale Löschung. Neustart prüft erneut und nutzt gültige Dateien weiter. Netzwerk-/Rechte-/Platzfehler brechen verständlich ab. Sperrwartezeit und kompletter Downloaddurchlauf sind auf ungefähr 30 Minuten begrenzt; ein einzelner Netz-Lesezugriff hat 30 Sekunden Timeout. Healthcheck hat 35 Minuten Startfrist und wird sofort aktiv, sobald Wyoming bereit ist.

Persistenter Unraid-Standard: `/mnt/user/appdata/nemotron-unified-wyoming/models/L37-runtime` → `/models`. RW-Bind für die vorbereitete Downloadphase; keine Gewichte im Image. Der Container ändert keine Eigentümer bestehender Dateien. PUID/PGID muss für Download schreiben und für Inferenz lesen dürfen. Der nur lesend geprüfte Unraid-7.3.4-Helfer `/usr/local/emhttp/plugins/dynamix.docker.manager/include/Helpers.php` erstellt fehlende Pfade bei tatsächlicher Installation als 99:100; in dieser Phase wurde diese Aktion nicht ausgeführt. Abweichende PUID/PGID erfordern einen entsprechend vorbereiteten neuen Zielordner. Compose verweigert automatische Hostpfaderstellung.

Nach Initialisierung sperrt ein zusätzlicher libseccomp-Filter Dateiänderungen vor exec des Rust-Servers und wird an alle ORT-Threads vererbt. Schreibende Dateiöffnungen, openat2, io_uring sowie Datei-/Metadatenänderungen werden verweigert; lesende Zugriffe und bestehende stdout/stderr bleiben verfügbar. Keine zusätzlichen Capabilities. Root-FS bleibt read-only, NNP bleibt 1, effektive Capabilities bleiben 0. Auf diesem Kernel war Landlock nicht verfügbar (ENOSYS); diese verworfene Variante wird nicht vorausgesetzt. Der Filter schützt den STT-Prozess, nicht vor Änderungen am Host oder durch andere berechtigte Container. Vollständige alte RO-Modellmounts funktionieren weiterhin.

## Unraid und bestehende Installationen

config/unraid-template.xml übernimmt vollständig die Phase-10-Oberfläche: sichtbar sind Hostport 10310 → intern 10300/TCP, Modellverzeichnis und THREADS=2. Nur erweitert: MAX_AUDIO_SECONDS=120, MAX_CONNECTIONS=8, CLIENT_TIMEOUT_SECONDS=30, LOG_LEVEL=info, LOG_TRANSCRIPTS=false, PUID=99, PGID=100. Die elf entfernten technischen Einträge bleiben entfernt. THREADS-Beschreibung erläutert 1/2 Threads und rät auf N100 von 4 ab.

Low-Q bleibt das einzige Standardicon im Template, CA-Profil und Image-Label. Neue vorgesehene Raw-Adresse: https://raw.githubusercontent.com/marco-taylor/nemotron-unified-wyoming/main/assets/icons/nemotron-lowq.png. Diese Adresse wird vor einer späteren CA-Freigabe tatsächlich erreichbar zu prüfen sein. Beide lokalen Icons sind unverändert; HQ bleibt zusätzliche Grafik.

Keine automatische Migration: bisherige Container-/Image-Namen, gespeicherte Unraid-Vorlagen und individuelle Variablen bleiben unangetastet. Alte Registry-Tags werden nicht entfernt. Alten Modellpfad bei späterer Migration bewusst weiterverwenden oder kontrolliert in ein neues, leeres Ziel kopieren; vorhandene Dateien nicht überschreiben. Hostnetz verwendet den internen Port (Standard 10300), Bridge bildet 10310 auf 10300 ab. Abweichender WYOMING_PORT benötigt passende manuelle Portzuordnung. Vor einem späteren Apply alte Benutzervorlage sichern und jeden Sonderwert übertragen.

## Tests und Freigabe

Lokales Testimage: `nemotron-unified-wyoming:phase11-test`, linux/amd64, Image-ID `sha256:7fc78c726a1d9d2a666764a76e039cde453dbd3dd176fcec10f2a0388b73dbee`. Keine Registry-Veröffentlichung; die ID ist kein öffentlicher GHCR-Digest.

| Prüfung | Ergebnis |
|---|---|
| Rust Release-Build, fmt, Clippy `-D warnings` | Bestanden mit `--locked --features sherpa`; Clippy für alle Targets |
| Rust-Tests | Alle 33 bestanden, einschließlich Konfiguration, Streaming, nativer Versionsprüfung, TCP und Python-Interop |
| Initialisierung | Alle 17 automatisierten Tests bestanden, zusätzlich kompletter Lauf als 99:100 |
| Leerer Cache / eine fehlende / beschädigte Datei | Kontrollierte Fixtures: gezielt geladen, Hashprüfung und Sicherung bestanden |
| HTTPS | Echter lokaler TLS-Transport: nicht vertrautes Zertifikat abgewiesen, explizit vertraute Test-CA akzeptiert; HTTP und unsichere Weiterleitungen verweigert |
| Unterbrechung und Konkurrenz | SIGKILL während Fixture-Download, Neustart und drei gleichzeitige Initialisierungen bestanden; nur ein Download je Datei |
| Netzwerk-/Speicherplatzfehler | Kontrollierte Netzwerkfehler, Platzvorprüfung und ENOSPC-Verarbeitung bestanden; zusätzlich tatsächlicher ENOSPC auf isoliertem 64-KiB-tmpfs als UID 99/GID 100 |
| Schreibschutz nach Initialisierung | Lesen erlaubt; schreibende Öffnung, Neuanlage, Löschen, chmod und rename eigener Dateien durch seccomp abgewiesen |
| Docker-Build und CLI | Bestanden; vollständiges Python-Standardpaket erforderlich, korrigierter finaler Build erfolgreich |
| Minimal / Template / bisherige Konfiguration | Alle drei isolierten Dockerläufe bestanden, jeweils drei echte deutsche Transkriptionen |
| Healthcheck und Bridge | Tatsächlicher Dockerstatus healthy; zufällige Loopback-Hostports auf 10300 bzw. abweichenden 10444 geprüft; XML-Parser bestätigt 10310→10300 |
| Identität und Sicherheit | 99:100 sowie 12345:23456; CapEff/CapPrm/CapAmb=0, NoNewPrivs=1; passende direkte Nonroot-Ausführung ohne Capabilities und ungültige IDs geprüft |
| Wyoming / Offline-Inferenz | Zusätzlicher Netzwerkmodus-none-Test mit offizieller Wyoming-Referenz: echte ASR, wiederholte Anfragen, Fehlerbehandlung und Shutdown bestanden |
| Alle 19 Variablen / Defaults | Unverändert; nichtstandardmäßige Legacy-Konfiguration mit allen 19 Variablen erfolgreich; ungültiges THREADS wird benannt abgewiesen |
| Modelle | SHA256 nach Umbenennung als UID 99/GID 100 erneut vollständig bestätigt; keine Änderung an Originalen |
| XML / Compose / Workflows | xmllint, offizielles Compose-JSON-Schema, installierter Unraid-Parser und Sichtbarkeit 3/7/11 bestanden; Workflows lokal geprüft, nicht gestartet |
| Icons / aktive Namen | Beide Icon-Hashes unverändert; Low-Q allein in allen drei Standardreferenzen; keine alten Slugs in aktiven Code-/Config-/Workflow-Dateien |
| Sicherheitsprüfung | Arbeitsbaum und veröffentlichungsfähige HEAD-Historie ohne Secrets/Modellgewichte; Archivrefs bleiben rein lokal |
| Runtime-Image-Audit | 4860 Dateien geprüft: keine Modellgewichte/Zugangsdaten. Bereits verifizierte öffentliche GnuTLS-Selbsttestschlüssel im exakten Debian-Binary sind separat ausgewiesen |
| Bestandsschutz | Alle 31 vorbestehenden Container: IDs, Config, HostConfig, Mounts, Start-/Endzeit, Status und RestartCount unverändert; gespeicherte Nemotron-Unraid-Vorlage byteidentisch; altes latest-Image unverändert |
| Echte leere Erstinstallation mit öffentlichen L37-Dateien | **Blockiert:** keine verifizierten URLs; tatsächlicher Containerstart ohne Modelle endet verständlich mit Exit 2, kein ungeprüfter Serverstart |

Echte Texte: in Minimal-, Template-, Legacy- und zusätzlichem Offline-Identitätstest jeweils `Einsteigen bitte.`. Es wurde nur die vorhandene unabhängige deutsche Aufnahme verwendet; keine zusätzliche Qualitätsabnahme oder Latenzbehauptung. Kleine Downloader-Fixtures sind keine echten Modellgewichte oder Sprachaufnahmen. Die vorhandene L37-Inferenz verarbeitet weiterhin inkrementell; Phase-9-Änderungen wurden nicht übernommen.

Reproduzieren: `docker build --platform linux/amd64 --target runtime -t nemotron-unified-wyoming:phase11-test .`; der Build führt Rust- und Initialisierungstests aus. Für zusätzliche UID-Prüfung das Testimage mit `--user 99:100`, `--network none`, read-only Projektmount und tmpfs für temporäre Fixtures starten, dann `python3 -m unittest discover -s tests -p model_init_test.py -v` im Projektverzeichnis ausführen. Runtime-Matrix über scripts/test-unraid-minimal.sh mit `IMAGE=nemotron-unified-wyoming:phase11-test`, TEST_MODE minimal/template/legacy und getrennten TEST_RESULTS_DIR; Identität über scripts/test-identity.sh mit lokalem Development-Image als CLIENT_IMAGE. Details: docs/TESTS.md.

Die erste Buildprobe hatte einen Cargo-libgit2-SSL-Fehler; Git-CLI-Abruf mit aktiver TLS-Prüfung behebt dies. Eine nach Paketumbenennung nötige Formatkorrektur wurde durchgeführt. Der Zwischenstand mit python3-minimal scheiterte wegen fehlendem ctypes; final wird Python 3 mit vollständiger Standardbibliothek verwendet. Alle oben als bestanden genannten Ergebnisse stammen vom korrigierten Stand. Der Host meldet fehlende Swap-Limit-Unterstützung; RAM-cgroup-Limits sind weiterhin aktiv.

Bestehender Nemotron-Container: `nemotron-unified-rust-wyoming`, ID `78e8a09f7f69`, weiterhin `created` und nicht gestartet. Sein gespeicherter alter Appdata-Modellpfad fehlt bereits vor dieser Phase. Das wurde weder automatisch repariert noch durch einen Startversuch verändert. Alle eigenen temporären Testcontainer wurden kontrolliert entfernt; das lokale Testimage bleibt für Review erhalten. Neues GitHub-Ziel bei Prüfung HTTP 404.

Veröffentlichung bleibt gesperrt. Zuerst separate Freigabe für die exakte Modellbereitstellung, öffentliche Hashprüfung und echte leere Erstinstallation; danach Freigabe für GitHub-Umbenennung/Push, GHCR und CA einholen. Kein offizielles v1.0.0-Release.
