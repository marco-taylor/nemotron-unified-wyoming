# Phase 5 – Abschluss der lokalen Implementierung

Stand: 01.11.2026. Projekt: `/mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming`. Alle relativen Dateipfade in diesem Bericht beziehen sich darauf. Version 1.0.0 ist zur Freigabe vorbereitet, nicht veröffentlicht. Ein produktiver Home-Assistant-/Unraid-Betrieb wird erst nach gemeinsamer Abnahme behauptet.

## 1. Implementierte Funktionen

Rust-Wyoming-Server für Deutsch mit PCM-S16LE, 16 kHz, Mono. Implementiert sind JSONL-Header, externe JSON-Daten, binäre Payloads und `describe`/`info`, `transcribe`, `audio-start`, `audio-chunk`, `audio-stop`, finale `transcript`- und korrekt gerahmte `error`-Antworten. `info` ist gemäß Spezifikation eine Peer-Beschreibung, keine Erkennungsanfrage. `select-program` wird unterstützt, unbekannte Erweiterungen werden ignoriert. Offizielle Quelle und ausführbare Testreferenz: [OHF-Voice/Wyoming](https://github.com/OHF-Voice/wyoming/tree/08a0c258df83fea6e1643bcfe67e86243f01cf31). Die Ereignisfolge wurde zusätzlich mit dem [Home-Assistant-STT-Client](https://github.com/home-assistant/core/blob/dev/homeassistant/components/wyoming/stt.py) abgeglichen.

Ein Inferenzworker lädt das reale L37-Modell genau einmal vor Bereitschaft. Rust-Backend und native Streams bleiben in diesem Besitzerthread; Verbindungsthreads tauschen nur Ereignisse aus. Keine eigene RNN-T-Portierung und kein Projekt-`unsafe`. Fester sherpa-Commit `31ba0e438f8065189a8e5589d84dfd7faf516d3d`, tatsächliche C-API-Version/SHA und Herkunftsstempel werden geprüft. Die vorhandene Korrektur falscher upstream Versionsmetadaten bleibt dokumentiert; Inferenzcode unverändert.

Je Anfrage neuer deutscher Stream, Rücksetzung nach Fehler/Abschluss und Freigabe nach Verbindungsabbruch. Wiederholte Anfragen am selben Socket und parallele Beschreibungsabfragen möglich; Inferenzaufrufe werden serialisiert. Begrenzte Verbindungen, Queue, Framegrößen und Audiodauer verhindern unbegrenztes Ansammeln von Rust-Audiopuffern. Absolute Empfangsfristen schützen gegen unvollständige langsam nachgelieferte Frames; aktive Anfragen haben eine zusätzliche Gesamtfrist. Standard: zwei Threads, acht Verbindungen, 120 Sekunden Audio, 30 Sekunden Clienttimeout.

SIGTERM/SIGINT: Listener und Sockets schließen, aktuellen nativen Aufruf beenden, Streams/Modell freigeben. Release-Container mit direktem Rust-Entrypoint, UID/GID 65534, CPU-only, persistentem read-only Modellmount, echten Wyoming-Healthchecks und getrennten Build-/Runtime-Stages. Compose und Unraid-Vorlage verwenden keine zusätzlichen Privilegien und begrenzen RAM/PIDs/Logs.

Bereitgestellt: ./docker-compose.yml, ./.env.example, config/unraid-template.xml, ./README.md, ./CHANGELOG.md, ./LICENSE, ./THIRD_PARTY_NOTICES.md sowie docs/UNRAID.md, docs/HOME_ASSISTANT.md, docs/MODELS.md, docs/CONFIGURATION.md, docs/TROUBLESHOOTING.md und docs/RELEASE.md. Build/Test-CI und ausschließlich manuell freizugebendes GHCR-Publishing vorbereitet; kein Workflow remote ausgeführt.

## 2. Build- und Testergebnisse

| Prüfung | Tatsächliches Ergebnis |
|---|---|
| Release-Build mit `--locked --features sherpa` | Bestanden, Rust 1.91.1, Release-Kompilierung 1m36s |
| Rustfmt / Clippy `-D warnings` | Bestanden |
| Automatisierte Tests | **25 bestanden, 0 fehlgeschlagen**: 4 Bibliothek, 1 Modellmetadaten, 1 native Identität, 10 Protokoll, 2 offizielle Python-Interoperabilität, 7 TCP/Config/Lifecycle |
| Fehlende Modelle / THREADS=3 | Klarer Fehler, jeweils Exit 2, kein Bereitschaftssignal |
| Absichtlich beschädigter Decoder im Container-tmpfs | ORT meldet Protobuf-Fehler, Server meldet Modellstartfehler und Exit 2, kein Crash/keine Bereitschaft |
| Laufzeitumgebung | UID/GID 65534, alle nativen Bibliotheken aufgelöst, kein Python/Cargo, Rust-/native Lizenzdateien vorhanden |
| Docker-Healthcheck | healthy; zusätzlich direkte echte Protokollproben bestanden |
| Konfigurationen | Offizielles Compose-JSON-Schema bestanden; XML und Workflow-YAML/Schutzbedingungen bestanden |
| Echter TCP-Modelltest | Drei Anfragen auf einem Socket, paralleles Describe, Sprach-/Audio-/Dauer-/Framefehler und aktiver Abbruch bestanden |
| SIGTERM mit Teilheader und aktiver nativer Sitzung | Beide Sockets geschlossen, keine Transkriptattrappe, Server und Prüfclient jeweils Exit 0; Log: `shutdown complete` |

Echte menschliche Referenz: **„Einsteigen bitte!“**, PCM16/16 kHz/Mono, 1,50025 s. Ausgabe kam ausschließlich vom laufenden nativen Modell:

| Anfrage | Tatsächliches Transkript | TCP-Anfragezeit s | Anfrage-RTF |
|---|---|---:|---:|
| 1 | Einsteigen bitte. | 1.040 | 0.693 |
| 2 | Einsteigen bitte. | 1.038 | 0.692 |
| 3 | Einsteigen bitte. | 1.149 | 0.766 |

Mittlere Anfrage-RTF **0.717**. Diese Zeit umfasst Upload ohne Echtzeit-Pacing, TCP-Verarbeitung, Inferenz und Antwort; Modellladen ist ausgeschlossen. Es ist ein kurzer Integrationstest mit 2 Threads, keine neue repräsentative Benchmarkmatrix. Alle drei Texte stimmen wortweise mit der Referenz überein; nur die Interpunktion unterscheidet sich.

Dockerstats-Momentaufnahme nach den Anfragen: **1,079 GiB von 4 GiB**, CPU 267,85 % (100 % = ein Kern), fünf Tasks/PIDs. **Kein Peak-RAM und kein gemittelter Inferenz-CPU-Wert**; siehe docs/evidence/phase5/docker-stats.json. Container-OOMKilled=false. Docker warnte auf diesem Unraid-Kernel vor fehlender Swap-Limit-Unterstützung: RAM-Limit 4 GiB war gesetzt, ein zusätzliches Swap-Limit wurde nicht zugesichert.

Reproduktionsbefehle ausschließlich im Projektverzeichnis:

```sh
sh scripts/check.sh
sh scripts/runtime-preflight-tests.sh
sh scripts/test-release.sh
```

Die letzten beiden Skripte sind ausdrückliche lokale Tests. Sie verwenden vorhandene Images/Modelle, veröffentlichen keine Hostports und erzeugen nur eigene kurzlebige Container. scripts/test-release.sh setzt absichtlich MAX_AUDIO_SECONDS=2 für den Grenztest; der normale Standard bleibt 120 Sekunden. Python läuft nur im bereits vorhandenen Prüfimage, nicht auf dem Host oder im Runtime-Image.

Artefakte: docs/evidence/phase5/docker-build-final.log, docs/evidence/phase5/config-validation.log, docs/evidence/phase5/real-server.json, docs/evidence/phase5/server.log, docs/evidence/phase5/signal-client.json, docs/evidence/phase5/runtime-environment.log und die jeweiligen Image-/Container-Inspektionen. Die reine Codec-/Lifecycle-Prüfung verwendet explizite Fixtures und wird getrennt von der echten STT-Prüfung gewertet.

## 3. Offene Probleme und Grenzen

- Home Assistant selbst, Assist-VAD, Mikrofon/Satellite, Unraid-DockerMan-Installation, Wiederverbindung nach längerem Betrieb und Langzeitlast wurden nicht verändert bzw. noch nicht gemeinsam getestet.
- Der echte Sprachbeleg verwendet weiterhin nur die 1,50025 s lange menschliche CC0-Aufnahme „Einsteigen bitte!“ von Daniel Mietchen. Drei wiederholte Erkennungen belegen Protokoll-/Modellintegration, keine allgemeine deutsche Home-Assistant-Qualität. Größerer deutscher Befehlssatz und unterschiedliche Sprecher bleiben Abnahmearbeit.
- Keine Wyoming-Teiltranskripte, keine interne VAD, kein Resampling und keine mDNS-Ankündigung. Modell-Streaming/EOF erfolgen in sherpa; Home Assistant muss `audio-stop` liefern. Keine simulierten Texte und keine künstlichen Referenzaufnahmen.
- Ein laufender nativer C-API-Aufruf ist nicht abbrechbar. Shutdown wartet darauf; maximal lange Streams unter voller Queue und ein tatsächlich hängender Decode müssen noch als Last-/Fehlerfall bewertet werden. Healthcheck prüft Protokoll und geladenes Modell, keine neue Erkennung pro Probe.
- Speichergrenzen für Frames/Audio/Sitzungen sind getestet; der maximale Speicherverbrauch bei 8 bzw. 32 langen nativen Streams ist nicht empirisch abgenommen. Compose/XML setzen 4 GiB als harte Grenze, keine Garantie für alle Extremkonfigurationen.
- Compose-Plugin fehlt auf dem Host. YAML wurde gegen das offizielle Compose-Schema geprüft, **kein** erfolgreicher `docker compose config/up` behauptet. XML wurde geparst und auf sicherheitsrelevante Felder geprüft; noch kein Import in DockerMan und keine öffentliche CA-Aufnahme.
- Öffentliche Repository-/Registry-/Support-/Icon-URLs fehlen bewusst. Kein GitHub-/GHCR-Push, kein Release-Tag, keine öffentliche CA-Einreichung. Manuelle Workflows sind syntaktisch vorbereitet, remote nicht getestet. GitHub-Environment `release` muss vor Veröffentlichung mit Reviewer-Regeln konfiguriert werden.
- Runtime-/Compilerbasen und sherpa/Cargo sind gepinnt; Debian-APT-Pakete und transitive CMake-Downloads stammen weiterhin aus den Upstreamquellen des gepinnten Builds. Kein bitidentischer Offline-Rebuild oder vollständiger Supply-Chain-/CVE-Audit behauptet.

## 4. Image und Speicherbedarf

Lokales Runtime-Image: **117.452.575 Byte = 112.01 MiB** (Docker-Uncompressed-Size, keine Registry-Kompressionsgröße). ID `sha256:31a9cc13e1e1a7a7022d3b6cd3a19c8f79e118634195417059a07db33ba3b1ae`. Enthält Server, native sherpa-/ORT-Bibliotheken, Debian-Laufzeit und gesammelte Lizenztexte, keine Gewichte/Compiler/Python. Beide Basisimages sind auf Digests gepinnt.

Am Abschlusszeitpunkt rund **305 GiB frei** im NVMe-Appdata-Dateisystem; Projektgröße einschließlich aller erhaltenen Phase4-Gewichte/Exportartefakte rund **11,93 GiB** (12.815.008.376 Byte; kleine Logänderungen danach möglich). Der Docker-Build nutzt zusätzlich lokale Cachelayer, die nicht Bestandteil des Runtime-Images sind. Keine Löschung oder Bereinigung vorhandener Daten.

Modellgewichte wurden nicht erneut heruntergeladen oder exportiert. Der geprüfte Runtime-Satz bleibt 726.885.887 Byte zuzüglich kleiner Lizenz-/Herkunftsdateien; alle vorhandenen Original-/FP32-Dateien bleiben erhalten. Neu benötigt wurden kleine Rust-/Validierungsabhängigkeiten und lokale Buildartefakte; die Compose-Schema-Prüfung lud rund 0,6 MiB Paketarchive und installierte die Validierungsbibliotheken ausschließlich im flüchtigen Prüfcontainer. Keine Hostpakete installiert. Freier Speicher und Build-/Projektgrößen wurden kontrolliert; keine Bereinigung fremder Images/Container/Caches.

## 5. Installation

1. Bereits lokal gebautes Image verwenden oder `sh scripts/check.sh` ausführen.
2. Modellverzeichnis und Leserechte für UID 65534 anhand docs/MODELS.md prüfen; read-only nach `/models` mounten.
3. Nach gemeinsamer Freigabe entweder config/unraid-template.xml manuell als neue DockerMan-Benutzervorlage installieren oder ./.env.example nach ./.env kopieren und ./docker-compose.yml bewusst starten. Anleitung: docs/UNRAID.md. Kein existierender Container muss ersetzt werden.
4. Freien dedizierten LAN-Hostport wählen (Beispiel 10310). Port/Modell/Threads über Konfiguration anpassen, Healthcheck und mehrere echte Anfragen prüfen.
5. Erst danach in Home Assistant manuell Wyoming Protocol mit Unraid-LAN-Adresse und Hostport hinzufügen und eine deutsche Testpipeline wählen, siehe docs/HOME_ASSISTANT.md.

## 6. Voraussetzungen für v1.0.0

Lokale Implementierung und Prüfungen müssen grün sein; der gemeinsame reale HA-/Satellite-/Unraid-Test und längerer Betrieb unter sinnvoller Last sind die verbleibenden betrieblichen Freigabepunkte. Code-/Modell-/Dependency-Lizenzhinweise prüfen und endgültige Repository-/Betreuerangaben festlegen. Anschließend ausdrücklich Veröffentlichung freigeben, Git-Release erstellen und erst dann den vorbereiteten manuellen GHCR-Workflow verwenden. Einzelheiten: docs/RELEASE.md.

Bestehende STT-Projekte, produktive Container, Home Assistant und bestehende Unraid-Docker-Konfigurationen wurden nicht geändert. Isolierte Phase5-Testcontainer werden nach den Prüfungen beendet und entfernt. Kein produktiver Nemotron-Dienst bleibt zurück.
