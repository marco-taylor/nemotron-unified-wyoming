# Phase 11.1 – GitHub Releases für den exakten Nemotron-L37-Export

Stand: 02.11.2026. Branch `feature/rename-model-download`, Ausgangscommit `91984c9450e05e8b8593547daa8979438c36e3f7`. Ausschließlich Prüfung und lokale Vorbereitung. Keine Gewichte hochgeladen, kein Tag oder GitHub-Release erstellt, kein Repository umbenannt, kein Push, kein Image veröffentlicht und kein produktiver Container verändert.

## Ergebnis

GitHub Releases ist für die vier konkreten Laufzeitdateien technisch geeignet und wird als bevorzugte erste Quelle empfohlen. Alle Assets liegen unter dem konservativ angewendeten offiziellen Limit von 2 GiB pro Datei. Die Modelllizenz erlaubt grundsätzlich Weitergabe und Bearbeitung unter ihren Bedingungen; eine formatspezifische Sperre für ONNX oder Quantisierung ist nicht erkennbar. Das ist eine Prüfung der verfügbaren Lizenz-/Herkunftsnachweise, keine Garantie, dass Rechte Dritter ausgeschlossen sind.

Das Modell stammt von NVIDIA. Dieses Projekt hat **kein Modell trainiert oder feinabgestimmt**, sondern den vorhandenen Checkpoint für den gepinnten Backendstand nach ONNX exportiert und den Encoder teilweise quantisiert. Eine öffentliche Freigabe ist weiterhin erforderlich. Der aktive Downloader bleibt gesperrt, bis die realen Release-Assets veröffentlicht und anonym verifiziert sind.

## 1. Tatsächlicher Dateibestand

Quelle unverändert unter models/L37-runtime. Alle Prüfungen ausschließlich lesend, im isolierten Container mit UID 99/GID 100, read-only Projektmount und deaktiviertem Netzwerk. Größenumrechnung: 1 MiB = 1.048.576 Byte; 1 GiB = 1.073.741.824 Byte. Gerundete Anzeigewerte ändern die exakten Bytewerte nicht.

| Datei | Byte | MiB | GiB | Format und Funktion |
|---|---:|---:|---:|---|
| models/L37-runtime/encoder.int8.onnx | 675.328.677 | 644,043614 | 0,628948842 | ONNX ModelProto, FastConformer/RNN-T-Encoder mit Sprachprompt; partiell QUInt8 |
| models/L37-runtime/decoder.onnx | 36.745.480 | 35,043221 | 0,034221895 | ONNX ModelProto, RNN-T-Predictor/Decoder, FP32 |
| models/L37-runtime/joiner.onnx | 14.768.802 | 14,084627 | 0,013754519 | ONNX ModelProto, RNN-T-Joiner, FP32 |
| models/L37-runtime/tokens.txt | 42.928 | 0,040939 | 0,000039980 | UTF-8-Token-Tabelle, **kein ONNX-Graph**; 4096 eindeutige fortlaufende IDs |
| **Gesamt** | **726.885.887** | **693,212401** | **0,676965236** | Vier erforderliche Laufzeitdateien |

| Datei | SHA256 |
|---|---|
| models/L37-runtime/encoder.int8.onnx | `8e1b140b85900dcaede7e5fc05c1adfd48d4a0585e3b55ec2a10cded7042c96d` |
| models/L37-runtime/decoder.onnx | `e5281215d86116e425191324830090922ec7732a34b1f5203d3b5a3564a20d97` |
| models/L37-runtime/joiner.onnx | `7abd80133827b59dbd3b57c47242d6001607ed14acda5db36ae28d64a3de8af8` |
| models/L37-runtime/tokens.txt | `94139a0b2134fd40664ca72260026fa8a073336bb2f062239c8ecde2c8031763` |

