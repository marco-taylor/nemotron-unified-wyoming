# Bestehende Installationen auf Nemotron Unified Wyoming umstellen

Die Veröffentlichung ersetzt keine Container und überschreibt keine gespeicherten
Unraid-Vorlagen oder Modellverzeichnisse. Das bisherige Image
`ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest` bleibt erhalten.
Der Repository-Link mit dem alten Namen leitet auf das neue Repository weiter;
Registry-Packages werden durch eine GitHub-Umbenennung nicht automatisch umbenannt.

Vor einer ausdrücklich gewünschten Umstellung die eigene Benutzervorlage aus
`/boot/config/plugins/dockerMan/templates-user/` sichern und alle individuellen
Ports, Variablen, Netzwerkmodi, Mounts und PUID/PGID notieren. Die neue Projektvorlage
config/unraid-template.xml nicht ungeprüft über die eigene Vorlage kopieren.

Bei der später bewusst vorgenommenen Bearbeitung den neuen Imagebezug
`ghcr.io/marco-taylor/nemotron-unified-wyoming:latest` und auf Wunsch den neuen
Containernamen verwenden. Eine solche Apply-Aktion kann den Container neu erstellen;
die Veröffentlichung führt sie nicht aus. Alten Container nicht parallel auf
denselben Hostport binden. Keine Home-Assistant-Pipeline wird automatisch geändert.

Ein vollständiges vorhandenes L37-Modellverzeichnis kann am bisherigen Hostpfad
bleiben. Dessen Bind nach `/models` beibehalten; gültige Dateien mit den festen
Hashes werden ohne erneuten Download verwendet. Ein RO-Mount bleibt dafür möglich.
Wer automatische Reparaturen/Downloads nutzen möchte, benötigt einen persistenten
RW-Mount und Schreibrechte für die konfigurierte PUID/PGID. Bestehende Besitzer oder
Rechte werden nicht automatisch geändert. Bei einem neuen Ziel zuerst dessen
Existenz, Platz, Berechtigungen und Prüfsummen prüfen; nichts überschreiben oder
verschieben. Die erste Downloadinitialisierung verwendet UID 99/GID 100 als Default,
der eigentliche Server blockiert anschließend Dateiänderungen zusätzlich per seccomp.

Der neue Standardhostpfad lautet
`/mnt/user/appdata/nemotron-unified-wyoming/models/L37-runtime`. Es besteht keine
Pflicht, funktionierende alte Pfade auf diesen Namen zu migrieren. Der alte lokale
Workspacepfad `/mnt/nvme/appdata/codex-workspace/nemotron-unified-rust-wyoming`
bleibt als Kompatibilitätslink auf das umbenannte Projekt bestehen.

Alle 19 Runtime-Variablen bleiben gültig. Bereits gespeicherte Unraid-Vorlagen
behalten ihre expliziten Sonderwerte; die vereinfachte neue Vorlage entfernt keine
Variablen aus dem Server. Die neue Oberfläche zeigt Hostport 10310→10300/TCP,
Modellpfad und THREADS=2; sieben Variablen stehen im Zusatzbereich. Manuelle
Einzelpfade und andere zulässige Werte müssen bewusst übernommen werden.
Bei abweichendem WYOMING_PORT auch das interne Portziel anpassen. Hostnetz ignoriert
Bridge-Portmapping und verwendet direkt den Serverport (Default 10300).

Als einziges Standardicon dient weiterhin assets/icons/nemotron-lowq.png.
Vorgehen für gespeicherte Icon-URLs: docs/UNRAID.md. Aktuelle öffentliche Nachweise,
Digest und CA-Status: docs/PHASE12_PUBLICATION.md. Eine veröffentlichte XML-Datei
ist noch keine bestätigte Aufnahme in Community Applications.
