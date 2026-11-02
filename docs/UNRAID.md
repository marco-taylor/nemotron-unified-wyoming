# Unraid installieren und gespeicherte Icons umstellen

Aktueller Veröffentlichungs-/CA-Status: docs/PHASE12_PUBLICATION.md. Migration: docs/MIGRATION.md. Regulärer Imagekanal ist latest; dev bleibt zur Kompatibilität erhalten. Tagprüfung: docs/LATEST.md. Lokale Builds funktionieren; bestehende Container werden hier nicht automatisch aktualisiert oder neu erstellt.

## Image und Modelle

Nach erfolgreichem GHCR-Workflow und bestätigtem anonymem Pull ist `ghcr.io/marco-taylor/nemotron-unified-wyoming:latest` der reguläre Installationskanal. Einen `sha-COMMIT`-Tag oder Digest für feste Installationen verwenden. Alternativ lokal bauen:

```sh
docker build --platform linux/amd64 -t ghcr.io/marco-taylor/nemotron-unified-wyoming:latest .
```

Das persistente Modellverzeichnis als RW-Cache nach `/models` mounten. Fehlende oder beschädigte L37-Dateien lädt der Container aus dem festen GitHub-Release `models-l37-v1.0.0` und prüft jeden SHA256-Wert. Der erste Start benötigt ca. 693 MiB Download und dauert länger; erst nach geladenem Modell wird Wyoming healthy. Gültige vorhandene Modelle funktionieren offline und weiterhin mit RO-Mount. Details: docs/MODELS.md. Standard PUID=99 und PGID=100 muss Elternverzeichnisse betreten, vorhandene Dateien lesen und für Downloads im Cache schreiben können. Der Entrypoint ändert keine Eigentümer oder Rechte. Keine pauschalen chown/chmod-Aktionen durchführen.

## DockerMan-Vorlage

config/unraid-template.xml ist die Projektvorlage. Bei einer neuen manuellen Installation unter einem freien Namen nach `/boot/config/plugins/dockerMan/templates-user/my-nemotron-unified-wyoming.xml` kopieren und im Docker-Tab „Add Container“ auswählen. Vorhandene Benutzervorlagen vorher sichern und nicht überschreiben. Eine XML-Prüfung oder GitHub-Veröffentlichung bedeutet noch keine Aufnahme in Community Applications.

Repository für den lokalen Build auf `ghcr.io/marco-taylor/nemotron-unified-wyoming:latest` setzen. Den voreingetragenen GHCR-Kanal erst nach erfolgreicher Veröffentlichung nutzen. Bridge, Privileged=false, Modellmount RW nur zur Initialisierung; Dateisystem-Schreibsperre im eigentlichen STT-Prozess; freier Hostport standardmäßig 10310 auf Containerport 10300/TCP. Keine GPU, kein Docker-Socket und kein Hostnetz erforderlich.

Die vereinfachte Vorlage zeigt genau drei projektspezifische Grundeinstellungen. Unraids eigene Felder wie Containername, Repository und Netzwerkmodus bleiben Teil der Oberfläche. Dieser Stand ist noch nicht in CA veröffentlicht.

| Grundeinstellung | Standard |
|---|---|
| Wyoming-Hostport | `10310` → intern `10300/TCP` |
| Modellverzeichnis am Host | `/mnt/user/appdata/nemotron-unified-wyoming/models/L37-runtime` → `/models`, RW-Downloadcache; STT-Prozess danach ohne Dateiänderungen |
| CPU-Threads (`THREADS`) | `2` |

Ein Thread liefert gleichmäßigere Reaktionszeiten bei geringerer CPU-Last. Zwei Threads liefern den schnelleren Median bei höherer CPU-Last. Vier Threads werden auf dem Intel N100 nicht empfohlen. Es gibt keine automatische Änderung bestehender Threadwerte.

Unter **„Mehr Einstellungen anzeigen“** liegen die sieben mit `Display="advanced"` gekennzeichneten Variablen:

| Variable | Standard |
|---|---|
| `MAX_AUDIO_SECONDS` | `120` |
| `MAX_CONNECTIONS` | `8` |
| `CLIENT_TIMEOUT_SECONDS` | `30` |
| `LOG_LEVEL` | `info` |
| `LOG_TRANSCRIPTS` | `false` |
| `PUID` | `99` |
| `PGID` | `100` |

