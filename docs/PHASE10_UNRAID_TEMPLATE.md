# Phase 10 – Unraid-Template vereinfachen

Stand: 2. November 2026. Lokaler Entwicklungszweig: `feature/unraid-template-simplification`. Ausgangsrevision: `d7af454c269da902b220ea50d23d256220edb376` auf `main`. Keine Veröffentlichung, kein Merge und keine Änderung am bestehenden STT-Container.

## 1. Getrennte Arbeitsstände

Beim Start war `feature/latency-optimization` aktiv. Die Phase-9-Änderung in `src/server.rs` sowie die noch unversionierten Phase-8-/Phase-9-Berichte und Werkzeuge wurden vor dem Branchwechsel gesichert:

* Tracked Diff: `/mnt/nvme/appdata/codex-workspace/nemotron-phase10-backups/phase9-working-tree.patch`.
* Unversionierte Dateien: `/mnt/nvme/appdata/codex-workspace/nemotron-phase10-backups/phase8-9-untracked.tar.gz`, mit `tar --compare` gegen die Originale geprüft.
* Vollständiger Git-Stash einschließlich unversionierter Dateien: `3c4b40dba63e722e205cea9d33742372eb5d7827`, Bezeichnung „Phase 8 and Phase 9 preserved before isolated Phase 10“.

Danach wurde der neue Branch ausdrücklich von `main` angelegt. Die Phase-9-Socket-Optimierung wurde weder geändert noch versehentlich in Phase 10 aufgenommen; sie ist im Stash unverändert erhalten. Der Phase-9-Branch bleibt bestehen. Die ignorierten Rohbelege der vorherigen Phasen liegen weiterhin lokal vor.

Für eine spätere Wiederaufnahme von Phase 9 zuerst die Phase-10-Arbeiten separat sichern oder committen und einen sauberen Arbeitsbaum herstellen, dann auf `feature/latency-optimization` wechseln und den oben genannten Stash bewusst anwenden. Den Stash nicht ungeprüft auf den Phase-10-Branch anwenden und bis zur erfolgreichen Wiederaufnahme nicht löschen. Es wird hier keine solche Rückmigration ausgeführt.

## 2. Neue Oberfläche

Die Änderung an config/unraid-template.xml betrifft ausschließlich Darstellung, Einträge und deren Beschreibungen. Es bleiben zehn Config-Elemente: **drei normal sichtbar, sieben erweitert**. Unraids allgemeine Containerfelder wie Name, Image oder Netzwerkmodus bleiben Teil der Weboberfläche.

| Normal sichtbare Einstellung | Standard | Zuordnung |
|---|---|---|
| Wyoming-Hostport | `10310` | Bridge-Port `10310:10300/tcp` |
| L37-Modellverzeichnis | `/mnt/user/appdata/nemotron-unified-rust-wyoming/models/L37-runtime` | `/models`, `Mode="ro"` |
| `THREADS` | `2` | `Display="always"` |

Die Threadbeschreibung erläutert ausdrücklich: ein Thread für gleichmäßigere Reaktionszeit und geringere CPU-Last, zwei für schnelleren Median bei höherer Last, vier auf Intel N100 nicht empfohlen. Der Default bleibt wie angefordert **2**; vorhandene Werte werden nicht automatisch geändert.

| Erweiterte Variable | Default | Darstellung |
|---|---|---|
| `MAX_AUDIO_SECONDS` | `120` | `advanced` |
| `MAX_CONNECTIONS` | `8` | `advanced` |
| `CLIENT_TIMEOUT_SECONDS` | `30` | `advanced` |
| `LOG_LEVEL` | `info` | `advanced` |
| `LOG_TRANSCRIPTS` | `false` | `advanced` |
| `PUID` | `99` | `advanced` |
| `PGID` | `100` | `advanced` |

