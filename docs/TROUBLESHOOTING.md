# Fehlerbehebung

| Beobachtung | Prüfung und Maßnahme |
|---|---|
| `missing model file` / `empty model file` / `cannot read` | Host-Bind-Mount, vier feste Namen, Leserechte für UID 65534 und vollständigen Export prüfen. Kein automatischer Download. |
| `model metadata mismatch` / deutscher Prompt fehlt | Ausschließlich Nemotron **Unified** L37 mit links37/chunk7/rechts7 verwenden, nicht Nemotron 3.5 oder einen anderen Kontext. docs/MODELS.md beachten. |
| Native SHA-/Commitfehler | Image aus ./Dockerfile neu bauen; keine Release-sherpa-Bibliotheken oder fremden `LD_LIBRARY_PATH` verwenden. SOURCE_COMMIT und tatsächlicher C-API-SHA werden verglichen. |
| `sherpa recognizer creation failed` | Native ORT-Fehlermeldung unmittelbar davor lesen; Decoder/Joiner/Encoder müssen aus demselben Export stammen, gültiges ONNX und vollständig lesbar sein. |
| `requires rate=16000, width=2, channels=1` | Eingabe außerhalb des Servers konvertieren; keine WAV-Datei als Chunkpayload senden. |
| Ungerade/leere PCM-Daten oder leere Aufnahme | Vollständige i16-Samples und mindestens einen nichtleeren Chunk senden; nach Fehler neuen `transcribe`-Zyklus beginnen. |
| `configured audio duration limit exceeded` | Sprachende durch VAD korrekt senden, MAX_AUDIO_SECONDS prüfen. Sitzung wird verworfen. |
| `invalid-frame` | JSONL, Byte-Längen, Header-/Payloadgrenze und Clienttimeout prüfen. Nach Framingfehler neu verbinden. Langsam nachgelieferte Teilheader halten keinen Slot unbegrenzt offen. |
| `busy` | MAX_CONNECTIONS erreicht. Leerlaufclient schließen oder nach Timeout erneut verbinden. Inferenz wird absichtlich serialisiert. |
| Healthcheck fehlschlägt | Modellstartlogs, Umgebungsport, Listener und Verbindungslimit prüfen. Bei CLI-`--bind` auch Healthcheck-Umgebung anpassen. Nicht als Ersatz für einen echten Sprachtest verstehen. |
| Modell startet, Text ist falsch/leer | Echte Aufnahme und Referenz behalten; Mikrofonpegel, VAD-Ende und Sprache prüfen. Keine Fixturetexte verwenden; Fehltranskript dokumentieren. |
| Langsamer N100 / OOM | THREADS zunächst2; keine konkurrierenden Inferenzlasten. Dockerstats beobachten. Acht Streams brauchen mehr RAM als ein Stream; 4-GiB-Limit wurde nicht für jeden maximalen Lastfall garantiert. |
| SIGTERM braucht länger | Aktueller nativer Aufruf wird zu Ende geführt. Stopfrist 60 s; bei wiederholter Überschreitung Logs behalten und nicht produktiv freigeben. |
| Unraid versucht ein Image zu pullen | Regulär `ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest` verwenden und anonymen Pull prüfen. Für feste Stände einen geprüften sha-COMMIT-Tag oder Digest wählen. |

Serverlogs enthalten Startbereitschaft, Konfigurationsgrenzen, Verbindungsfehler und Shutdown, standardmäßig keine erkannten Texte oder Audioaufnahmen. Diagnostische Tests schreiben echte Transkripte ausdrücklich in ihre Ergebnisdatei. Nach einer fehlgeschlagenen Anfrage ist nur ein neuer vollständiger Ereigniszyklus zulässig; alte Audio-Chunks gehören nicht zu einer neuen Sitzung.
