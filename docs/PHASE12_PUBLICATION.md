# Phase 12 – Veröffentlichung Nemotron Unified Wyoming

Status am 03.11.2026: Repository, main, Modell-Release und neues GHCR-Package
sind öffentlich. Die Übernahme im CA-Katalog wird gesondert geprüft; eine
GitHub-Veröffentlichung ist keine Bestätigung der CA-Feed-Aktualisierung.
Freigabe des Nutzers gilt für Repository-Umbenennung, den Modell-Release,
neues GHCR-Image und CA-Aktualisierung nach erfolgreichen Prüfungen.

## Sicherung und Bestandsaufnahme

Ausgangscommit: `91984c9450e05e8b8593547daa8979438c36e3f7` auf
`feature/rename-model-download`, mit den noch uncommitteten Phase-11.1-Dateien.
Bisheriges main: `d7af454c269da902b220ea50d23d256220edb376`.
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
Dieser Stand wurde vor der main-Übernahme vollständig lokal geprüft.

Der vollständige Funktionstest ist inzwischen bestanden. Funktionscommit
`01733f79a25c4cf0571d6b047f5fee4c7d4cb8e3` ist auf `release/phase12` gepusht;
main und damit der bestehende CA-Template-Bezug wurden bis zur öffentlichen
Image-Erreichbarkeit bewusst unverändert gelassen. Ein zusätzliches vollständiges Bundle
`/mnt/nvme/appdata/codex-workspace/nemotron-phase12-backups/phase12.HvuUMQ/functional-progress.bundle`
wurde verifiziert und tatsächlich in einen separaten Mirror zurückgespielt.

Nach erfolgreichem anonymem Kandidaten-Pull wurde main ohne Force-Push von
`d7af454c269da902b220ea50d23d256220edb376` auf
`c16f41d35ff410b38f1c0fd136c1e09bf0b9d71a` vorgespult. Dieser Commit ergänzt
die kontrollierte Workflow-Übernahme eines festen validierten Image-Digests.
Seit dem Funktionscommit sind nur Dokumentation und Workflow geändert;
Rust, Modelle und Inferenz sind identisch. Das zusätzliche vollständige
`/mnt/nvme/appdata/codex-workspace/nemotron-phase12-backups/phase12.HvuUMQ/completion-before-main.bundle`
wurde vor der Übernahme erstellt und erfolgreich verifiziert.

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

## Öffentliches GHCR-Image

Das vollständig lokal geprüfte Image bleibt unter seinem Kandidaten-Tag erhalten:
`ghcr.io/marco-taylor/nemotron-unified-wyoming:validated-phase12-660fd95d171f`.
Digest `sha256:661f2c7c779e7c13b7fcf40d9a0a2252e8e64b93e1615d7254de5446b038a679`,
linux/amd64; lokale Image-ID
`sha256:660fd95d171f1c992858650aeb8828f7acff01488943f147c91da3bfd2f96c87`.

GitHub legte das Package zunächst privat an. Nach der Public-Umstellung durch
den Benutzer funktionierte der Pull mit einer neuen Docker-Konfiguration mit
`auths={}` ohne GitHub-Zugangsdaten. Anschließend wurden latest und der
Kompatibilitätstag dev aus exakt diesem Image veröffentlicht. Keine alten Tags
oder Packages gelöscht. Package: https://github.com/users/marco-taylor/packages/container/package/nemotron-unified-wyoming

Reguläres Image: `ghcr.io/marco-taylor/nemotron-unified-wyoming:latest`.
Der erwartete Digest für latest und dev ist identisch mit dem validierten
Kandidaten: `sha256:661f2c7c779e7c13b7fcf40d9a0a2252e8e64b93e1615d7254de5446b038a679`.
Der manuell ausgelöste main-Workflow baut und testet den aktuellen Quellstand,
lädt anschließend den festen öffentlichen Kandidaten-Digest, auditiert diesen
und testet erneut eine echte leere Modellinitialisierung. Danach taggt er exakt
dieses Image. Ein unabhängig neu gebautes Image muss aufgrund von Buildzeit
und Revision-Label keinen identischen Digest haben und ersetzt den geprüften
Kandidaten in dieser Übernahme nicht.

Der automatisch ausgelöste Publish-Lauf wurde durch die explizite Übernahme
über die bestehende Workflow-Konkurrenzregel abgelöst. Reine spätere Markdown-
Änderungen starten weiterhin CI, veröffentlichen aber kein neues Image.

