# Phase 5.2 – PUID/PGID und vollständige Variablen

Stand: 02.11.2026. Projekt: /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming. Relative Pfade beziehen sich auf dieses Projekt. Keine Veröffentlichung und keine Änderung des laufenden Containers nemotron-unified-stt oder anderer vorhandener Dienste.

## Bisheriger Zustand und Änderung

Das bisherige Runtime-Image startete fest als UID/GID 65534:65534. Docker-Umgebungsvariablen allein ändern USER nicht. PUID und PGID werden jetzt deshalb vom tatsächlichen Entrypoint scripts/docker-entrypoint.sh ausgewertet, nicht als wirkungslose Rust-Optionen angeboten.

Das neue Image beginnt mit UID 0 nur für den Identitätswechsel. Das Startskript validiert numerische IDs, verwendet das bereits im Debian-Runtime-Basisimage enthaltene setpriv und ersetzt sich anschließend per exec durch den Rust-Prozess. Vor Modellzugriff/Inferenz werden reale/effective/saved/filesystem UID/GID gesetzt, zusätzliche Gruppen entfernt, Inheritable-/Ambient-Capabilities entfernt und no_new_privs gesetzt. Der Server bleibt PID 1, SIGTERM/SIGINT funktionieren direkt. Keine Passwort-/Gruppendateien werden geschrieben; keine Modellrechte geändert und keine rekursiven chown/chmod-Aktionen durchgeführt.

./docker-compose.yml und config/unraid-template.xml geben beim Bootstrap ausschließlich SETUID und SETGID zu cap_drop=ALL hinzu. Keine DAC_OVERRIDE-, CHOWN-, SYS_ADMIN- oder sonstigen erweiterten Rechte nötig. Der laufende Server besitzt nach dem UID-Wechsel keine effektiven/permitted/ambient Capabilities. Ein identisch konfiguriertes explizites Docker --user PUID:PGID erlaubt auch den Start ganz ohne Root und ohne Capabilities. Bei widersprüchlichen --user/Umgebungswerten wird abgebrochen statt PUID/PGID zu ignorieren.

Docker-Inspect Config.User=0:0 beschreibt nur den Bootstrap, nicht den laufenden Server. Tatsächliche Identität deshalb über /proc/1/status prüfen. Docker exec verwendet ohne --user ebenfalls den Docker-Konfigurationsbenutzer; für normale Diagnosen --user 99:100 verwenden oder den Entrypoint aufrufen. Der Docker-Healthcheck ruft den Entrypoint auf und läuft dadurch ebenfalls unter den angeforderten IDs.

## Vollständige unterstützte Variablen

Die ursprünglichen 17 Dienstvariablen bleiben unverändert. PUID/PGID gehören zur Container-Startschicht; die anderen 17 werden vom Rust-Parser verarbeitet. Insgesamt 19 Nutzer-Variablen. Referenzliste: config/variables.json. Alle sind in ./.env.example, config/unraid.env.example, ./docker-compose.yml und config/unraid-template.xml enthalten. Pflichtwerte sind nur dort nötig, wo der Anwender tatsächlich einen Modellmount bereitstellen muss; optionale Modell-Einzelpfade dürfen leer bleiben.