In Unraid 7.3.4 ordnet `Display="advanced"` diese Einträge dem zunächst eingeklappten Zusatzbereich zu. Dieser Bereich ist über „Mehr Einstellungen anzeigen“ erreichbar; er ist nicht mit dem globalen Schalter „Advanced View“ für sämtliche Docker-Eigenschaften gleichzusetzen.

### Interne Defaults und manuelle Sonderwerte

Elf technische Variablen sind nicht mehr als eigene Template-Einträge vorhanden. Server, Image und Entrypoint behalten ihre bisherigen Defaults: `WYOMING_HOST=0.0.0.0`, `WYOMING_PORT=10300`, `LANGUAGE=de`, `STT_DEVICE=cpu`, `MODEL_DIR=/models`, `MAX_AUDIO_CHUNK_BYTES=320000` und `INFERENCE_CHUNK_MS=20`. Ohne Einzelpfade werden `/models/encoder.int8.onnx`, `/models/decoder.onnx`, `/models/joiner.onnx` und `/models/tokens.txt` verwendet; keine Suche in beliebigen Verzeichnissen. Beim Containerstart prüft die Initialisierung die festen SHA256-Werte und lädt nur betroffene Dateien aus dem versionierten Modell-Release nach. Verwaiste eigene temporäre Downloads werden unter Sperre bereinigt; keine Löschung unbekannter Dateien oder Originalsicherungen.

Alle 19 Variablen bleiben vollständig unterstützt und dokumentiert in docs/PHASE5_2.md, docs/CONFIGURATION.md und config/variables.json. Für Sonderfälle lassen sich über Unraids Funktion zum Hinzufügen eines Pfads, Ports, einer Variablen, eines Labels oder Geräts wieder **Variable**-Einträge mit dem exakten Schlüssel ergänzen, beispielsweise `ENCODER_PATH` oder `INFERENCE_CHUNK_MS`. Bereits vorhandene Einträge bearbeiten, keine doppelten Schlüssel anlegen. Leere optionale Einzelpfade bedeuten Standarddateien; Modell-Einzelpfade sind Containerpfade. Andere Sprache und GPU bleiben nicht unterstützt.

Bei manuellem `WYOMING_PORT` muss im Bridge-Modus auch der interne Target-Port der Portzuordnung denselben Wert bekommen. `WYOMING_HOST` muss für die Weiterleitung im Container erreichbar sein; normalerweise `0.0.0.0`. Bei `MODEL_DIR`-Sonderwerten müssen Mount-Ziel und/oder die vier Einzelpfade weiterhin zusammenpassen. Der sichtbare Modellverzeichniswert bezeichnet ausschließlich den Hostpfad.

### Neuinstallation und bestehende Container

**Vor einem bewussten Vorlagenwechsel die eigene Benutzervorlage und alle benutzerdefinierten Werte sichern. Nicht einfach die gespeicherte Vorlage durch die neue Projektdatei ersetzen: Dabei würden abweichende Ports, Pfade, Identitäten und manuell ergänzte Variablen verloren gehen.** Gespeicherte Benutzervorlagen liegen unter `/boot/config/plugins/dockerMan/templates-user/`.

Bei einer Neuinstallation mit der vereinfachten Projektvorlage gelten die drei Grundeinstellungen und sieben erweiterten Defaults. Bei einem normalen Image-Update werden auf dem geprüften Unraid 7.3.4 die vorhandenen gespeicherten Benutzervorlagen verwendet. Die vorhandenen 19 Variablen und manuell ergänzten Werte bleiben damit bestehen; die Oberfläche wird nicht automatisch auf drei Grundeinstellungen reduziert. Das gilt auch für gültige bisherige Werte der elf jetzt weggelassenen Einträge. Die Repo-XML migriert keine laufenden Container.

