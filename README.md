# Nemotron Unified Rust Wyoming

Deutscher Speech-to-Text-Server für Home Assistant und Unraid auf **linux/amd64 mit CPU/AVX2**. Rust verarbeitet Wyoming-TCP, Sitzungen und Audiolimits. Die sichere sherpa-onnx-Anbindung lädt NVIDIA Nemotron Labs Unified ASR 0.6B als geprüften L37-Export mit INT8-Encoder über ONNX Runtime. Python wird nur für Entwicklung und Tests benötigt.

Entwicklungsstand, **kein offizieller v1.0.0-Release**. Repository-Ziel: https://github.com/marco-taylor/nemotron-unified-rust-wyoming. Die Veröffentlichung wartet auf die Entscheidung zur Bereinigung der alten Icon-Historie; Einzelheiten in docs/PHASE6.md. Die Cargo-Paketversion 1.0.0 bezeichnet noch keinen veröffentlichten Release.

## Funktionen und Grenzen

Der Server lädt das Modell einmal und verarbeitet wiederholte Wyoming-Anfragen. Unterstützt werden `describe`/`info`, `transcribe`, `audio-start`, `audio-chunk`, `audio-stop`, finale `transcript`-Antworten und gerahmte Fehler. Audio: PCM-S16LE, 16 kHz, Mono. Begrenzte Verbindungen, Framegröße, Audiodauer und Zeitlimits schützen den Dienst. Native Inferenz wird serialisiert. Healthcheck prüft den laufenden Wyoming-Dienst; SIGTERM/SIGINT beenden ihn geordnet.

**Nicht implementiert:** internes Endpointing/VAD, Wyoming-Teiltranskripte, alternative L37-Kontexte, GPU-Provider, Resampling, automatische Sprachwahl, Hotwords, mDNS sowie Wyoming-TLS/Authentifizierung. Home Assistant muss das Sprachende mit `audio-stop` melden. `INFERENCE_CHUNK_MS` ändert die Audiozuführung, nicht den Modellkontext oder die algorithmische Latenz von 1,12 Sekunden. Nur im vertrauenswürdigen LAN verwenden.

## Modelle bereitstellen

Das Image und das Git-Repository enthalten **keine Modellgewichte**. Ein zusammengehöriger L37-Runtime-Satz benötigt unter dem Host-Modellverzeichnis:

- `models/L37-runtime/encoder.int8.onnx`
- `models/L37-runtime/decoder.onnx`
- `models/L37-runtime/joiner.onnx`
- `models/L37-runtime/tokens.txt`

Diese Pfade sind Beispiele relativ zum Checkout. Den eigenen Hostpfad read-only nach `/models` mounten; Lizenz und Herkunft bei den Gewichten aufbewahren. Vorhandene Gewichte weiterverwenden. Beschaffung, SHA256-Werte und reproduzierbarer Export: docs/MODELS.md. Kein automatischer Download oder Export beim Serverstart. Der geprüfte Runtime-Satz umfasst 726.885.887 Byte ohne Lizenzdateien.

## Docker installieren

Voraussetzungen: Linux amd64, AVX2, Docker, vorbereitete Modelle und ungefähr 4 GiB RAM für den Container. Build und Export benötigen mehr Ressourcen.

Nach **erfolgreicher Veröffentlichung** ist der geplante Entwicklungsbezug:

```sh
docker pull ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:dev
```

Dieser Pull ist derzeit noch nicht als verfügbar bestätigt. Für reproduzierbare Installationen den veröffentlichten `sha-COMMIT`-Tag oder Digest verwenden. Lokal bauen und Modellvorprüfung ausführen:

```sh
docker build --platform linux/amd64 -t nemotron-unified-rust-wyoming:dev .
docker run --rm --network none --read-only \
  -v /ABSOLUTER/MODELLPFAD:/models:ro \
  nemotron-unified-rust-wyoming:dev check-model
```

Der Build führt Release-Kompilierung, Formatprüfung, Rust-/Protokolltests und Clippy mit `-D warnings` aus. `check-model` prüft Dateien/Metadaten; vollständiges Graphladen und Inferenz erfordern einen Serverstart.

Compose: ./.env.example nach ./.env kopieren, `MODEL_DIR` auf den vorhandenen absoluten **Hostpfad** setzen, freien `HOST_PORT` und `PUBLISH_ADDRESS` prüfen. `IMAGE=nemotron-unified-rust-wyoming:dev` für den lokalen Build oder nach Veröffentlichung den GHCR-Tag setzen.

```sh
cp .env.example .env
docker compose config
docker compose up -d --build
```

./docker-compose.yml enthält nur diesen Dienst. Bestehende Dienste werden durch die Anleitung nicht automatisch migriert. Für Registry-Nutzung nach erfolgreichem Pull `docker compose up -d --no-build` verwenden.

## Unraid und Home Assistant

Unraid-Anleitung: docs/UNRAID.md. Die Vorlage config/unraid-template.xml bietet Bridge-Netz, read-only Modelle, standardmäßig Hostport 10310 → Containerport 10300 sowie alle 19 wirksamen Variablen mit deutschen Beschreibungen.

