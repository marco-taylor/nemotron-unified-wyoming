# Veröffentlichung und spätere v1.0.0-Freigabe

**Aktuelle Phase-11-Sperre:** Alle neuen Namen/Adressen sind lokal vorbereitet. Keine frühere Freigabe gilt als Erlaubnis für diese Veröffentlichung. scripts/check_model_source.py blockiert den neuen Publikationsworkflow, solange die exakten eigenen L37-Exporte keine genehmigten HTTPS-Quellen haben. Erst Modellbereitstellung mit Lizenz-/Herkunftshinweisen freigeben, leere Erstinstallation testen, dann GitHub-Umbenennung, Push, GHCR und CA einzeln nach Freigabe durchführen. Historische Statusangaben unten betreffen den bisherigen Projektnamen.

Quellrepository: https://github.com/marco-taylor/nemotron-unified-wyoming
GHCR: ghcr.io/marco-taylor/nemotron-unified-wyoming

Phase6 erlaubt öffentliches Repository und Upload nach main. Es wird **kein offizieller v1.0.0-Release und kein v1.0.0-Git-Tag** angelegt. Die Version im Quellcode bleibt ein zur Abnahme vorbereiteter Stand.

./.github/workflows/ci.yml baut und prüft Pull Requests und Pushes. ./.github/workflows/publish-ghcr.yml baut linux/amd64 auf Push nach main; der Docker-Build führt Formatierung, alle Tests und Clippy aus. Vor Veröffentlichung werden Architektur, CLI und das exportierte Runtime-Dateisystem auf Modellgewichte geprüft. Erst danach pushen GITHUB_TOKEN und packages:write latest, den kompatiblen dev-Tag und sha-COMMIT desselben Builds. Keine Zugangsdaten im Repository, kein v1.0.0-Tag und keine Release-Erstellung. Manuelle Auslösung verlangt publish=true und Branch main.

Die Registry-Sichtbarkeit muss nach dem ersten Push anonym geprüft werden; ein erfolgreiches Actions-Push allein beweist noch keinen öffentlichen Pull. Workflow-/Publikationsstatus: docs/PHASE6.md.

Vor einem offiziellen Release bleiben der gemeinsame Home-Assistant-/Satellite-/Unraid-Abnahmetest, längerer Betrieb und deutsche Befehlsqualität offen. Lizenz-/Quellhinweise prüfen, öffentliche Imageverfügbarkeit bestätigen und danach gesondert offiziellen Release und Versionstags freigeben. Keine automatische Bereitstellung und kein Ersatz bestehender Container.

Die öffentliche main-Historie wurde nach ausdrücklicher Freigabe neu aus dem geprüften Projektstand erstellt. Alte NVIDIA-Logo-Bilder sind weder im aktuellen Stand noch in dieser öffentlichen Abstammung enthalten. Die vollständige ursprüngliche Historie wurde außerhalb des Projekts als Git-Bundle gesichert und wiederhergestellt geprüft. Ein zusätzlicher lokaler Archivbranch wird niemals mitgepusht. Referenzen und Prüfbelege: docs/PHASE6.md.

Regulärer Installationsbezug: `ghcr.io/marco-taylor/nemotron-unified-wyoming:latest`. latest wird erst nach erfolgreichem Build inklusive Rust-Prüfungen und Runtime-Audit gepusht, nach dev und dem Commit-Tag. Der Workflow läuft ausschließlich für main; Pull Requests veröffentlichen nichts. dev und latest werden aus demselben lokal geprüften Image getaggt. Tatsächliche Registry-Digests und Integrationsergebnis: docs/LATEST.md.