Erfolgreicher Publish-/Übernahmelauf:
https://github.com/marco-taylor/nemotron-unified-wyoming/actions/runs/41542903291

Erfolgreiche unabhängige main-CI mit Release-Build, Formatprüfung, 33 Rust-Tests,
strengem Clippy, 20 Downloader-Tests und Offline-Fehlerprüfung:
https://github.com/marco-taylor/nemotron-unified-wyoming/actions/runs/41542884612
Der abschließende Commit aktualisiert ausschließlich Markdown-Dokumentation und
verwendet `[skip ci]`; getesteter Programm- und Image-Stand bleiben identisch.

Der anschließende erneute anonyme Pull von latest und dev hat bestanden.
Beide Registry-Manifeste bestätigen den oben genannten identischen Digest und
`linux/amd64`. Auch der Commit-Tag
`sha-c16f41d35ff410b38f1c0fd136c1e09bf0b9d71a` gehört zur kontrollierten Übernahme.

## Community Applications

Der aktuelle offizielle Feed `https://ca.unraid.net/assets/feed/applicationFeed.json`
enthält bereits genau eine Nemotron-App unter dem alten Namen sowie das bestehende
Repositoryprofil. Daher keine neue Einreichung/zweite Registrierung. Aktuell zeigt
dieser Eintrag noch auf das alte Image und den alten Template-Link. Die Umbenennung
des GitHub-Repositories leitet diese URL bereits sicher weiter.

config/unraid-template.xml ist auf main am bisherigen Pfad veröffentlicht,
mit neuem Image, Projektnamen, Low-Q-Icon und TemplateURL. Alte Repository- und
Template-Adressen leiten weiterhin auf dieses Repository. Die bestehende
Repositoryregistrierung bleibt erhalten; keine doppelte Einreichung angelegt.

Öffentliches Template:
https://raw.githubusercontent.com/marco-taylor/nemotron-unified-wyoming/main/config/unraid-template.xml

Das CA-Portal https://ca.unraid.net/submissions verlangt eine gesonderte Anmeldung
mit dem Unraid-Konto; eine solche Sitzung ist in dieser Umgebung nicht vorhanden.
Für eine erforderliche Portaländerung muss die **bestehende** Einreichung auf die
neue Repository-Adresse aktualisiert und Validate/Scan ausgeführt werden.
GitHub-/GHCR-Anmeldedaten werden dafür weder weitergegeben noch zweckentfremdet.
Aktueller offizieller Feed-Abgleich und gegebenenfalls noch offene Übernahme
werden im Abschluss unten ausgewiesen.

Offizielle Anforderungen und Aktualisierungsprüfung:
https://ca.unraid.net/submit/help und
https://ca.unraid.net/submit/help/repository-xml.

## Schutz bestehender Installationen

Die erste Phase-12-Zwischenprüfung zeigte 31 unveränderte Container. Bei der
Fortsetzung hatten ESPHome und teddycloud inzwischen andere IDs: die alten
IDs `52ca661d7bc4` und `4e1acaf94051` waren nicht mehr vorhanden; stattdessen
existierten `45baac53a65b` (erstellt 02.11.2026 23:02:04 UTC) und
`a7592b772c86` (23:01:44 UTC). Diese beiden Container wurden von dieser Arbeit
nicht bearbeitet. Deshalb wird ausdrücklich **keine unveränderte 31er-Baseline**
behauptet. Die übrigen 29 stimmen in ID, Config, HostConfig, Mounts, Status,
Start-/Endzeit, ExitCode und RestartCount mit der ursprünglichen Baseline überein.
Der alte Nemotron-Container bleibt im vorgefundenen Zustand `created`.

Die gespeicherte Nemotron-Vorlage ist gegenüber der ursprünglichen Baseline
byteidentisch, SHA256 `88a127b9efd70910dd7613514f9c72d3546aa53257438cf961188d6959d2949b`.
Zusätzlich wurden bei der Fortsetzung alle 45 gespeicherten Benutzer-XML-Vorlagen
gehasht und am Abschluss erneut verglichen. Keine Vorlage überschrieben.
Das alte Image ist lokal und anonym in GHCR unverändert nachgewiesen:
`sha256:63218a57850d6b5521a13ccdf93b5c19c958657f7b3c530d0ff583dcac7166bf`.
Das alte GHCR-Package und dessen Tags werden nicht beschrieben oder entfernt.

