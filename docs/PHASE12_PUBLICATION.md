# Phase 12 – Veröffentlichung Nemotron Unified Wyoming

Status: Teilveröffentlichung erfolgt; Fortsetzung wartet auf die Public-Sichtbarkeit
des neuen GHCR-Packages. Noch keine vollständige Veröffentlichungsbestätigung.
Freigabe des Nutzers gilt für Repository-Umbenennung, den Modell-Release,
neues GHCR-Image und CA-Aktualisierung nach erfolgreichen Prüfungen.

## Sicherung und Bestandsaufnahme

Ausgangscommit: `91984c9450e05e8b8593547daa8979438c36e3f7` auf
`feature/rename-model-download`, mit den noch uncommitteten Phase-11.1-Dateien.
Unverändertes bisheriges main: `d7af454c269da902b220ea50d23d256220edb376`.
Phase 9 bleibt im eigenen Branch/Stash; keine experimentelle Socket-Optimierung
wurde übernommen. Phase 10, 11 und 11.1 bilden den Veröffentlichungsstand.

Wiederherstellbare Sicherung vor Änderungen:
`/mnt/nvme/appdata/codex-workspace/nemotron-phase12-backups/phase12.HvuUMQ`.
Darin vollständiges Git-Bundle mit allen Refs/Stashes, Arbeitsbaum-Patch,
ungetrackte Phase-11.1-Dateien als Archiv und der Git-Index. Bundle-Verifikation,
tatsächlicher Mirror-Restore mit fsck sowie Archivvergleich erfolgreich.
Sicherung privat; keine Zugangsdaten in Projektdateien oder Bericht übernommen.

31 vorbestehende Container sowie das bisherige Image und die gespeicherte
Unraid-Vorlage sind als ausschließlich gelesene Baseline dokumentiert.
Rohbelege bleiben ignoriert unter docs/evidence/phase12.

## GitHub

Umbenennung erfolgreich:
https://github.com/marco-taylor/nemotron-unified-wyoming

Repository-ID `1442993885` unverändert, öffentlich. Die alte URL
https://github.com/marco-taylor/nemotron-unified-rust-wyoming leitet mit
abschließendem HTTP 200 auf das neue Repository weiter. origin zeigt auf
die neue SSH-Adresse. Keine andere Repository-Umbenennung, keine neue Historie,
kein Force-Push.

Veröffentlichungsvorbereitung im separaten Branch `release/phase12`:
Commit `8122e518c4d1717e5e86c0048e1300fececcb0cc`, einschließlich
Lizenz-/Herkunftsdokumentation und der geprüften Modell-Release-Planung.
main bleibt bis zum vollständigen lokalen Funktionstest zurückgestellt.

Der vollständige Funktionstest ist inzwischen bestanden. Funktionscommit
`01733f79a25c4cf0571d6b047f5fee4c7d4cb8e3` ist auf `release/phase12` gepusht;
main und damit der bestehende CA-Template-Bezug bleiben bis zur öffentlichen
Image-Erreichbarkeit bewusst unverändert. Ein zusätzliches vollständiges Bundle
`/mnt/nvme/appdata/codex-workspace/nemotron-phase12-backups/phase12.HvuUMQ/functional-progress.bundle`
wurde verifiziert und tatsächlich in einen separaten Mirror zurückgespielt.

## Modell-Release

Separater Tag: `models-l37-v1.0.0`, kein offizieller Server-v1.0.0-Release.
https://github.com/marco-taylor/nemotron-unified-wyoming/releases/tag/models-l37-v1.0.0

Der Release ist öffentlich und immutable. Er wurde zunächst als Entwurf angelegt,
erst nach Größen-/SHA256-Abgleich aller 14 hochgeladenen Assets veröffentlicht
und danach vollständig ohne Authentifizierung heruntergeladen und erneut geprüft.
Vier Modelle enthalten 726.885.887 Byte; die 14 Assets enthalten zusätzlich die
vollständige OpenMDW-1.1-Lizenz, NVIDIA-Modellkarte, Herkunfts-/Exporthinweise und
SHA256SUMS. Es wurden ausschließlich die vorhandenen geprüften Gewichte verwendet.

Feste Downloads:

- https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/encoder.int8.onnx
- https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/decoder.onnx
- https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/joiner.onnx
- https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/tokens.txt
- https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/SHA256SUMS
- https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/LICENSE.OpenMDW-1.1.md

