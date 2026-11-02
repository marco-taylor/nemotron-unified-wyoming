# Konfiguration und Wyoming

Die vollständige aktuelle Variablentabelle mit Standardwerten, Validierung, Wirkung, Docker-/Unraid-Hinweisen und Backend-Grenzen steht in docs/PHASE5_2.md. Die 17 Dienstvariablen plus die zwei Entrypoint-Variablen PUID/PGID sind in ./.env.example und config/unraid-template.xml aufgeführt; Referenzliste für automatische Paritätsprüfungen: config/variables.json.

N100-Defaults: Sprache de, CPU, 2 ORT-Threads, 0.0.0.0:10300, maximal120s Audio, 8 Verbindungen, 320000 Byte pro Payload, native Zuführung in höchstens20-ms-Stücken. PUID/PGID=99:100 werden vor Modellzugriff angewendet; der laufende Server ist unprivilegiert. L37-Modellkontext bleibt fest. Keine native VAD-/Endpointing-Konfiguration, kein Wyoming-Transcript-Streaming.

Protokoll: offizielles Wyoming JSONL mit optionalen externen JSON-Daten und exakter binärer Payloadlänge. `describe` → `info`; `transcribe` → `audio-start` → mindestens ein `audio-chunk` → `audio-stop` → `transcript`. Derselbe Socket erlaubt neue Anfragen nach Abschluss. Format auf Start/Chunk: rate16000, width2, channels1; Little-Endian-PCM, kein WAV-Header. Andere Sprache, falsche Reihenfolge, ungültiges/zu langes Audio oder Backendfehler liefern `error` und verwerfen die Sitzung. Nach Framingfehler Verbindung neu aufbauen. Codes stt-error, invalid-frame, timeout, busy sind projektspezifisch.

Headerlimit16KiB und JSON-Datenlimit64KiB sind feste Schutzgrenzen; binäre Payload ist zusätzlich durch MAX_AUDIO_CHUNK_BYTES begrenzt. Keine unbeschränkte Audiosammlung in Rust. Native Streamdaten sind durch Audiodauer und Verbindungsanzahl begrenzt; Docker-cgroup-Limit separat konfigurieren.

Healthcheck nutzt dieselben Umgebungswerte für Adresse/Port, lädt keine zweite Modellkopie und prüft echtes describe/info. Er belegt geladene Modellbereitschaft und den Protokollweg, keine neue ASR pro Probe. SIGTERM/SIGINT warten auf einen laufenden nativen Aufruf. Hintergrund und bisherige technische Tests: docs/PHASE5.md.
