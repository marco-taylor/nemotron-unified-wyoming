# Veröffentlichung und spätere v1.0.0-Freigabe

Quellrepository: https://github.com/marco-taylor/nemotron-unified-rust-wyoming
GHCR: ghcr.io/marco-taylor/nemotron-unified-rust-wyoming

Phase6 erlaubt öffentliches Repository und Upload nach main. Es wird **kein offizieller v1.0.0-Release und kein v1.0.0-Git-Tag** angelegt. Die Version im Quellcode bleibt ein zur Abnahme vorbereiteter Stand.

./.github/workflows/ci.yml baut und prüft Pull Requests und Pushes. ./.github/workflows/publish-ghcr.yml baut linux/amd64 auf Push nach main; der Docker-Build führt Formatierung, alle Tests und Clippy aus. Vor Veröffentlichung werden Architektur, CLI und das exportierte Runtime-Dateisystem auf Modellgewichte geprüft. Erst danach pushen GITHUB_TOKEN und packages:write die Entwicklungstags dev und sha-COMMIT. Keine Zugangsdaten im Repository, kein automatisches latest-/v1.0.0-Tag und keine Release-Erstellung. Manuelle Auslösung verlangt publish=true und Branch main.

Die Registry-Sichtbarkeit muss nach dem ersten Push anonym geprüft werden; ein erfolgreiches Actions-Push allein beweist noch keinen öffentlichen Pull. Workflow-/Publikationsstatus: docs/PHASE6.md.

Vor einem offiziellen Release bleiben der gemeinsame Home-Assistant-/Satellite-/Unraid-Abnahmetest, längerer Betrieb und deutsche Befehlsqualität offen. Lizenz-/Quellhinweise prüfen, öffentliche Imageverfügbarkeit bestätigen und danach gesondert offiziellen Release und Versionstags freigeben. Keine automatische Bereitstellung und kein Ersatz bestehender Container.

Die neuen Nemotron-STT-Icons ersetzen die früheren Logo-Grafiken im aktuellen Dateistand. Vor dem ersten Push muss die Historienentscheidung geklärt sein: frühere Commits enthalten noch die alten NVIDIA-Logos. Ungeprüftes Mitveröffentlichen oder eigenmächtiges Umschreiben der zu erhaltenden Historie findet nicht statt. Aktueller Status: docs/PHASE6.md.
