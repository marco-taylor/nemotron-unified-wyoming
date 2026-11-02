# Unraid installieren und gespeicherte Icons umstellen

Aktueller Entwicklungsstand: docs/PHASE6.md. GitHub/GHCR und Raw-Icons sind noch nicht veröffentlicht. Lokale Builds funktionieren; bestehende Container werden hier nicht automatisch aktualisiert oder neu erstellt.

## Image und Modelle

Nach erfolgreichem GHCR-Workflow und bestätigtem anonymem Pull ist `ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:dev` der Entwicklungskanal. Einen `sha-COMMIT`-Tag oder Digest für feste Installationen verwenden. Bis dahin lokal bauen:

```sh
docker build --platform linux/amd64 -t nemotron-unified-rust-wyoming:dev .
```

Zusammengehörige Modellgewichte gemäß docs/MODELS.md separat bereitstellen und read-only nach `/models` mounten. Standard PUID=99 und PGID=100 muss alle Elternverzeichnisse betreten und Dateien lesen können. Der Entrypoint ändert keine Eigentümer oder Rechte. Keine pauschalen chown/chmod-Aktionen durchführen.

## DockerMan-Vorlage

config/unraid-template.xml ist die Projektvorlage. Bei einer neuen manuellen Installation unter einem freien Namen nach `/boot/config/plugins/dockerMan/templates-user/my-nemotron-unified-rust-wyoming.xml` kopieren und im Docker-Tab „Add Container“ auswählen. Vorhandene Benutzervorlagen vorher sichern und nicht überschreiben. Eine XML-Prüfung oder GitHub-Veröffentlichung bedeutet noch keine Aufnahme in Community Applications.

Repository für den lokalen Build auf `nemotron-unified-rust-wyoming:dev` setzen. Den voreingetragenen GHCR-Kanal erst nach erfolgreicher Veröffentlichung nutzen. Bridge, Privileged=false, Modellmount read-only; freier Hostport standardmäßig 10310 auf Containerport 10300/TCP. Keine GPU, kein Docker-Socket und kein Hostnetz erforderlich.

Alle 19 Variablen sind mit deutschen Beschreibungen sichtbar. Referenz: docs/PHASE5_2.md und config/variables.json. Bei Änderung von WYOMING_PORT auch den Target-Port der Vorlage ändern; WYOMING_HOST im normalen Bridge-Betrieb auf 0.0.0.0 belassen. Modell-Einzelpfade sind Containerpfade. Nur CPU und THREADS=1/2/4 unterstützt.

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

Die XML-Vorlage und das Image-Label `net.unraid.docker.icon` enthalten ausschließlich den geplanten Low-Q-Raw-Link:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/assets/icons/nemotron-lowq.png

HQ bleibt eine optionale Alternative im Repository:

https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/assets/icons/nemotron-hq.png

Beide Dateien sind lokal vorhanden. Die Links sind bis zum erfolgreichen Push nicht öffentlich nutzbar. Die neuen Icons enthalten visuell kein NVIDIA-Logo. Die öffentliche Historie enthält ausschließlich die neuen Grafiken; die ursprüngliche Historie ist lokal gesichert. Kein HQ-Link wird als Standard in CA, Docker-Übersicht oder Template eingesetzt. Low-Q wird nicht erneut komprimiert.

## Bereits installierte Anwendung: nur Icon-Metadaten vorbereiten

Eine aktualisierte Projektvorlage ersetzt keine gespeicherte Benutzervorlage. Zuerst nach Veröffentlichung den Low-Q-Link im Browser öffnen und Inhalt prüfen. Dann die eigene Vorlage unter `/boot/config/plugins/dockerMan/templates-user/` sichern und im Unraid-Editor ausschließlich ihren `<Icon>`-Wert auf die Low-Q-URL ändern. Dies bereitet zukünftige DockerMan-Verwendung vor und verändert den laufenden Container nicht.

Auf diesem Host wurde die Implementierung in `/usr/local/emhttp/plugins/dynamix.docker.manager/include/DockerClient.php` nur gelesen: `getIcon()` liest zuerst `<Icon>` aus der passenden Vorlage und verwendet erst danach das Containerlabel `net.unraid.docker.icon` als Fallback. Ein unverändertes Label am bestehenden Container muss daher für die Anzeige nicht zwingend geändert werden. Dockerlabels selbst sind bei bestehenden Containern unveränderlich und benötigen für eine dauerhafte Änderung einen separat geplanten Neubau.

Die zwei tatsächlich konfigurierten Icon-Caches sind `/var/lib/docker/unraid/images/` und `/usr/local/emhttp/state/plugins/dynamix.docker.manager/images/`. Für einen konkreten Container heißen die Dateien jeweils `CONTAINERNAME-icon.png`. Nach Sicherung der passenden Benutzervorlage und beider Cachedateien kann man ausschließlich diese beiden Dateien durch das verifizierte Low-Q-PNG ersetzen. Dann Docker-Seite und Browsercache neu laden. Das ändert Anzeige-Dateien, ohne den Container neu zu erstellen. Eine korrekt zugeordnete Vorlage mit neuer Low-Q-URL verhindert spätere Rückkehr zur alten URL; keine fremden Vorlagen ändern. DockerMan-Anzeigemetadaten liegen hier unter `/usr/local/emhttp/state/plugins/dynamix.docker.manager/docker.json`; sie speichern den lokalen Cachepfad und brauchen bei gleichem Cachedateinamen keine manuelle Änderung.

Für den derzeit per Docker gestarteten `nemotron-unified-stt` wurde keine passende gespeicherte Nemotron-Benutzervorlage gefunden. Bei einer späteren DockerMan-Verwaltung muss eine Vorlage bewusst passend zu Name und Repository angelegt werden. Kein automatischer Import und keine Annahme, dass eine neue Projekt-XML eine bestehende Installation migriert.

Änderungen über Docker → Edit → Advanced View → Icon URL können beim Anwenden einen Container-Neubau auslösen. Deshalb für eine reine Icon-Migration nicht ungeprüft „Apply“ verwenden. Im Auftrag wurden weder Benutzervorlagen, Metadaten, Caches noch Container verändert. Eine Veröffentlichung in CA benötigt zusätzlich die Aufnahme in den CA-Templatekatalog; die GitHub-XML allein stellt keinen CA-Eintrag her.

## Compose und Home Assistant

./.env.example nach ./.env kopieren, Modellpfad und freien Hostport prüfen. ./docker-compose.yml verwendet MODEL_DIR als Host-Mountquelle und `/models` im Container. Erst `docker compose config`, dann bewusst installieren. Lokal `IMAGE=nemotron-unified-rust-wyoming:dev`; GHCR erst nach bestätigter Verfügbarkeit. Nur dieser Dienst ist Bestandteil der Compose-Datei.

Home Assistant: Wyoming Protocol mit Unraid-LAN-IP und veröffentlichtem Hostport hinzufügen, anschließend eine deutsche Assist-Testpipeline auswählen. Details: docs/HOME_ASSISTANT.md. Internes VAD/Endpointing und Teiltranskripte fehlen; Home Assistant liefert audio-stop. Der bestehende nemotron-unified-stt bleibt bei Phase 6 unverändert.