Alle drei Graphen verwenden ONNX IR 8 und Standard-Opset 17. Der Encoder enthält zwei identische Standard-Opset-Importeinträge; der offizielle ONNX-Checker akzeptiert den vorhandenen Graphen. Producer: Encoder `onnx.compose.merge_models` 1.0, Predictor/Joiner PyTorch 2.7.1. 265 MatMulInteger-Knoten bestätigen die partielle Encoderquantisierung; ein vollständig INT8-Modell wird nicht behauptet.

ONNX 1.18.0 aus der bestehenden Exportumgebung wurde ohne Paketdownload wiederverwendet. Vollständige Protobuf-Dateien geladen, `onnx.checker.check_model` für alle drei Pfade erfolgreich. Rekursive Tensorprüfung einschließlich Graphattribute und Sparse-Unterstrukturen: keine externen Tensorreferenzen. Es werden **keine zusätzlichen ONNX-Datendateien** benötigt. Alle vier Größen und SHA256 erneut bestätigt, lesbar mit 99:100. scripts/inspect_model_release.py erzeugt den Rohbericht docs/evidence/phase11_1/model-audit.json; dieser lokale Beleg bleibt ignoriert.

## 2. Aktuelle GitHub-Limits und Betrieb

Die [spezifische Release-Dokumentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases#storage-and-bandwidth-quotas) nennt maximal 1000 Assets, jede Datei kleiner als 2 GiB, ohne festes Limit für Release-Gesamtgröße oder Release-Bandbreite. Deshalb gilt hier strikt `< 2.147.483.648 Byte`; Gleichheit wäre nicht ausreichend. Alle vier Laufzeitdateien und alle zehn Textassets erfüllen das. Keine Aufteilung oder Komprimierung erforderlich. Der größere originale NeMo-Checkpoint wird nicht verteilt; seine Größe ist für diese vier Assets unerheblich.

Das bedeutet keine unbegrenzte Verfügbarkeitsgarantie: Die [Acceptable Use Policies, Abschnitt 9](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies#9-excessive-bandwidth-use) erlauben bei übermäßiger Nutzung unter anderem Drosselung und Sperren. Netz-/Provider-Ausfälle, gelöschte Releases, Rechteänderungen und gesperrte Accounts bleiben Betriebsrisiken. Es gibt hier keine nachgewiesene garantierte Downloadrate oder projektbezogene SLA.

Öffentliche Assets benötigen keine Zugangsdaten; die [Release-Asset-API](https://docs.github.com/en/rest/releases/assets#get-a-release-asset) dokumentiert anonymen Zugriff und Antworten per direktem Stream oder Weiterleitung. Der Downloader verwendet feste Browser-Downloadadressen ohne vorgeschaltete API-Abfrage. Die [60 anonymen REST-API-Anfragen pro Stunde und IP](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api#primary-rate-limit-for-unauthenticated-users) sind ein separates API-Limit, keine dokumentierte Downloadquote für diese direkten Browseradressen. Git-LFS- oder GHCR-Quoten werden damit nicht vermischt.

GitHubs [API-Beispiel für browser_download_url](https://docs.github.com/en/rest/releases/assets#get-a-release-asset) belegt die Form `/releases/download/TAG/ASSET`. Die Tagadresse wird im Image fest hinterlegt, keine `/latest`-Adresse. HTTPS-Weiterleitungen auf GitHub-Asset-Storage sind zulässig; kurzlebige signierte CDN-Zieladressen niemals als feste Quelle speichern. Firewall/Proxy muss auch die tatsächlichen HTTPS-Weiterleitungsziele erlauben. Öffentliche Erreichbarkeit und konkreter Redirectablauf bleiben bis zur Freigabe ungetestet.

Ein gewöhnlicher Tag allein macht ein Release noch nicht unveränderlich. GitHubs [Immutable Releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases) sperren veröffentlichte Assets und Tag gegen nachträgliche Änderung und erzeugen eine Attestation. Empfehlung: nach gesonderter Freigabe diese Funktion aktivieren, alle Assets zuerst vollständig an einen Entwurf hängen, prüfen und erst dann veröffentlichen. Diese Phase hat auch keinen Entwurf angelegt. Auch Immutability ersetzt keinen Schutz gegen vollständige Löschung oder Ausfälle; die festen SHA256 bleiben der lokale Vertrauensanker.

## 3. NVIDIA-Herkunft und Lizenz

Original: [nvidia/nemotron-labs-unified-asr-0.6b](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b), laut NVIDIA-Modellkarte Version `Nemotron-Labs-Unified-ASR-0.6b-v1`, FastConformer/RNN-T. Ursprünglich verwendete Repository-Revision `023ce907267a09a308a5cb69239447cb3d0c1597`. Originalcheckpoint models/source/nemotron-labs-unified-asr-0.6b.nemo: 2.507.735.040 Byte, SHA256 `1718cc1b44fb8597b2356328d706a8d89f31c389ca6f2256c2e3f743c0246936`. Die offizielle revisionsgebundene Dateiliste bestätigt diesen LFS-Hash; kein erneuter Gewichtedownload.

**Herkunftskorrektur:** Phase 11 hatte im Manifest die Revision `e141dff433df9ab1962eec4d8d494560f9a02009` eingetragen. Die ursprünglichen Downloadbelege nennen `023ce907267a09a308a5cb69239447cb3d0c1597`. Beide offiziellen revisionsgebundenen API-Antworten und Lizenzdateien wurden direkt abgeglichen: Checkpoint-Hash, Größe und Lizenz sind identisch. Lizenz-SHA256 `222d7f77ca2f2c26bf45156776b6d70207a9f963b3d9ff43e659684c1ddd4895`, jeweils 2845 Byte. config/model-manifest.json dokumentiert jetzt die tatsächlich verwendete Revision. Keine Modell-Hashes, URLs, Variablen, Inferenz oder Downloadlogik geändert.

Maßgeblich ist die vollständige [NVIDIA-Lizenz am ursprünglichen Modellstand](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b/blob/023ce907267a09a308a5cb69239447cb3d0c1597/LICENSE.md), lokal unverändert unter releases/models-l37-v1.0.0/LICENSE.OpenMDW-1.1.md. OpenMDW-1.1 gewährt breite Nutzungs-/Bearbeitungs-/Weitergaberechte. Daraus ergibt sich grundsätzlich auch die Zulässigkeit der Konvertierung und Quantisierung samt Weitergabe; kein besonderer ONNX-Ausschluss gefunden. Originalgewichte und abgeleitete Exporte bleiben Modellmaterialien; MIT für den Server ersetzt diese Lizenz nicht.

Bei Weitergabe müssen Lizenz, Copyright und anwendbare Herkunftshinweise erhalten bleiben. Copyright: NVIDIA CORPORATION & AFFILIATES, 2026. Lizenzbedingungen einschließlich der Beendigungsklausel bei bestimmten Patent-/Urheberrechtsklagen beachten. Gewährleistung wird ausgeschlossen; mögliche Rechte Dritter müssen gesondert berücksichtigt werden. Keine ausdrückliche neue Markenlizenz, Herstellerpartnerschaft oder Freistellung behaupten.

Zur nachvollziehbaren Dokumentation liegen außerdem die unveränderte NVIDIA-Modellkarte sowie die Hinweise zu Bias, Explainability, Privacy und Safety bei. Diese zusätzlichen Dokumente sind konservativ erhaltene Herkunftsinformationen, keine behauptete formale Pflicht zu jedem einzelnen Dateinamen und keine neue Zertifizierung des Projekts. Alle sechs Originaltexte wurden revisionsgebunden geladen und gegen die bereits aufgezeichneten offiziellen Git-Blob-IDs geprüft. Datenkorpora oder Trainingsdaten werden nicht verteilt; die Lizenzprüfung ist keine vollständige Prüfung sämtlicher etwaiger Trainingsdatenrechte.

Unsere technische Anpassung: sherpa-onnx-Exporter Commit `31ba0e438f8065189a8e5589d84dfd7faf516d3d`, L37/Center7/Right7, Encoder partiell QUInt8, Predictor/Joiner FP32; NeMo `43dd97ddf50dc3b3104cc22471f6e30407d1b18c`. Erfolgreicher lokaler Export ist unter models/L37-cpu/export-status.json mit Returncode 0 belegt; frühere gescheiterte Versuche bleiben als historische Belege erhalten. Versionen und tatsächliche Laufzeitvalidierung: docs/PHASE4_RESULTS.md. Apache-2.0 des Exportwerkzeugs überschreibt nicht die Modelllizenz. Es wird kein Exporter-Quellcode als Modellasset mitverteilt; bei späterer Beigabe von Code dessen eigene Lizenz-/NOTICE-Pflichten zusätzlich prüfen.

## 4. Vorbereiteter separater Modell-Release

Geplantes Repository: https://github.com/marco-taylor/nemotron-unified-wyoming.
Geplanter Tag: `models-l37-v1.0.0`. Er versioniert den exakten adaptierten Laufzeitsatz und ist **kein offizieller Server-v1.0.0-Release**. Nicht als neuester Anwendungsrelease markieren (`make_latest=false`); ein Namenspräfix allein verhindert die Latest-Markierung nicht zuverlässig.

Lokale Uploadplanung: releases/models-l37-v1.0.0.plan.json. Die vier Gewichte bleiben an ihrem vorhandenen Ort; keine zweite Kopie, kein Archiv und kein Upload. Je Datei ein Asset ermöglicht gezielte Reparaturen und unmittelbare Prüfsummenprüfung.

| Vorgesehene Assets | Lokale Quelle |
|---|---|
| Vier Laufzeitdateien, gleiche Basenamen wie bisher | models/L37-runtime |
| SHA256SUMS | releases/models-l37-v1.0.0/SHA256SUMS |
| Modelllizenz mit NVIDIA-Copyright | releases/models-l37-v1.0.0/LICENSE.OpenMDW-1.1.md |
| Unveränderte NVIDIA-Modellkarte | releases/models-l37-v1.0.0/MODEL_CARD.NVIDIA.md |
| Bias-/Explainability-/Privacy-/Safety-Hinweise | releases/models-l37-v1.0.0/bias.md, releases/models-l37-v1.0.0/explainability.md, releases/models-l37-v1.0.0/privacy.md, releases/models-l37-v1.0.0/safety.md |
| Herkunft/Revisionen/Hashes und Anpassung | releases/models-l37-v1.0.0/PROVENANCE.json |
| Lesbare Export-/Lizenzabgrenzung | releases/models-l37-v1.0.0/EXPORT_INFO.md |
| Geplantes festes Downloadmanifest | releases/models-l37-v1.0.0/model-manifest.json |

Insgesamt 14 Assets und **726.971.870 Byte** einschließlich aller Texte und Prüfsummen; die vier Laufzeitdateien allein bleiben **726.885.887 Byte**. Die Prüfsummenliste enthält alle anderen 13 Assets, nicht sich selbst. Gewichtedateien gehören nur als Release-Assets ins Hosting, niemals in Git, Git LFS oder das Image. Eine zusätzliche Komprimierung wird ohne gemessenen Nutzen nicht vorgenommen. Kein Modelltraining wird als Projektleistung ausgegeben.

### Geplante, noch nicht aktivierte Downloadadressen

```text
https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/encoder.int8.onnx
https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/decoder.onnx
https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/joiner.onnx
https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/tokens.txt
```

Weitere Textassets verwenden denselben Basispfad und ihren jeweiligen Basenamen. Diese URLs sind **Planwerte**, nicht als verfügbar bestätigt. Kein öffentlicher Asset-Download oder Asset-HEAD-Test wurde durchgeführt. Das aktive config/model-manifest.json enthält weiterhin vier `null`-URLs; scripts/check_model_source.py blockiert weiterhin Veröffentlichung.

## 5. Downloader-Eignung und Grenzen

Die bestehende Implementierung scripts/model-init.py benötigt für GitHub-Assets keinen neuen Runtime-Schalter, kein Token, keine API-Integration und keinen anderen Modelltyp. Nach genehmigter tatsächlicher Veröffentlichung werden ausschließlich die vier im Image geprüften URL-Felder übernommen. Namen, Bytewerte, SHA256 und die gesamte Sicherheitslogik bleiben erhalten. Ein öffentlich heruntergeladenes Manifest wird nicht dynamisch als Vertrauensanker übernommen.

Erhalten bleiben vollständige SHA256-Prüfung, Wiederverwendung gültiger Dateien auch auf RO-Mounts, gezielter Ersatz fehlender/defekter Dateien, flock, temporäres Schreiben, Größenlimit, HTTPS/TLS, Timeout, fsync, atomare Übernahme und Sicherung beschädigter Originale. Neustarts verursachen bei gültigen Modellen keinen Download. Nach Netzwerkfehlern genügt ein späterer Start; bereits abgeschlossene gültige Dateien werden nicht erneut geladen. Kein Byte-Range-Resume erforderlich oder zugesagt. Keine neue Berechtigung und keine neue Runtime-Variable; PUID/PGID-Wechsel und seccomp-Schutz aus Phase 11 bleiben unverändert.

**Unterbrechungsgrenze ausdrücklich:** Normale Fehler entfernen die eigene temporäre Datei. Bei hartem SIGKILL/Stromausfall können `.part-*`-Reste im Cache zurückbleiben. Sie werden niemals unter den vier finalen Modellnamen akzeptiert und nie für Inferenz verwendet. Ein vollständig temporärdateifreier Cache nach beliebigem Absturz ist aktuell nicht garantiert; falls diese Anforderung wörtlich gilt, vor Produktivfreigabe eine sichere Staging-/Bereinigungsstrategie ergänzen und gesondert testen. Keine pauschale Löschung bestehender Dateien vorbereiten.

Lizenz und Herkunft gehören zum Release und zur späteren Installation. Das aktuelle Phase-11-Image enthält bereits die vollständige Modelllizenz. Für Aktivierung der öffentlichen Quelle auch die gebündelten Herkunfts-/NVIDIA-Hinweise im Distributionspaket bzw. Image und möglichst neben dem persistenten Cache berücksichtigen; eine Installation lädt derzeit nur die vier Laufzeitdateien. Deren vier feste Hashes werden nicht durch eine nur remote geladene Prüfsummenliste ersetzt.

## 6. Ausgeführte Tests

| Prüfung | Ergebnis |
|---|---|
| Dateigrößen und GitHub-Limit | Alle vier Modelle und zehn Texte unter 2 GiB, 14 < 1000 Assets |
| SHA256 / Lesbarkeit | Alle vier Originale erneut korrekt und als UID 99/GID 100 lesbar |
| ONNX-Struktur | Alle drei Graphen ONNX-Checker erfolgreich; rekursiv keine externen Tensoren |
| Token-Tabelle | UTF-8, 4096 eindeutige fortlaufende IDs bestätigt |
| Herkunft / Lizenz | Zwei NVIDIA-Revisionen abgeglichen; identischer Checkpoint und Lizenztext; ursprüngliche Revision korrigiert |
| Release-Struktur | scripts/validate_model_release.py prüft alle 14 lokalen Quellen, Namen, Größen, SHA256SUMS, Plan-URLs und Herkunfts-Hashes; bestanden |
| Kontrollierte Downloader-Tests | Alle 17 bestehenden Tests erneut als UID99/GID100 bestanden, einschließlich echtem lokalen HTTPS mit Zertifikatsprüfung |
| Vorhandene echte Modelle | Offline-Aufruf der aktuellen Initialisierungsfunktion auf dem RO-Modellverzeichnis; unerwarteter Download hätte explizit einen Fehler ausgelöst; bestanden |
| Fehlende / defekte Dateien | Fixture-Tests: nur betroffene Dateien geladen, SHA256/Größe geprüft, beschädigtes Original erhalten |
| Netz-/Platzfehler / Abbruch / Konkurrenz | Bestehende Fehler-, SIGKILL-, Wiederanlauf- und Konkurrenztests bestanden; Einschränkung zu verbleibenden Teilstücken oben |
| Veröffentlichungsblockade | Aktive vier URLs bleiben leer; Veröffentlichungsgate bleibt absichtlich gesperrt |
| Öffentliche Release-Downloads | Nicht durchgeführt, benötigen separate Freigabe |
| Bestandsschutz / Veröffentlichungsprüfung | Alle 31 vorbestehenden Container unverändert; Arbeitsbaumprüfung von 142 Dateien ohne Secret-/Modellgewichtbefund |

Reproduktion der Prüfungen im isolierten Python-Container: scripts/inspect_model_release.py mit der bereits vorhandenen ONNX-Exportumgebung, scripts/validate_model_release.py sowie `python3 -m unittest discover -s tests -p model_init_test.py -v`. Keine Rust-/Inferenzänderungen, daher kein erneuter Rust- oder Docker-Build erforderlich. Modelldateien, Produktivkonfigurationen, Images und laufende Dienste bleiben unverändert. Rohbelege unter docs/evidence/phase11_1 sind lokal ignoriert.

## 7. Empfehlung und noch notwendige Schritte

Für diesen kleinen, fest versionierten Satz bietet GitHub Releases die einfachere Verwaltung im ohnehin vorgesehenen Repository. Einzelne direkte Downloads, feste Hashes und Immutability reichen für unsere Erstinstallation; eine zusätzliche Hugging-Face-Veröffentlichung ist aktuell nicht nötig. Hugging Face kann später als genehmigter Mirror oder für zusätzliche Modellvarianten sinnvoll sein. Keine gemessene Geschwindigkeits- oder Verfügbarkeitsüberlegenheit von GitHub gegenüber Hugging Face wird behauptet.

Vor Veröffentlichung fehlen:

1. Freigabe der hier dokumentierten Modellweitergabe und des neuen Repository-Ziels; keine eigenständige Umbenennung.
2. Vollständige Prüfung der 14 vorbereiteten Assets und Hinweisabdeckung; bei offenen Fremdrechten nicht veröffentlichen. Anforderungen an absturzbedingte temporäre Reste festlegen.
3. Erst nach Freigabe Immutable Releases aktivieren, Modell-Tag/Entwurf am geprüften Commit anlegen, alle 14 Assets hochladen und veröffentlichen; `make_latest=false`. Keine Git-/Image-Gewichte und kein Server-v1.0.0-Release.
4. Dann alle vier echten öffentlichen Assets ohne Authentifizierung von den versionierten Adressen laden, Weiterleitungen, Größe und SHA256 bestätigen; optional GitHub-Attestation prüfen. Dieser öffentliche Test fand noch nicht statt.
5. Erst danach vier aktive Manifest-URLs setzen, Notice-Abdeckung der Containerdistribution ergänzen und komplette isolierte Neuinstallation mit leerem persistenten Cache, anschließend Neustart, Offline-Wiederverwendung und gezielte Reparatur der echten Dateien testen.
6. GitHub-/GHCR-/CA-Migration nur nach eigener weiterer Freigabe. Alte Images, Tags, gespeicherte Vorlagen und existierende Container nicht automatisch ersetzen.

Die Prüfung bestätigt somit technische Eignung und eine lizenztextbasierte grundsätzliche Weitergabemöglichkeit, jedoch noch keine öffentlich getestete Downloadquelle und keine Veröffentlichungserlaubnis.
