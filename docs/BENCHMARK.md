# Benchmark-Konzept – noch nicht ausgeführt

Alle Pfade hier beziehen sich auf das neue Projektverzeichnis.

## Reproduzierbarer Korpus

Ein gemeinsames unveränderliches Manifest für Nemotron, Moonshine Small DE und
Kroko: ./benchmarks/manifest.example.jsonl als Schema-Beispiel, keine Testdaten.
Pro echter Datei ID, WAV-Pfad, SHA256, Dauer, Sprechergruppe und deutsche
Referenz speichern. Referenzen vor dem Lauf fixieren. Identische 16-kHz-Mono-
PCM16-Dateien und exakt gleiche Äußerungsgrenzen für alle Modelle verwenden.
Keine getrennte Audioaufbereitung je Modell; erforderliches modellinternes
Feature-Preprocessing gehört jeweils zur gemessenen Pipeline.

Mindestens 200 manuell geprüfte deutsche HA-Befehle, mehrere Sprecher, Räume,
Mikrofone und SNR-Bedingungen: Licht, Helligkeit, Temperatur, Rollläden, Timer,
Zahlen, zusammengesetzte Raumnamen, Eigennamen und Umlaute. Zusätzlich Stille,
Geräusche, sehr kurze Befehle und längere freie Sprache. Aufnahme-Einwilligung
und Dateirechte dokumentieren. Kalibrierungs- und Testsprecher getrennt halten.
Keine Audiodownloads oder Aufnahmen Bestandteil dieser Phase.

## Matrix

| Dimension | Werte |
|---|---|
| Nemotron-Modus | Offline; links/Chunk/rechts = 5,6/0,56/0,56 s und 5,6/0,16/0,40 s |
| CPU-Threads | 1, 2, 4 |
| Gewichte | FP32; partielle INT8 nur nach numerischer und qualitativer Prüfung |
| Sprache | explizit de |
| Parallelität | zunächst eine Sitzung; Mehrbenutzerlast später separat |
| Baselines | Moonshine Small DE und Kroko mit fixierten Versionen/Hashes |

Nemotron ergibt maximal 18 Grundkonfigurationen. Nicht unterstützte
Kombinationen als N/A mit Grund erfassen. Baselines nach ihren tatsächlichen
Fähigkeiten offline bzw. nativ streaming prüfen; eine Offline-Baseline nicht
als echtes Streaming ausweisen. Kontextverkürzung L37 als zusätzliche benannte
Variante führen, niemals unbemerkt mit L70 mischen. Algorithmische Latenz ist
Chunk plus Rechtskontext, nicht Audio-Netzwerkpaketgröße und nicht Endlatenz.

## Ablauf und Messgrößen

1. Host-/OS-/Runtime-/Exportrevision, Modellhashes, Graphformen, CPU-Governor,
   Affinität, Thermik und freie Ressourcen protokollieren. Bestehende Container
   unverändert lassen; deren Hintergrundlast erfassen. Keine globale CPU-
   Umkonfiguration ohne gesonderten Auftrag.
2. Sequentielle Läufe, pro Variante ein Warm-up und mindestens drei Messläufe;
   Variantenreihenfolge rotieren. Modell-Ladezeit separat erfassen. Native
   intra-op Threads auf 1/2/4 setzen, inter-op und weitere Threadpools so begrenzen,
   dass nicht unbemerkt überbucht wird. Sessionkonfiguration dokumentieren.
3. Offline mit bereits geladenem Modell und Streaming sowohl ohne Echtzeit-
   Pacing für Compute-RTF als auch mit Echtzeit-Pacing für Endlatenz messen.
   Gleiche PCM-Pakete, monotone Zeitstempel, gleiche Audio-stop-Zeitpunkte.
   Audio-Ende im Korpus ist primäre Grenze; adaptive Endpointing-Varianten
   getrennt berichten, da sonst Modelle unterschiedliche Sprache sehen.
4. WER = (Substitutionen + Löschungen + Einfügungen) / Referenzwortzahl;
   Korpuswerte aus aufsummierten Zählern, nicht Mittelwert einzelner WERs.
   Referenz und Hypothese gleich normalisieren: Unicode NFC, Kleinschreibung,
   festgelegte Interpunktionsbehandlung. Zahlen-/Kompositaregeln versionieren;
   Rohtranskripte zusätzlich behalten. ß und Umlaute erhalten. Stille mit
   null Referenzwörtern getrennt als False-positive-Rate ausweisen.
5. RTF = aktive Verarbeitungszeit / Audiodauer; Pipeline einschließlich DSP,
   Decoding und Detokenisierung, Modellladen separat. Echtzeit-gepacte Wartezeit
   nicht als Compute-RTF zählen; zusätzlich gesamte Walltime und CPU-Zeit erfassen.
6. First-token-Latenz ab Audio-start, Endlatenz ab audio-stop bis transcript,
   p50/p95/p99 und Maximum berichten. Falls keine Partial-Tokens zugänglich sind,
   First-token als nicht messbar ausweisen. Backlog und Peak pro Chunk erfassen.
7. Peak-RSS des gesamten Prozesses (z.B. eigener Prozess mit /usr/bin/time -v,
   sofern verfügbar), Idle-/Loaded-RSS, Prozess-CPU und thermische Entwicklung
   erfassen. Bei Python-Referenz Kindprozesse berücksichtigen. Keine synthetischen
   RAM-Werte aus Dateigrößen ableiten.

Zusätzlich Exact-Match und Intent-/Slot-Erfolg mit eingefrorenen Sollwerten
optional offline bewerten; keine Befehle in Home Assistant ausführen. Gepaarte
WER-Differenzen mit Konfidenzintervallen, Qualitätsdelta INT8–FP32 und Verhalten
bei Stille berichten. Ergebnisse enthalten Modell-/Audiohashes, Backend,
Präzision, Kontext, Threads, Messverfahren und Fehlermeldungen. Fehlgeschlagene
Läufe behalten. Es liegen noch keine Ergebnisse oder Leistungszusagen vor.