| Exakter Name | Standard | Zulässige Werte | Beschreibung/Wirkung |
|---|---|---|---|
| `PUID` | `99` | kanonische Dezimalzahl 1–2147483647, keine führenden Nullen; 0 verboten | Tatsächliche Server-UID, durch Entrypoint vor Programmstart angewendet. Nicht vorhandener Wert nutzt 99; leerer Wert ist Fehler. |
| `PGID` | `100` | kanonische Dezimalzahl 1–2147483647, keine führenden Nullen; 0 verboten | Tatsächliche primäre Server-GID; Root-Bootstrap löscht zusätzliche Gruppen. Fehlend nutzt 100, leer ist Fehler. |
| `WYOMING_HOST` | `0.0.0.0` | gültige IPv4-/IPv6-Adresse, IPv6 auch geklammert | Listener- und Healthcheck-Adresse im Container. Kein DNS-Bindname. |
| `WYOMING_PORT` | `10300` | ganze Zahl 1–65535 | Interner Listener-/Healthcheck-Port. Hostport separat; Compose-Porttarget passt sich an. |
| `LANGUAGE` | `de` | nur `de` | Deutscher Dienst mit deutscher Sprachkonditionierung. |
| `STT_DEVICE` | `cpu` | nur `cpu` | Native ORT-Providerwahl; dieses Image unterstützt keine GPU-Provider. |
| `MODEL_DIR` | `/models` | nicht leer, UTF-8 ohne NUL; ausgewählte Dateien lesbar/nicht leer | Basis für Standardmodellnamen und relative Einzelpfade. |
| `ENCODER_PATH` | leer → MODEL_DIR/encoder.int8.onnx | leer oder gültiger relativer/absoluter Containerpfad ohne NUL | Ausgewählter INT8-Encoder; L37-/Deutsch-Metadatenprüfung und echter ORT-Graphload. |
| `DECODER_PATH` | leer → MODEL_DIR/decoder.onnx | leer oder gültiger relativer/absoluter Containerpfad ohne NUL | Predictor aus demselben Export. |
| `JOINER_PATH` | leer → MODEL_DIR/joiner.onnx | leer oder gültiger relativer/absoluter Containerpfad ohne NUL | Joint Network aus demselben Export. |
| `TOKENS_PATH` | leer → MODEL_DIR/tokens.txt | leer oder gültiger relativer/absoluter Containerpfad ohne NUL | Passende Tokenliste. |
| `THREADS` | `2` | 1, 2 oder 4 | ORT-Threads pro Sessionkonfiguration, kein hartes Prozess-Threadlimit. |
| `MAX_AUDIO_SECONDS` | `120` | ganze Zahl 1–120 | Samplelimit je Anfrage, zusätzlich Bestandteil der Gesamtfrist. |
| `MAX_AUDIO_CHUNK_BYTES` | `320000` | gerade ganze Zahl 640–320000 | Frame-Payloadlimit vor Allokation, kürzere Chunks zulässig. |
| `MAX_CONNECTIONS` | `8` | ganze Zahl 1–32 | Begrenzt Verbindungsthreads/Sitzungen und Queue. Native Inferenz bleibt serialisiert. |
| `CLIENT_TIMEOUT_SECONDS` | `30` | ganze Zahl 1–300 | Absolute Frame-Empfangsfrist und Schreibtimeout. |
| `INFERENCE_CHUNK_MS` | `20` | ganze Zahl 10–560 | Maximalgröße nativer Zuführungsstücke, keine Änderung des L37-Modellkontexts oder der 1,12 s-Latenz. |
| `LOG_LEVEL` | `info` | error, warn, warning, info, debug; Groß-/Kleinschreibung erlaubt | Rust-Logfilter; native Fehlerausgaben separat. |
| `LOG_TRANSCRIPTS` | `false` | exakt true oder false | Finale Texte nur bei explizitem true und info/debug protokollieren; Audio wird nicht geloggt. |

Compose-Hilfswerte außerhalb des Rust-Prozesses: IMAGE (lokales Image-Tag), HOST_PORT (10310), PUBLISH_ADDRESS (0.0.0.0). MODEL_DIR in Compose-./.env bezeichnet aus Kompatibilitätsgründen die Host-Mountquelle; der Container erhält MODEL_DIR=/models. SHERPA_ONNX_LIB_DIR und LD_LIBRARY_PATH sind technische Image-/Loaderwerte, keine neuen Benutzer-Tuningoptionen.

## Modellrechte

Die vorhandenen Modelle unter /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming/models/L37-runtime sind read-only gemountet. Verzeichnisse sind 0755, die vier Dateien 0644, Eigentümer root:root. Damit sind sie auch für 99:100 lesbar, ohne Kopie, Eigentums- oder Rechteänderung. Die Inferenz öffnet alle Dateien erst nach dem Identitätswechsel. Nicht zugängliche Pfade melden jetzt ausdrücklich Zugriff/Permission denied statt bloß missing model file.

Für eigene restriktive Mounts müssen alle Elternverzeichnisse für die Zielidentität betretbar und Dateien über Eigentümer/primäre Gruppe/ACL lesbar sein. Nicht pauschal vorhandene Modellbestände chownen. PUID/PGID sind Container-IDs; ein neuer benannter Linux-Benutzer ist nicht erforderlich. Die bekannten CLI-Pfade und alle bisherigen Defaults bleiben erhalten.

## Tatsächliche Build-/Testergebnisse