In Home Assistant: **Einstellungen → Geräte & Dienste → Integration hinzufügen → Wyoming Protocol**; LAN-IP des Unraid-Hosts und den veröffentlichten Hostport eintragen. In einer deutschen Assist-Testpipeline den STT-Dienst `nemotron-unified-l37-int8` auswählen. Details und Abnahme: docs/HOME_ASSISTANT.md. Bestehende Pipelines bleiben manuell verwaltet.

## Alle 19 wirksamen Variablen

Vollständige Wertebereiche, Defaults und Wirkung: docs/PHASE5_2.md und docs/CONFIGURATION.md; maschinenlesbar in config/variables.json. **17** Variablen verarbeitet Rust, **2** der Container-Entrypoint.

| Variablen | Standard |
|---|---|
| `PUID`, `PGID` | `99`, `100` |
| `WYOMING_HOST`, `WYOMING_PORT` | `0.0.0.0`, `10300` |
| `LANGUAGE`, `STT_DEVICE` | `de`, `cpu` |
| `MODEL_DIR` | `/models` im Container |
| `ENCODER_PATH`, `DECODER_PATH`, `JOINER_PATH`, `TOKENS_PATH` | leer → Standarddateien unter `MODEL_DIR` |
| `THREADS` | `2` (zulässig: 1, 2, 4) |
| `MAX_AUDIO_SECONDS`, `MAX_AUDIO_CHUNK_BYTES` | `120`, `320000` |
| `MAX_CONNECTIONS`, `CLIENT_TIMEOUT_SECONDS` | `8`, `30` |
| `INFERENCE_CHUNK_MS` | `20` |
| `LOG_LEVEL`, `LOG_TRANSCRIPTS` | `info`, `false` |

PUID/PGID wechseln vor Modellzugriff auf die konfigurierte Identität. Der Bootstrap benötigt ausschließlich SETUID/SETGID; der Server läuft ohne effektive Capabilities mit NoNewPrivs. Kein automatisches chown/chmod an Modellen. Alternativ mit passenden `--user 99:100` und Variablen vollständig ohne Bootstrap-Capabilities starten. Fehlerhafte Werte werden mit Variablennamen abgewiesen. Optionale Modell-Einzelpfade dürfen leer sein.

`IMAGE`, `HOST_PORT` und `PUBLISH_ADDRESS` sind Compose-Hilfswerte. Compose verwendet `MODEL_DIR` als Host-Mountquelle und setzt im Container `/models`. `SHERPA_ONNX_LIB_DIR` und `LD_LIBRARY_PATH` sind technische Imagewerte, keine zusätzlichen Nutzer-Tuningoptionen.

## Icons

| Icon | Zweck | GitHub-Dateipfad | Größe | Abmessungen |
|---|---|---|---:|---|
| Low-Q | **Einziger Standard für Unraid CA und Docker** | assets/icons/nemotron-lowq.png | 82.756 Byte | 256 × 256 |
| HQ | Hochwertige Alternative, kein Unraid-Standard | assets/icons/nemotron-hq.png | 1.560.271 Byte | 1254 × 1254 |

Die XML-Vorlage und das Image-Label `net.unraid.docker.icon` verwenden ausschließlich Low-Q. Beide PNGs haben transparente Pixel und wurden unverändert kopiert. Low-Q erfüllt die Performancevorgaben ohne weitere Komprimierung. Die neuen Quelldateien icons/nemotron-stt-hq.png und icons/nemotron-stt-lowq.png bleiben lokal unverändert erhalten. Die neuen Grafiken zeigen kein erkennbares NVIDIA-Augenlogo oder NVIDIA-Wortlogo und keine ®-/™-Symbole. Die alten Bilder sind im aktuellen Dateistand ersetzt, bleiben aber vorerst in der lokalen Git-Historie enthalten. Geplante Raw-Links und Migration gespeicherter Unraid-Icon-URLs: docs/UNRAID.md. Derzeit sind die Raw-Dateien noch nicht öffentlich erreichbar.

## Entwicklung, Tests und Lizenzen

Bedienung: `serve` (Standard), `healthcheck`, `check-model`, `--help`, `--version`; Benchmarkdiagnose über `benchmark`. CLI-Overrides: `--model DIR`, `--threads 1|2|4`, `--bind HOST:PORT`. Auch überschriebene Umgebungswerte müssen gültig sein.

Tests und Belege: docs/TESTS.md, docs/PHASE5_1.md, docs/PHASE5_2.md und docs/PHASE6.md. CI-/GHCR-Ablauf: docs/RELEASE.md. Die kurze echte deutsche Referenzaufnahme prüft die technische Kette; allgemeine Befehlsqualität, Assist-/Satellite-Abnahme und Langzeitlast bleiben offen.

Eigener Code: ./LICENSE (MIT). sherpa-onnx: Apache-2.0; ONNX Runtime: MIT; NVIDIA-Modell: getrennt OpenMDW-1.1. Abhängigkeiten und Herkunft: ./THIRD_PARTY_NOTICES.md. Kein offizielles NVIDIA-Projekt und keine behauptete Unterstützung durch NVIDIA.