| Quelle | Byte | SHA256 |
|---|---:|---|
| models/L37-runtime/encoder.int8.onnx | 675328677 | `8e1b140b85900dcaede7e5fc05c1adfd48d4a0585e3b55ec2a10cded7042c96d` |
| models/L37-runtime/decoder.onnx | 36745480 | `e5281215d86116e425191324830090922ec7732a34b1f5203d3b5a3564a20d97` |
| models/L37-runtime/joiner.onnx | 14768802 | `7abd80133827b59dbd3b57c47242d6001607ed14acda5db36ae28d64a3de8af8` |
| models/L37-runtime/tokens.txt | 42928 | `94139a0b2134fd40664ca72260026fa8a073336bb2f062239c8ecde2c8031763` |

NVIDIA trainierte das Originalmodell. Dieses Projekt exportierte die vorhandenen
Gewichte und quantisierte Teile des Encoders; kein eigenes Training/Fine-Tuning.
Vollständige Herkunft und Lizenzprüfung: docs/PHASE11_1_GITHUB_MODEL_RELEASE.md.
Die drei ONNX-Graphen wurden erneut mit ONNX-Checker validiert; keine externen
Tensor-Dateien erforderlich. Keine Gewichte in Git oder im Docker-Image.

## Downloader und Sicherheitsmaßnahmen

Die vier aktiven URLs sind fest auf models-l37-v1.0.0 gesetzt. Die bestehende
Größen-/SHA256-Prüfung, HTTPS-Regeln, flock, atomare Übernahme und Sicherung
beschädigter Originale bleiben erhalten. Ein remote geladenes Manifest ist kein
Vertrauensanker. Gültige Dateien werden unverändert wiederverwendet, auch offline.

Verwaiste eigene `.part-*` werden bei erneutem Start unter Initialisierungssperre
bereinigt, auch bei bereits vollständigem RW-Cache. Exaktes Tempnamenformat,
Eigentümer, regulärer Dateityp, Einfachlink und nicht aktive Dateisperre werden
geprüft. Finale Modelle, `.corrupt-*`-Sicherungen, fremde Dateien, Symlinks,
Hardlinks und aktive Downloads werden nicht gelöscht. Ein RO-Cache bleibt nutzbar;
bei fehlenden Berechtigungen werden Reste mit Hinweis erhalten. Modelle oder
Ordner werden nicht pauschal umbenannt, gelöscht oder gechownt.

Vor Modellzugriff Wechsel auf PUID/PGID; danach STT-PID1 mit 99:100,
CapEff/CapPrm/CapAmb=0, NoNewPrivs=1 und zwei seccomp-Filtern (Docker plus
Dateisystem-Schreibsperre). Lesender Modellzugriff, keine privilegierte Inferenz.
Vollständige Modellhinweise sind im Image unter
`/usr/share/licenses/nemotron-wyoming/model` enthalten.

## Erfolgreiche lokale Tests vor main/GHCR

| Prüfung | Ergebnis |
|---|---|
| Rust fmt / Release / Tests / Clippy | Bestanden, 33 Tests, `--locked --features sherpa`, alle Targets mit `-D warnings` |
| Downloader | 20 Tests als 99:100 bestanden, einschließlich SIGKILL, Konkurrenz, TLS, Netzwerk-/Platzfehler und sicherer Orphan-Bereinigung |
| Echte leere Erstinstallation | Neue isolierte RW-Bindablage; alle vier Dateien anonym von GitHub geladen, SHA256 korrekt, Dateien 99:100, Wyoming healthy |
| Deutsche Transkription | Je drei echte Anfragen nach Erstinstallation, Neustart und Reparaturen: `Einsteigen bitte.` |
| Neustart | Kein neuer Download; vier Modell-Inodes, mtimes und Hashes identisch |
| Fehlende Datei | Test-Token-Datei gesichert und gezielt nachgeladen; andere Dateien unverändert |
| Beschädigte Datei | Eigene Joiner-Testkopie bei identischer Größe manipuliert, Hashfehler erkannt und gezielt repariert; Original und beschädigte Sicherung erhalten |
| Orphan-Integration | Kontrolliertes eigenes Teilstück beim Start entfernt, keine neuen Downloads, finale Modellmetadaten unverändert |
| Legacy / Identität / Offline | Alle 19 Variablen in abweichender Konfiguration, 99:100 und 12345:23456, echter Betrieb ohne Internet, ungültige IDs/Konfigurationen, Protokollfehler und Shutdown bestanden |
| XML / Unraid / Compose / Workflows | xmllint, installierter Unraid-Parser, offizielles Compose-Schema und Workflow-Schutzprüfungen bestanden; 3 sichtbar / 7 erweitert / 11 ausgelassen |
| Image-Inhalt | 4870 Dateien: keine Modellgewichte oder Zugangsdaten; exakter öffentlicher GnuTLS-Selbsttestschlüssel-Ausnahmefall separat ausgewiesen |
| Git-Sicherheit | Arbeitsbaum und veröffentlichungsfähige HEAD-Abstammung ohne Secret-/Gewichtbefund, keine Archivrefs gepusht |