Wer die vereinfachte Ansicht später bewusst übernehmen möchte, sollte zunächst die gesicherte alte und die neue Vorlage vergleichen, jeden Sonderwert übernehmen und die erzeugten Docker-Argumente prüfen. Nur explizite Werte entfernen, die tatsächlich dem gewünschten Default entsprechen. Eine Änderung über „Apply“ kann einen Container neu erstellen und ist separat zu planen. Die Veröffentlichung führt keine solche Migration durch. Die GUI-Version und zusätzliche Plugins können das Verhalten beeinflussen; die Sicherung ist auch bei anderen Unraid-Versionen erforderlich.

### Bridge- und Host-Netzwerk

Empfohlen bleibt **Bridge**: Home Assistant verbindet sich mit der Unraid-IP und dem sichtbaren Hostport, standardmäßig `10310`; der Server hört intern auf `10300`. Der Test verwendet freie, ausschließlich auf Loopback gebundene Hostports, damit bestehende Belegungen unverändert bleiben.

Im **Host-Modus** ist Docker-Portmapping wirkungslos. Ohne manuell ergänztes `WYOMING_PORT` hört der Server direkt auf Hostport `10300`, und Home Assistant muss diesen Port nutzen. Ein sichtbarer Hostportwert `10310` ändert das nicht. Bei einer bestehenden Host-Installation mit anderem Serverport den bisherigen `WYOMING_PORT` erhalten und dessen Verfügbarkeit prüfen. Kein Wechsel des Netzwerkmodus erfolgt automatisch.

Die Extra Parameters erhalten: read-only, cap-drop=ALL, ausschließlich SETUID/SETGID zum kurzen Identitätswechsel, no-new-privileges, Speicher-/CPU-/PID-Grenzen, Logrotation und 60 Sekunden Stopfrist. Der Server wird per exec PID 1 mit PUID/PGID, ohne effektive Capabilities. Optional `--user 99:100` mit passenden PUID/PGID und ohne Capabilities verwenden. Keine alte feste user-Zeile 65534:65534 für das neue Bootstrap-Image übernehmen.

Healthcheck:

```sh
docker exec --user 99:100 CONTAINER nemotron-wyoming healthcheck
docker exec --user 99:100 CONTAINER cat /proc/1/status
```

Docker-Inspect User=0:0 beschreibt nur den Bootstrap. Die tatsächlichen IDs, CapEff und NoNewPrivs in `/proc/1/status` prüfen.

## Icons: ausschließlich Low-Q als Standard

Vorhandene lokale Dateien:

| Variante | Pfad | Größe | Eigenschaften |
|---|---|---:|---|
| Low-Q | assets/icons/nemotron-lowq.png | 82.756 Byte | PNG, 256 × 256, transparent |
| HQ | assets/icons/nemotron-hq.png | 1.560.271 Byte | PNG, 1254 × 1254, transparent |

Die XML-Vorlage und das Image-Label `net.unraid.docker.icon` enthalten ausschließlich den öffentlichen Low-Q-Raw-Link:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-wyoming/main/assets/icons/nemotron-lowq.png

HQ bleibt eine optionale Alternative im Repository:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-wyoming/main/assets/icons/nemotron-hq.png

Beide Dateien sind lokal vorhanden. Beide Links sind öffentlich erreichbar und bytegenau geprüft. Die neuen Icons enthalten visuell kein NVIDIA-Logo. Die öffentliche Historie enthält ausschließlich die neuen Grafiken; die ursprüngliche Historie ist lokal gesichert. Kein HQ-Link wird als Standard in CA, Docker-Übersicht oder Template eingesetzt. Low-Q wird nicht erneut komprimiert.

## Bereits installierte Anwendung: nur Icon-Metadaten vorbereiten

Eine aktualisierte Projektvorlage ersetzt keine gespeicherte Benutzervorlage. Zuerst nach Veröffentlichung den Low-Q-Link im Browser öffnen und Inhalt prüfen. Dann die eigene Vorlage unter `/boot/config/plugins/dockerMan/templates-user/` sichern und im Unraid-Editor ausschließlich ihren `<Icon>`-Wert auf die Low-Q-URL ändern. Dies bereitet zukünftige DockerMan-Verwendung vor und verändert den laufenden Container nicht.

