# Changelog

## 1.0.0 – zur Freigabe vorbereitet, noch nicht veröffentlicht

Phase5.2 ergänzt tatsächlich angewendete PUID/PGID (99:100), minimalen Identitäts-Bootstrap, unprivilegierten Server-/Healthcheck-Betrieb, Modellzugriffsdiagnose und isolierte Identitätstests. Bestehende laufende Container werden nicht automatisch aktualisiert.

Phase5.1 ergänzt 17 validierte Docker-Variablen, optionale Modell-Einzelpfade, native Zuführungsgröße, Payloadlimit, Logging/Transkript-Opt-in, vollständige deutsche Unraid-Felder und Konfigurationstests. Bestehende Variablennamen bleiben kompatibel.

- Vollständiger begrenzter deutscher Wyoming-STT-Server mit wiederholten Anfragen, getrennten Sitzungen und parallelen Verbindungen.
- Echte Nemotron-Unified-L37-INT8-Inferenz über sichere sherpa-Rust-Anbindung; feste PR- und Laufzeitidentität.
- Modellstart vor Bereitschaft, Umgebungsvariablen, absolute Framefristen, Audiolimits und SIGTERM/SIGINT-Shutdown.
- Multi-Stage-CPU-Image, Nonroot, Protokoll-Healthcheck, Compose und lokale Unraid-XML-Vorlage.
- Automatisierte TCP-/Codec-/Lifecycle-Tests und opt-in echter Sprachtest mit offizieller Wyoming-Python-Referenz.
- Installations-, Modell-, Lizenz- und Release-Dokumentation; CI und ausschließlich manuell auslösbares GHCR-Publishing vorbereitet.

## 0.2.0 – lokale Entwicklungsphase

- Tatsächlichen PR #4141 gebaut und sichere Rust-Anbindung integriert.
- L37 auf CPU exportiert, Encoder teilweise INT8-quantisiert und mit echter deutscher Aufnahme geprüft.
- Ergebnisse und Grenzen in docs/PHASE4_RESULTS.md dokumentiert.
