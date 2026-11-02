# Nemotron Unified – Unraid-Integrationstest

Stand: 02.11.2026. Neuer, separat gestarteter Testcontainer. Kein GitHub-/GHCR-Publishing, kein Image-/Modelldownload, kein Modellkopieren, keine Änderung an Home Assistant, Moonshine, Kroko oder anderen bestehenden Containerkonfigurationen.

## Laufender Dienst

| Einstellung | Tatsächlicher Wert |
|---|---|
| Name | nemotron-unified-stt |
| Status | running / healthy |
| Image-Tag | nemotron-unified-rust-wyoming:phase6 |
| Verwendete feste Image-ID | sha256:cceb1003febcb079ead01a5bd10961e375b2da93f864e5cd1723a5e0bbd63dcd |
| Container-ID | 2e7e4ac10709143378e9494eb6a7b71bdfcf80930e02dd1908901f0e6e28269e |
| Netzwerk | Docker bridge |
| Veröffentlichte Adresse | 192.168.178.100:10310/TCP |
| Interner Listener | 0.0.0.0:10300/TCP |
| Restart-Policy | unless-stopped |
| Sprache / Provider / Threads | de / cpu / 2 |
| Laufzeitrechte | UID/GID 65534, read-only Root, cap-drop ALL, no-new-privileges |
| Grenzen | 4 GiB RAM, 4 CPU-Äquivalente, 128 PIDs, 120 s Audio, 8 Verbindungen |
| Native Zuführung / Payloadlimit | 20 ms maximal / 320000 Byte |
| Logging | info, LOG_TRANSCRIPTS=false, begrenzte Docker-Logrotation |

Das Image war bereits lokal gebaut und mit allen 32 Tests geprüft. Ein Neubau war nicht nötig. Der Start verwendet die unveränderliche Image-ID statt eines möglicherweise später umgebogenen Tags. Der vollständige tatsächlich ausgeführte Startbefehl ist nur lokal unter docs/evidence/unraid-integration/start-container.sh gespeichert; nicht in Git aufgenommen.

## Modelle

Hostverzeichnis: /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming/models/L37-runtime

Dieses vorhandene Verzeichnis ist read-only nach /models gemountet. MODEL_DIR=/models; alle optionalen Einzelpfade verwenden ihre Standarddateinamen. Die Dateien wurden weder kopiert noch verändert. Aktuelle SHA256 stimmen mit dem erfolgreichen Phase4-Export überein:

| Hostdatei | Containerpfad | SHA256 |
|---|---|---|
| /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming/models/L37-runtime/encoder.int8.onnx | /models/encoder.int8.onnx | 8e1b140b85900dcaede7e5fc05c1adfd48d4a0585e3b55ec2a10cded7042c96d |
| /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming/models/L37-runtime/decoder.onnx | /models/decoder.onnx | e5281215d86116e425191324830090922ec7732a34b1f5203d3b5a3564a20d97 |
| /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming/models/L37-runtime/joiner.onnx | /models/joiner.onnx | 7abd80133827b59dbd3b57c47242d6001607ed14acda5db36ae28d64a3de8af8 |
| /mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming/models/L37-runtime/tokens.txt | /models/tokens.txt | 94139a0b2134fd40664ca72260026fa8a073336bb2f062239c8ecde2c8031763 |

## Erreichbarkeit und echte Erkennung

Port 10310 war vor dem Start laut Host-Socket-/Docker-Belegung frei. Bindung ausschließlich an NAS-LAN-IP 192.168.178.100. Home Assistant läuft im Hostnetz. Daher wird die geprüfte NAS-IP verwendet, nicht der im Docker-Bridge-DNS nur eingeschränkt auflösbare Containername. Moonshine auf 10300 und Kroko auf 10321 bleiben unverändert.

Direkter Container-Healthcheck erfolgreich; Docker-Healthcheck healthy. Zusätzlich echte describe/info-Verhandlung und drei aufeinanderfolgende Erkennungen über offizielle, bereits in Home Assistant installierte Wyoming-Python-Klassen. Der Prüfprozess wurde per docker exec in Home Assistant ausgeführt, ohne Pakete zu installieren, Dateien dort zu schreiben oder die HA-Konfiguration anzupassen; PYTHONDONTWRITEBYTECODE=1 wurde nur für diesen Prozess gesetzt. Audio wurde als kleine vorhandene Referenzaufnahme über stdin zugespielt; keine Modellgewichte übertragen.

Referenz: menschliche CC0-Aufnahme „Einsteigen bitte!“ von Daniel Mietchen, 1,50025 s, PCM16/16 kHz/Mono. Tatsächliche Ergebnisse:

| Anfrage | Empfangener Text | Sprache | Anfragezeit s | Anfrage-RTF |
|---|---|---|---:|---:|
| 1 | Einsteigen bitte. | de | 0.686 | 0.457 |
| 2 | Einsteigen bitte. | de | 0.728 | 0.485 |
| 3 | Einsteigen bitte. | de | 0.697 | 0.465 |

Mittlere Anfrage-RTF 0.469; einschließlich TCP-Zuführung ohne Echtzeit-Pacing, Inferenz und Antwort, ohne Modellladen. Kein repräsentativer Befehlsbenchmark und noch kein vollständiger Assist-/Satellite-Test. Der Dienst meldet requires_external_vad=true und supports_transcript_streaming=false.

Serverlogs nach den Tests enthalten ausschließlich die Bereitschaftszeile, keine Backend-/Protokollfehler. Prozess stderr des HA-Prüfclients leer, OOMKilled=false. Docker meldete beim Start die bekannte fehlende Swap-Limit-Unterstützung des Unraid-Kernels; das RAM-Limit ist gesetzt. Alle 30 vorbestehenden Container haben unveränderte IDs, Status, Startzeitpunkte und Restart-Zähler; ausschließlich der neue Testcontainer kam hinzu.

## Home Assistant manuell einrichten

1. Einstellungen → Geräte & Dienste → Integration hinzufügen → Wyoming Protocol.
2. Host **192.168.178.100**, Port **10310** eintragen. Kein URL-Schema, kein interner Port 10300 und kein Containername erforderlich.
3. Unter Einstellungen → Sprachassistenten eine separate deutsche Testpipeline anlegen oder bewusst eine gewünschte Pipeline bearbeiten. Als Sprache-zu-Text **nemotron-unified-l37-int8**, Sprache Deutsch wählen. Andere Pipelines unverändert lassen.
4. Über Mikrofon/Satellite mehrere echte deutsche Befehle, Sprachende/VAD, Abbruch und Wiederverbindung testen. Diese Assist-Abnahme wurde noch nicht automatisch ausgeführt.

Offizielle Anleitung: https://www.home-assistant.io/integrations/wyoming/

Der neue Container bleibt gemäß Auftrag aktiv und verwendet unless-stopped. Er ist in der Unraid-Dockerübersicht sichtbar. Es wurde keine DockerMan-Benutzervorlage nach /boot kopiert und keine vorhandene Vorlage importiert/überschrieben. Diagnose: docker logs --tail=100 nemotron-unified-stt sowie docker exec nemotron-unified-stt nemotron-wyoming healthcheck. Manuelles späteres Beenden: docker stop --time 60 nemotron-unified-stt.

Lokale Rohbelege: docs/evidence/unraid-integration/ha-real-transcription.json, docs/evidence/unraid-integration/server.log, docs/evidence/unraid-integration/container-inspect.json und docs/evidence/unraid-integration/container-comparison.json. Diese Rohdaten sind durch ./.gitignore ausgeschlossen. Keine Git-Commits oder Pushes für diesen Test.