Auf diesem Host wurde die Implementierung in `/usr/local/emhttp/plugins/dynamix.docker.manager/include/DockerClient.php` nur gelesen: `getIcon()` liest zuerst `<Icon>` aus der passenden Vorlage und verwendet erst danach das Containerlabel `net.unraid.docker.icon` als Fallback. Ein unverändertes Label am bestehenden Container muss daher für die Anzeige nicht zwingend geändert werden. Dockerlabels selbst sind bei bestehenden Containern unveränderlich und benötigen für eine dauerhafte Änderung einen separat geplanten Neubau.

Die zwei tatsächlich konfigurierten Icon-Caches sind `/var/lib/docker/unraid/images/` und `/usr/local/emhttp/state/plugins/dynamix.docker.manager/images/`. Für einen konkreten Container heißen die Dateien jeweils `CONTAINERNAME-icon.png`. Nach Sicherung der passenden Benutzervorlage und beider Cachedateien kann man ausschließlich diese beiden Dateien durch das verifizierte Low-Q-PNG ersetzen. Dann Docker-Seite und Browsercache neu laden. Das ändert Anzeige-Dateien, ohne den Container neu zu erstellen. Eine korrekt zugeordnete Vorlage mit neuer Low-Q-URL verhindert spätere Rückkehr zur alten URL; keine fremden Vorlagen ändern. DockerMan-Anzeigemetadaten liegen hier unter `/usr/local/emhttp/state/plugins/dynamix.docker.manager/docker.json`; sie speichern den lokalen Cachepfad und brauchen bei gleichem Cachedateinamen keine manuelle Änderung.

Für den derzeit per Docker gestarteten `nemotron-unified-stt` wurde keine passende gespeicherte Nemotron-Benutzervorlage gefunden. Bei einer späteren DockerMan-Verwaltung muss eine Vorlage bewusst passend zu Name und Repository angelegt werden. Kein automatischer Import und keine Annahme, dass eine neue Projekt-XML eine bestehende Installation migriert.

Änderungen über Docker → Edit → Advanced View → Icon URL können beim Anwenden einen Container-Neubau auslösen. Deshalb für eine reine Icon-Migration nicht ungeprüft „Apply“ verwenden. Im Auftrag wurden weder Benutzervorlagen, Metadaten, Caches noch Container verändert. Eine Veröffentlichung in CA benötigt zusätzlich die Aufnahme in den CA-Templatekatalog; die GitHub-XML allein stellt keinen CA-Eintrag her.

## Compose und Home Assistant

./.env.example nach ./.env kopieren, Modellpfad und freien Hostport prüfen. ./docker-compose.yml verwendet MODEL_DIR als Host-Mountquelle und `/models` im Container. Erst `docker compose config`, dann bewusst installieren. Lokal `IMAGE=ghcr.io/marco-taylor/nemotron-unified-wyoming:latest`. Der reguläre GHCR-Kanal ist latest; Ergebnisse des anonymen Pulls stehen in docs/LATEST.md. Nur dieser Dienst ist Bestandteil der Compose-Datei.

Home Assistant: Wyoming Protocol mit Unraid-LAN-IP und veröffentlichtem Hostport hinzufügen, anschließend eine deutsche Assist-Testpipeline auswählen. Details: docs/HOME_ASSISTANT.md. Internes VAD/Endpointing und Teiltranskripte fehlen; Home Assistant liefert audio-stop. Der bestehende nemotron-unified-stt bleibt bei Phase 6 unverändert.


## Schreibschutz und Modellherkunft

Der RW-Mount erlaubt ausschließlich der Initialisierung den Download als PUID/PGID. Vor exec des Rust-Servers blockiert ein zusätzlicher seccomp-Filter Dateiänderungen durch diesen Prozess und seine Threads. CapEff/CapPrm/CapAmb bleiben 0, NoNewPrivs bleibt 1; es gibt kein automatisches chown bestehender Modelle. Lizenz, NVIDIA-Modellkarte, Herkunft und Exportinformationen befinden sich im Image unter `/usr/share/licenses/nemotron-wyoming/model` sowie im öffentlichen Modell-Release. NVIDIA trainierte die Gewichte; dieses Projekt exportierte und quantisierte den L37-Satz, ohne eigenes Training.