- **Release-Build, cargo fmt --check, alle 33 Rust-Tests und Clippy mit -D warnings bestanden.** Darin bleiben die bisherigen 17 Variablen mit Default-/Override-/Ungültigkeits-/Pfad-/Limit-/Logging-Prüfungen enthalten; der zusätzliche Test prüft die getrennt dokumentierten Bootstrap-Defaults.
- **19/19 Variablen** in Compose, XML und Beispieldateien gegen die Referenzliste geprüft; offizielles Compose-Schema und XML-/Workflow-YAML-Prüfung bestanden. SETUID/SETGID als einzige zusätzlichen Compose-Capabilities und fehlende feste user-Zeile automatisch geprüft.
- **Tatsächlicher PID 1-Zustand bei Default PUID/PGID:** alle vier UID-Felder 99, alle vier GID-Felder 100; zusätzliche Gruppen leer; CapPrm/CapEff/CapAmb jeweils 0000000000000000; NoNewPrivs=1. Das ist der Rust-Serverprozess, keine simulierte Benutzerausgabe.
- **Reine Umgebungsänderung wirkt:** separater Bootstrap-Start mit PUID=12345/PGID=23456, ohne --user-Override. PID 1 tatsächlich 12345:23456, effektive Capabilities 0, NoNewPrivs=1, Healthcheck erfolgreich. Zusätzlich bereits unprivilegierter Start mit passenden --user/Umgebungswerten und cap-drop ALL erfolgreich.
- **Ungültige Werte:** für PUID und PGID jeweils 0, -1, invalid, leer, 099 und 2147483648 getestet; alle Exit 2 mit Variablennamen. Widersprüchliches Docker --user ebenfalls Exit 2, kein stiller Fallback.
- **Modellzugriff:** vorhandener read-only L37-Mount unter 99:100 erfolgreich geladen. Kontrollfall mit nur im Testcontainer angelegtem root-only 0700-Verzeichnis scheitert mit klarer Permission-denied-Meldung und Exit 2. Eigentümer/Modi aller vorhandenen Modellpfade vor/nach Test identisch; keine chown/chmod/Kopie an bestehenden Gewichten.
- **Echte deutsche Inferenz bei 99:100:** drei Anfragen liefern jeweils „Einsteigen bitte.“. Referenz ist die vorhandene menschliche 1,50025-s-CC0-Aufnahme, kein Fixturetext. Wiederholte Wyoming-Anfragen, Fehler-/Limitfälle und direkte Healthchecks bestanden.
- **Bisheriger Nichtstandard-Konfigurationstest erneut grün unter 99:100:** Port 10444, ein Thread, vier explizite Modellpfade, native 80-ms-Zuführung bei 160-ms-Netzwerkchunks, geändertes Payloadlimit, Debug-/Transkriptlogging. Ebenfalls drei echte Texte „Einsteigen bitte.“; SIGTERM bei offenen Sockets/aktiver Sitzung endet mit Exit 0.
- **Neues lokales Image:** nemotron-unified-rust-wyoming:phase5.2, sha256:8b3645948c36a1ec93c17dc31b24e9a2bce51b0ec6f3446f9002bed0233ad45d, 117.491.034 Byte / 112.05 MiB. Bestehende Image-Tags des laufenden HA-Testcontainers nicht umgebogen. Keine Veröffentlichung.
- Runtime-Vorprüfer ebenfalls erneut bestanden: --version, fehlende/inkompatible Modelle, ungültige Threadzahl, native Bibliotheken und Lizenztexte. Diagnose-Shell explizit 99:100; auch der beschädigte-Decoder-Kontrollfall nutzt vor Programmstart den Entrypoint. Aktuelle Ergebnisse getrennt unter docs/evidence/phase5_2/preflight.
- Alle eigenen Testcontainer entfernt. Alle 31 Bestandscontainer nach ID, Status, Startzeit und Restart-Zähler unverändert. Der bisherige nemotron-unified-stt bleibt healthy, mit unveränderter ID/Startzeit und 65534:65534.

Reproduktion: Docker-Build nach ./Dockerfile; sh scripts/test-identity.sh; IMAGE=nemotron-unified-rust-wyoming:phase5.2 CLIENT_IMAGE=nemotron-unified-checks:phase5.2 TEST_RESULTS_DIR=docs/evidence/phase5_2/configured sh scripts/test-configured-release.sh. Keine Hostports werden dabei veröffentlicht. Schema-Validator scripts/validate_configs.py lief in einem separaten vorhandenen Python-Prüfimage, ohne den Home-Assistant-Container zu verändern.

Rohbelege unter docs/evidence/phase5_2: build-final.log, config-validation.log, process-identity.txt, override-process-identity.txt, denied-model.log, real-server.json, configured/server.log und container-comparison.json. Ein erster Build vor verfügbarer Formatierung scheiterte erwartbar an fmt --check; nach Docker-rustfmt wurde vollständig neu gebaut und alle Prüfungen bestanden. Das zuvor entfernte Entwicklungsimage musste wieder aufgebaut werden. Ein erster isolierter Schema-Prüferstart benötigte korrigierte Pythonpfade; der erfolgreiche erneute Lauf ist separat protokolliert. Keine Hostpakete installiert; keine Modelle heruntergeladen. Docker meldet wie zuvor fehlende Swap-Limit-Unterstützung dieses Kernels, das gesetzte 4-GiB-RAM-Limit bleibt wirksam.

## Betrieb und Grenzen

Der vorhandene HA-Testcontainer nemotron-unified-stt bleibt bewusst auf seinem bisherigen Image und 65534:65534. Dieser Auftrag aktualisiert nur Projektdateien und ein getrenntes Phase5.2-Prüfimage; kein Austausch, Neustart, Netzwerkwechsel oder Auto-Update des vorhandenen Containers. Ein späterer Wechsel dieses Containers benötigt einen eigenen Auftrag.

Root-Bootstrap braucht bei cap_drop=ALL die beiden angegebenen Capabilities. Wer das Image mit --cap-drop ALL ohne die zwei Bootstrap-Rechte startet, muss stattdessen --user mit passenden PUID/PGID verwenden. Sonst wird der Start fehlschlagen; es gibt keinen Root-Fallback. Die frühere feste Compose-user-Zeile ist entfernt, damit sie PUID/PGID nicht übersteuert.

setpriv-Referenz: https://man7.org/linux/man-pages/man1/setpriv.1.html. Endpointing, Modellkontext und Wyoming-Partial-Unterstützung bleiben unverändert wie in docs/PHASE5_1.md; keine weiteren Schalter erfunden. Keine GitHub-/GHCR-Aktionen ausgeführt.