Bestehende Container, Modellverzeichnisse und gespeicherte Unraid-Vorlagen
werden nicht automatisch migriert. Altes GHCR-Package und dessen Tags bleiben
unverändert erhalten. Bei kritischem Fehler stoppt die Veröffentlichung weiterer
Bestandteile; bereits hochgeladene Dateien werden nicht automatisch gelöscht.

## Abschlussprüfung am öffentlichen latest

Erneuter vollständiger Lauf mit scripts/test-model-download-release.sh und
`IMAGE=ghcr.io/marco-taylor/nemotron-unified-wyoming:latest` erfolgreich:

| Prüfung | Tatsächliches Ergebnis |
|---|---|
| Anonymer GHCR-Zugriff | Kandidat, latest und dev mit frischer Docker-Konfiguration ohne gespeicherte Zugangsdaten erfolgreich |
| Leere Erstinstallation | Neues isoliertes Modellverzeichnis, vier HTTPS-Downloads vom festen öffentlichen Release, 726.885.887 Byte |
| Integrität | Alle vier Größen und SHA256 stimmen mit den oben dokumentierten festen Werten überein |
| Healthcheck / Wyoming | healthy, describe/info, deutsche Transkription, erwartete Protokollfehler und Audio-Chunk-Limit bestanden |
| Deutsche Transkription | Neun Anfragen, je drei nach Installation, Neustart und Reparatur: immer `Einsteigen bitte.` |
| Neustart | Kein zusätzlicher Download; Inodes, mtimes und SHA256 der vier Modelle identisch |
| Fehlende / beschädigte Datei | Nur tokens bzw. joiner gezielt nachgeladen, andere Dateien unverändert; gesicherte Testoriginale erhalten |
| Abbruchreste | Kontrollierter eigener Orphan bereinigt; keine finalen Modelldateien verändert |
| Rechte / Sicherheit | UID 99, GID 100, alle Modell-Dateien 99:100, CapEff/CapPrm/CapAmb=0, NoNewPrivs=1, zwei seccomp-Filter |
| Unraid-Template | XML und tatsächlicher installierter DockerMan-Parser bestanden; drei Grundeinstellungen, sieben erweiterte Variablen, elf Defaults ausgelassen |
| Runtime-Variablen | Alle 19 in config/variables.json und Compose erhalten, keine Änderungen an der STT-Inferenz oder Phase-9-Experimente |
| Öffentliche Raw-Dateien | Template, ca_profile und beide Icons anonym geladen und byteidentisch zum lokalen geprüften Stand |
| Alte Installation | 29 ursprüngliche Container unverändert, zwei extern ersetzte Container ausdrücklich ausgewiesen; 45 Benutzer-XMLs unverändert |
| Altes GHCR-Image | Anonym abrufbar, alter Digest unverändert; lokale Image-ID ebenfalls unverändert |

Der Testcontainer wurde kontrolliert beendet und entfernt. Der neue Testcache
bleibt für die Nachprüfung lokal erhalten. Keine produktiven Container gestartet,
gestoppt oder neu erstellt; keine Modelle verschoben oder gelöscht.

Öffentliche Icons, unverändert und ausschließlich Low-Q als Standard:

- Low-Q, 82.756 Byte: https://raw.githubusercontent.com/marco-taylor/nemotron-unified-wyoming/main/assets/icons/nemotron-lowq.png
- HQ, 1.560.271 Byte: https://raw.githubusercontent.com/marco-taylor/nemotron-unified-wyoming/main/assets/icons/nemotron-hq.png

## Offene Punkte

Der offizielle CA-Feed zeigt bei der Abschlusskontrolle weiterhin genau einen
Eintrag unter `nemotron-unified-rust-wyoming` mit dem alten Image. Die aktualisierte
Quelle ist bereits auf main öffentlich; die neue CA-Anzeige ist **noch nicht
bestätigt**. Das bestehende Portal-Listing muss bei Bedarf durch den angemeldeten
Kontoinhaber aktualisiert/gescannt werden. Der fehlende Unraid-Portalzugang ist
der verbleibende externe Blocker; keine neue Einreichung angelegt.

Weitere spätere Abnahme: repräsentativer deutscher Sprachkorpus, längerer Betrieb
und bewusste End-to-End-Abnahme in einer Home-Assistant-Pipeline. Kein offizieller
Server-v1.0.0-Release erstellt. Die Belege liegen lokal unter docs/evidence/phase12;
große Testdaten, Modellgewichte und lokale Docker-Konfigurationen bleiben ignoriert.