Die installierte Unraid-Version ist **7.3.4**. Ihr Quellcode in `/usr/local/emhttp/plugins/dynamix.docker.manager/include/CreateDocker.php` erkennt `Display="advanced"` und legt diese Einträge im zunächst eingeklappten Bereich `configLocationAdvanced` ab. Der Bereich wird über „Mehr Einstellungen anzeigen“ geöffnet. Der globale Advanced-View-Schalter ist davon zu unterscheiden. Die [offizielle CA-Startervorlage](https://github.com/unraid/unraid-community-apps-starter/blob/main/templates/example-app.xml) verwendet diese Darstellungsart ebenfalls; die [offizielle WebGUI-Implementierung](https://github.com/unraid/webgui/blob/master/emhttp/plugins/dynamix.docker.manager/include/CreateDocker.php) zeigt die Verarbeitung.

## 3. Elf entfernte Template-Einträge und Default-Nachweis

Keine Variable wird aus Rust oder Entrypoint entfernt. Die technische Liste config/variables.json, beide Umgebungsbeispiele und ./docker-compose.yml enthalten weiterhin alle 19 Variablen: 17 verarbeitet Rust, zwei der Entrypoint.

| Aus dem Template entfernt | Unverändertes Verhalten ohne Eintrag | Herkunft |
|---|---|---|
| `WYOMING_HOST` | `0.0.0.0` | Image-ENV und Rust-Fallback |
| `WYOMING_PORT` | `10300` | Image-ENV und Rust-Fallback |
| `LANGUAGE` | `de` | Image-ENV und Rust-Fallback |
| `STT_DEVICE` | `cpu` | Rust-Fallback |
| `MODEL_DIR` | `/models` | Image-ENV und Rust-Fallback |
| `ENCODER_PATH` | `/models/encoder.int8.onnx` | Fehlender/leer gelassener Override → Standarddatei |
| `DECODER_PATH` | `/models/decoder.onnx` | Fehlender/leer gelassener Override → Standarddatei |
| `JOINER_PATH` | `/models/joiner.onnx` | Fehlender/leer gelassener Override → Standarddatei |
| `TOKENS_PATH` | `/models/tokens.txt` | Fehlender/leer gelassener Override → Standarddatei |
| `MAX_AUDIO_CHUNK_BYTES` | `320000` Byte | Rust-Fallback; gerade PCM16-Payloadgrenze |
| `INFERENCE_CHUNK_MS` | `20` ms | Rust-Fallback für native Zuführung |

Der Default-Nachweis erfolgte **vor** dem Entfernen: Codeprüfung von src/config.rs, src/inference.rs, ./Dockerfile und scripts/docker-entrypoint.sh sowie Start des vorhandenen Images ohne eine einzige explizite `--env`-Angabe. Der Server meldete `0.0.0.0:10300`, `threads=2`, `max_clients=8`, `max_audio=120s`. Modelle wurden aus dem Default-Mount geladen, drei echte deutsche Anfragen erkannt, der Host-Port erreicht und eine deklarierte Payload über 320000 Byte vor dem Payload-Lesen abgewiesen. Tatsächliche UID/GID waren 99:100 bei leeren Capabilities und NoNewPrivs=1. Der Erfolg ist unter docs/evidence/phase10/defaults-verified/ belegt.

Die vier Dateinamen werden deterministisch relativ zu `/models` aufgelöst, nicht durch eine Suche nach beliebigen Modellpaketen. Der Test bindet die vorhandenen Gewichte aus dem Projekt schreibgeschützt ein. Der neue vorgeschlagene Hostpfad wurde weder automatisch angelegt noch mit Gewichten befüllt. Neue Anwender müssen dort selbst ein zusammengehöriges L37-Paket bereitstellen.

Die Prüfungen bestätigen korrekte bereits vorhandene Defaults; eine Änderung oder zusätzliche Kompatibilitätsschicht im Runtime-Code ist nicht erforderlich. Audio-Payloadgrenzen, native Chunk-Zuführung und die inkrementelle L37-Verarbeitung bleiben unverändert.

## 4. Neuinstallation, Update und Sonderkonfiguration

### Neuinstallation

Die lokale Vorlage kann bei einer späteren Freigabe mit ihren drei Grundeinstellungen verwendet werden. Bridge, read-only Modellmount, unprivilegierter Dauerbetrieb und vorhandene Sicherheitsparameter bleiben erhalten. Sieben weitere Werte stehen im Zusatzbereich. Die restlichen elf Werte müssen normale Anwender nicht konfigurieren.

### Bestehende Installationen

**Gespeicherte Benutzervorlagen niemals ungeprüft mit der neuen Projektdatei überschreiben. Zuerst die Vorlage und sämtliche Sonderwerte sichern.** Ein vollständiger Austausch würde benutzerdefinierte Ports, Pfade, UID/GID oder zusätzliche Variablen durch neue Defaults ersetzen beziehungsweise entfernen. Diese Phase nimmt keine Migration vor.

Unraid speichert anwendungsspezifische Vorlagen unter `/boot/config/plugins/dockerMan/templates-user/`, wie auch die [offizielle CA-Dokumentation](https://docs.unraid.net/community-applications/) beschreibt. Die hier installierten Skripte `/usr/local/emhttp/plugins/dynamix.docker.manager/scripts/update_container` und `/usr/local/emhttp/plugins/dynamix.docker.manager/scripts/rebuild_container` verwenden die gespeicherte Benutzervorlage über `getUserTemplate()` und `xmlToCommand()`. Die Methode `updateUserTemplate()` in `/usr/local/emhttp/plugins/dynamix.docker.manager/include/DockerClient.php` kehrt in dieser Version unmittelbar zurück; ihr alter Remote-Abgleich ist deaktiviert.

Damit bleiben bei einem normalen Image-Update auf dem geprüften System die gespeicherten alten Einträge erhalten. Die neue reduzierte Oberfläche wird dadurch nicht automatisch übernommen. Das gilt auch für die elf aus der Projektvorlage entfernten Variablen und andere manuell ergänzte Schlüssel. Keine gespeicherte Benutzervorlage und kein laufender Container wurden für diese Prüfung verändert. Andere Unraid-/Plugin-Versionen sind nicht pauschal als identisch abgenommen.

Wer die Oberfläche bewusst vereinfachen möchte, muss die Vorlagen vergleichen, individuelle Werte und zugehörige Mount-/Portziele übernehmen und vor „Apply“ die erzeugten Argumente prüfen. Nur Werte entfernen, die tatsächlich dem gewünschten Default entsprechen. „Apply“ kann einen Container neu erstellen und ist separat zu planen.

### Manuell ergänzte Variablen

Unraids Funktion zum Hinzufügen eines Konfigurationseintrags kann weiterhin Variable-Einträge mit den exakten bisherigen Schlüsseln erzeugen. Keine doppelten Schlüssel anlegen. Vier absolute Modellpfade können wie bisher einen abweichenden `MODEL_DIR` übersteuern. Bei geändertem Basisverzeichnis müssen Mountziel und relative Dateipfade zusammenpassen.

### Bridge und Host

Bridge bleibt Standard: Hostport 10310 wird auf internen Port 10300 weitergeleitet. Freie Hostports dürfen abweichen, ohne `WYOMING_PORT` zu ändern. Der Runtime-Test veröffentlicht ausschließlich einen vom Betriebssystem vergebenen Loopback-Port und prüft ihn vom Host aus; die reale produktive Portbelegung bleibt unangetastet.

Im Host-Modus gibt es kein wirksames Docker-Portmapping. Ohne Sonderwert hört der Server auf Hostport 10300; Home Assistant muss dann diesen Port benutzen. Ein sichtbarer Hostportwert 10310 ändert das nicht. Für einen anderen Host-Netz-Port ist `WYOMING_PORT` manuell zu ergänzen. Bei manuell verändertem Serverport im Bridge-Modus muss auch der interne Target-Port der Portzuordnung angepasst werden. Der native Unraid-Command-Generator wurde für Bridge, Host und ein manuelles Port-/Pfadbeispiel geprüft; echtes Host-Networking wurde wegen möglicher Kollisionen mit bestehenden Diensten nicht gestartet.

### Dateiberechtigungen

99:100 bleibt der Default. Die Identität benötigt Leserecht auf allen vier Dateien und Suchrecht auf den Elternverzeichnissen. Andere gültige PUID/PGID bleiben möglich; 0 und ungültige Werte bleiben abgewiesen. Die Anwendung verändert keine Besitzer und keine Dateirechte. Wenn ein Sondernutzer nicht lesen darf, die Berechtigungen gezielt außerhalb der Anwendung prüfen; keine pauschalen chown-/chmod-Aktionen. Der reale Kompatibilitätstest mit UID/GID 12345:23456 konnte die vorhandenen Gewichte lesen.

## 5. Tests und Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| XML-Syntax mit `xmllint` | Bestanden |
| Config-Vollständigkeit und Sichtbarkeit | Genau 10 Einträge: 3 normal, 7 erweitert; 8 Variablen |
| Elf entfernte Schlüssel | Exakte Menge geprüft, keine verbliebenen versteckten Einträge |
| Doppelte Einträge/Variablen | Keine; Typschlüssel und Variablennamen eindeutig |
| Defaults | Alle XML-Werte gegen config/variables.json, interne Defaults gegen Quellcode und reale Minimalinstallation geprüft |
| Installierter Unraid-Parser | Bestanden; 3/7-Sichtbarkeit, read-only Mount, Bridge-Port und Host-Verhalten |
| Manuell ergänzte Einträge | Port, Modellpfad und Chunkwert im erzeugten Kommando erhalten; Port-Target passend angepasst |
| Minimaler Docker-Start ohne explizite Variablen | Bestanden; Hostmapping, UID/GID, Healthcheck, drei deutsche Transkriptionen |
| Neue Vorlage mit acht Variablen/defaults | Bestanden; gleiche echte Inferenz und Sicherheitsmerkmale |
| Bisherige Konfiguration mit allen 19 Variablen | Bestanden; andere UID/GID, Port, vier absolute Modellpfade, Limits und Chunkzuführung |
| Rückwärtskompatibler Payload-Override | 128000 Byte, Überschreitung verständlich abgewiesen |
| Runtime-Preflight | Versionsaufruf, fehlende Modelle, ungültige Threadzahl, Modellprüfung und beschädigter Testdecoder korrekt behandelt |
| Konfigurationsschema/19er-Parität | Compose-Schema, XML, Workflow-Regeln und vollständige Beispiele bestanden |
| Shutdown | Exitcode 0 bei den isolierten Serverläufen |

Die primären Testwerkzeuge sind scripts/test-unraid-minimal.sh, tests/unraid_minimal.py, tests/unraid_template.php und die angepasste Prüfung scripts/validate_configs.py. Der Unraid-PHP-Test erzeugt ausschließlich Befehlsstrings und ruft `xmlToCommand(..., false)` auf; es werden keine Hostpfade angelegt und keine generierten Docker-Kommandos ausgeführt. Starten der echten Testcontainer erfolgt ausschließlich durch das separate Testskript mit eigenen Namen und freien Ports. Reproduktion: docs/TESTS.md.

Die früheren lokalen Build-/Checks-Images waren vor Phase 10 bereits entfernt. Deshalb wurde keine Rust-Release-/Clippy-/Unit-Test-Pipeline neu gebaut. Es gibt keinerlei Rust-, Cargo-, Entrypoint- oder Dockerfile-Änderung. Die vorhandenen Konfigurationstests tests/configuration.rs wurden gelesen; die Phase-10-Mindestprüfungen erfolgen zusätzlich über statische Vertragsprüfungen und das unveränderte echte Runtime-Image. Es wurde kein Image gebaut, getaggt oder veröffentlicht.

Für den Python-Testinterpreter wurde ein bereits vorhandenes ESPHome-Image in eigenen Wegwerfcontainern verwendet; der ESPHome-Dienst wurde nicht angesprochen. Erste Testumgebungsversuche mit entfernten Buildimages beziehungsweise dem Python-Interpreter des HA-Basisimages waren nicht nutzbar. Die offizielle Wyoming-Eventkodierung wird ohne die unter Python 3.14 fehlende Audio-Konvertierungsbibliothek verwendet. Die benötigten Schema-Testpakete wurden nur in einem temporären Containerdateisystem installiert. Ein anfangs fehlgeschlagener PHP-Dry-run war durch Unraids automatischen Wechsel des CLI-Arbeitsverzeichnisses bedingt; der endgültige Aufruf deaktiviert ausschließlich für den Test `auto_prepend_file`. Die endgültigen Prüfungen bestehen.

## 6. Dokumentation und Freigabestatus

Aktualisiert sind ./README.md, docs/UNRAID.md, docs/CONFIGURATION.md und docs/TESTS.md. docs/PHASE5_2.md behält seine vollständige technische 19er-Tabelle und historischen Ergebnisse, mit einem Hinweis zur abweichenden Phase-10-Oberfläche. ./docker-compose.yml, beide Umgebungsbeispiele, config/variables.json sowie Rust und Entrypoint bleiben unverändert.

**Status: lokal technisch zur Veröffentlichung vorbereitet; Veröffentlichung wartet auf die Nutzerfreigabe.** Die Parser-/Schema-/Runtimeprüfungen ersetzen keinen öffentlichen CA-Submission-Scan oder eine manuelle Abnahme der veröffentlichten GUI. Es gibt keinen bekannten lokalen Funktionsblocker. Keine gespeicherte Installation wird automatisch umgestellt. Kein Merge nach `main`, kein GitHub-Push, kein GHCR-Upload und keine CA-Katalogänderung werden in dieser Phase vorgenommen.

**Bestehender Betriebsbefund:** Der vorhandene Container `nemotron-unified-rust-wyoming` war bereits bei Beginn der Phase **beendet (`exited`) und `unhealthy`**. Dieser Zustand bleibt unverändert. Seine letzten Servermeldungen lauten `runtime: missing model file: /models/encoder.int8.onnx`. Die gespeicherte Konfiguration bindet `/mnt/user/appdata/nemotron-unified-rust-wyoming/models/L37-runtime` read-only nach `/models` ein; die Einzelpfade sind leer. Das ist ein bereits bestehendes Bereitstellungsproblem und wird durch eine vereinfachte Oberfläche nicht behoben. Die erfolgreichen isolierten Tests verwenden ausdrücklich die vorhandenen vollständigen Gewichte im Projekt. Es wurden weder Modelle in das produktive Verzeichnis kopiert noch der bestehende Container gestartet. Die lokale Template-Prüfung ist keine Freigabe des bestehenden Betriebszustands.

Für eine spätere reine Template-Veröffentlichung ist der Veröffentlichungsweg gesondert festzulegen: Der bestehende Workflow .github/workflows/publish-ghcr.yml reagiert auf Pushes nach `main` und kann dabei auch GHCR aktualisieren. Dieser Workflow wird hier nicht geändert oder gestartet. Eine spätere Freigabe des Templates ist daher nicht automatisch eine Freigabe für einen neuen Image-Build oder ein neues `latest`.

## 7. Abschließende Sicherheitskontrolle

Die Abschlussprüfung ist erfolgreich:

* Alle **31 vorbestehenden Container** haben unveränderte IDs, Konfigurationen, Host-Konfigurationen, Mounts, Startzeiten, Restart-Zähler, Laufzustände und Health-Status. Der vorhandene Nemotron-Container bleibt wie zu Beginn **beendet und unhealthy**; der bereits bestehende Modellfehler ist oben dokumentiert. Kein eigener Phase-10-Testcontainer ist übrig.
* SHA256-Prüfung aller Rust-Dateien, von ./Cargo.toml, ./Cargo.lock, ./Dockerfile, scripts/docker-entrypoint.sh, config/variables.json und ./docker-compose.yml: unverändert. Alle vier Modell-Dateihashes stimmen mit Phase 8 überein.
* Image-ID und Registry-Digest-Zuordnung von `latest` sind unverändert. Kein Image wurde gebaut, getaggt oder veröffentlicht.
* `main` bleibt auf `d7af454c269da902b220ea50d23d256220edb376`. Der aktive Branch ist `feature/unraid-template-simplification`; Änderungen sind lokal und noch nicht committet. Der gesicherte Phase-9-Stash-Diff ist bytegleich mit dem zuvor gesicherten Patch. Die Phase-9-Optimierung wurde nicht verändert.
* XML-Syntax, nativer Unraid-Dry-run, vollständige Konfigurationsprüfung, Python-/PHP-/Shell-Syntax und `git diff --check` bestehen. Die Abschlussdaten stehen unter docs/evidence/phase10/safety-summary.json. Rohbelege bleiben unter docs/evidence/phase10/ ignoriert und lokal.

**Ergebnis:** Drei Grundeinstellungen, sieben erweiterte Variablen und elf ausschließlich aus der Oberfläche entfernte Einträge sind umgesetzt. Alle 19 technischen Variablen und ihre Defaults bleiben erhalten. Bestehende gültige Sonderkonfigurationen funktionieren weiterhin; eine sichere Übernahme der neuen Ansicht erfordert einen bewussten Vorlagenvergleich. Die Veröffentlichung wartet auf die ausdrückliche Freigabe.