Die Originalgewichte im bisherigen Projekt-Modellverzeichnis wurden nicht für
Fehlersimulationen verändert. Tests verwenden neue Cache-Dateien; Testcache und
Sicherungen bleiben zur Nachprüfung lokal erhalten. Eine kurze unabhängige
Sprachaufnahme prüft die technische Kette, keine repräsentative deutsche WER-Abnahme.

## GHCR-Kandidat und laufende Veröffentlichung

Das vollständig lokal geprüfte Image ist als Kandidat hochgeladen:
`ghcr.io/marco-taylor/nemotron-unified-wyoming:validated-phase12-660fd95d171f`.
Digest `sha256:661f2c7c779e7c13b7fcf40d9a0a2252e8e64b93e1615d7254de5446b038a679`,
linux/amd64; lokale Image-ID
`sha256:660fd95d171f1c992858650aeb8828f7acff01488943f147c91da3bfd2f96c87`.

GitHub legte das neue Package zunächst privat an. Die API bietet hier keine
funktionierende Sichtbarkeitsänderung (gezielter Änderungsversuch HTTP 404);
der Benutzer wurde um die notwendige einmalige UI-Umstellung auf Public gebeten.
Bis zur Bestätigung durch anonymen Pull werden main und der CA-Umstieg
zurückgehalten. Dieser Kandidat ist noch keine bestätigte öffentliche latest-
Veröffentlichung. Nach öffentlicher Erreichbarkeit soll der geprüfte main-Workflow
erneut bauen, echte leere Modellinitialisierung bis healthy prüfen und dann
sha-COMMIT, dev und latest aus demselben Build veröffentlichen.

## Community Applications

Der aktuelle offizielle Feed `https://ca.unraid.net/assets/feed/applicationFeed.json`
enthält bereits genau eine Nemotron-App unter dem alten Namen sowie das bestehende
Repositoryprofil. Daher keine neue Einreichung/zweite Registrierung. Aktuell zeigt
dieser Eintrag noch auf das alte Image und den alten Template-Link. Die Umbenennung
des GitHub-Repositories leitet diese URL bereits sicher weiter.

Nach öffentlich geprüftem neuen Image wird config/unraid-template.xml am bisherigen
Pfad veröffentlicht, mit neuem Image, Projektnamen, Low-Q-Icon und TemplateURL.
Die bestehende Repositoryregistrierung bleibt erhalten. Feed-Übernahme bzw.
eventuell notwendige Maintainer-/Portaländerung ist danach zu prüfen; eine
aktualisierte CA-Aufnahme wird ohne Feed-Bestätigung nicht behauptet.

## Noch zu bestätigen

Public-Sichtbarkeit des neuen Packages und anonymer Pull; main-/Actions-Veröffentlichung
mit latest/dev-Digests; erneute Tests am Registry-Image; öffentliche Raw-Dateien;
CA-Feed-Übernahme. Der Zwischenvergleich aller 31 vorbestehenden Container ergab
keine Änderungen an ID, Config, HostConfig, Mounts, Status, Start-/Endzeit oder
RestartCount. Die gespeicherte Unraid-Vorlage ist byteidentisch. Das alte Image ist
lokal und anonym in GHCR unverändert nachgewiesen:
`sha256:63218a57850d6b5521a13ccdf93b5c19c958657f7b3c530d0ff583dcac7166bf`.
Nach der verbleibenden Veröffentlichung ist dieser Vergleich nochmals auszuführen.

Bestehende Container, Modellverzeichnisse und gespeicherte Unraid-Vorlagen
werden nicht automatisch migriert. Altes GHCR-Package und dessen Tags bleiben
unverändert erhalten. Bei kritischem Fehler stoppt die Veröffentlichung weiterer
Bestandteile; bereits hochgeladene Dateien werden nicht automatisch gelöscht.
