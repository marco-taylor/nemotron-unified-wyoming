# latest – regulärer Installationskanal

Build-Quellcommit: `555e3e180abdfbbaea3fb5dad5223dec01e72d56`.

Reguläre Installation: `ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest`. Der kompatible Tag `dev` bleibt erhalten. Beide wurden mit leerer Docker-Client-Konfiguration erfolgreich anonym gepullt und zeigen auf denselben linux/amd64-Build:

`sha256:63218a57850d6b5521a13ccdf93b5c19c958657f7b3c530d0ff583dcac7166bf`

Image-ID: sha256:6d694a1e5e46ad991cdbf49cb718be29e8ec1cd19fdff8e1db3813fe11505dc7. Entpackte Imagegröße: 116.748.638 Byte. Das Revisionlabel stimmt mit dem Quellcommit überein.

## Workflow und Installation

./.github/workflows/publish-ghcr.yml veröffentlicht ausschließlich vom main-Branch: Build mit Formatprüfung, Tests und strengem Clippy, Architektur-/Runtime-Audit, danach Commit-Tag, dev und zuletzt latest. Alle Tags stammen aus demselben geprüften Image. Pull Requests veröffentlichen nichts; manueller Start verlangt publish=true auf main. Kein offizieller v1.0.0-Release.

Unraid-Vorlage config/unraid-template.xml, ./docker-compose.yml, ./.env.example, config/unraid.env.example, aktuelle Installationsanleitungen und Diagnosebefehle verwenden für reguläre Installationen den vollständigen GHCR-latest-Pfad. Sämtliche 19 wirksamen Variablen bleiben erhalten und werden auf Parität geprüft. Historische Phasenberichte behalten ihre damaligen Tags als Nachweis.

Öffentliche Unraid-Vorlage: https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/config/unraid-template.xml . Erfolgreich heruntergeladen und bytegenau mit der lokalen Vorlage verglichen. Ausschließlich Low-Q als Icon in Template und Image-Label: https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/assets/icons/nemotron-lowq.png . HQ ist kein Standard.

## Tests und Sicherheit

- GHCR-Lauf erfolgreich: https://github.com/marco-taylor/nemotron-unified-rust-wyoming/actions/runs/41472190698 . Docker-Build verwendet für unveränderte Runtime-/Rust-Quellen geprüfte Cache-Schichten; Runtime-Audit und Upload wurden tatsächlich ausgeführt.
- Separater CI-Lauf erfolgreich: https://github.com/marco-taylor/nemotron-unified-rust-wyoming/actions/runs/41472190889 . Vollständiger Neubau einschließlich Release-Build, cargo fmt --check, 33 bestandenen Rust-Tests, Clippy mit -D warnings und Runtime-Prüfung erfolgreich.
- Lokal erneut geprüft: Compose-Schema, XML, Workflow-Tagregeln, Shellsyntax, Low-Q-Standard und alle 19 Variablen.
- Git-Index und zu veröffentlichende HEAD-Historie vor Push ohne Secrets, Modellgewichte oder Buildartefakte. Der rein lokale Archivbranch wurde nicht gepusht.
- Vor Veröffentlichung vorhandenes Runtime-Image erneut auditiert; der Workflow prüft das neue Image vor latest-Push. Anschließend tatsächlich heruntergeladenes latest erneut exportiert und geprüft: 3.548 Dateien, keine Modellgewichte und keine unbekannten Credentialmuster. Bekannte öffentliche GnuTLS-Selbsttestschlüssel ausschließlich für die exakt geprüfte Debian-Bibliothek ausgenommen; keine privaten Nutzer-/Deployment-Schlüssel.
- Runtime-Preflight auf latest bestanden: CLI, fehlende Modelle, ungültige Konfiguration, beschädigter Decoder, native Bibliotheken und Lizenztexte.
- Identitäts-/L37-Tests auf latest bestanden: PUID/PGID=99:100, Override 12345:23456, keine effektiven Capabilities, NoNewPrivs=1, verständliche Fehler bei ungültigen IDs oder unlesbaren Modellen, geordneter Shutdown. Bestehende L37-Gewichte ausschließlich read-only verwendet; kein Download oder Rechtewechsel.
- Direkter Wyoming-Healthcheck und unveränderter automatischer Docker-HEALTHCHECK bestanden; ein eigener Wegwerfcontainer wurde tatsächlich healthy.
- Standard- und Nichtstandard-Konfiguration liefern insgesamt sechs echte deutsche Transkriptionen „Einsteigen bitte.“. Wyoming-Fehler-/Limitfälle und Shutdown ebenfalls bestanden. Kein neuer allgemeiner Qualitäts-/Performancebenchmark behauptet.
- Beide Registry-Digests identisch: dev und latest verweisen auf denselben Build. Der frühere sha-6e2cd9e4112e5211f0c934483e65fca21c12ae13-Tag ist weiterhin anonym pullbar und behält seinen bisherigen Digest sha256:7f758ff370c45ce07b55c9d761be13b1b422643748d423cd1535d1398a1caa6d. Keine GHCR-Tags gelöscht.

Alle 31 Bestandscontainer nach ID, Konfiguration, Startzeit und Restart-Zähler unverändert; nemotron-unified-stt weiterhin healthy. Sämtliche eigenen Prüfcontainer kontrolliert entfernt. Keine produktiven Container aktualisiert oder neu gestartet, keine Modelle/Volumes gelöscht, kein Force-Push. Kernelwarnung zur fehlenden Swap-Limit-Unterstützung wie zuvor; RAM-Limit wirksam.

Rohbelege lokal unter docs/evidence/latest/. Die vollständige ursprüngliche Git-Sicherung und die frühere Veröffentlichung sind in docs/PHASE6.md dokumentiert. Ein anschließender reiner Berichtscommit verwendet [skip ci]; das getestete Image bleibt dem oben genannten Build-Quellcommit zugeordnet.

Abschluss: beide Actions erfolgreich, alle genannten Integrations-/Sicherheitsprüfungen bestanden; keine verbleibenden Blocker für latest.
