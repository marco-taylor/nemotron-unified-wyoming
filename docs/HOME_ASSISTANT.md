# Home Assistant nach gemeinsamer Freigabe einrichten

Es wurde keine Home-Assistant-Konfiguration verändert. Bisher ist echte Inferenz über einen isolierten Wyoming-Testclient geprüft; der vollständige Assist-/Satellite-Weg ist noch abzunehmen.

Nach einem absichtlich gestarteten Server unter einer freien LAN-Adresse/Port:

1. In Home Assistant Einstellungen → Geräte & Dienste → Integration hinzufügen → Wyoming Protocol wählen.
2. LAN-Adresse des Unraid-Hosts und den veröffentlichten Hostport eingeben, im Beispiel 10310. Nicht `/models`, nicht Containerport 10300 bei abweichender Portabbildung und nicht `localhost`, wenn HA in einem anderen Container läuft.
3. Unter Einstellungen → Sprachassistenten eine deutsche Assist-Pipeline auswählen bzw. eine getrennte Testpipeline anlegen. Als Sprache-zu-Text den beworbenen Dienst `nemotron-unified-l37-int8` wählen; Sprache Deutsch. Andere vorhandene Pipelines unverändert lassen.
4. Mehrere echte deutsche Befehle hintereinander mit demselben Mikrofon/Satellite prüfen, auch Pause, Stille, Abbruch und Wiederverbindung. Erkennungsqualität, VAD-Ende, Antwortzeit und Speicherauslastung beobachten.

Das Modell benötigt ein extern ermitteltes Sprachende (`audio-stop`). Der Server liefert finale Texte, keine Wyoming-Teiltranskripte. Home-Assistant-Client muss 16-kHz-Mono-PCM mit 16 Bit senden. Es gibt keine automatische mDNS-Erkennung dieses Servers und keine automatische Anmeldung an Home Assistant.

Als gemeinsamer Abnahmesatz eignen sich z. B. Licht schalten, Temperatur abfragen und Rollläden steuern, mit unterschiedlichen Sprechern und Hintergrundgeräuschen. Diese Befehle wurden hier nicht künstlich als erfolgreiche Ergebnisse ausgegeben. Die bisherige zweiwörtige Referenzaufnahme belegt die technische Kette, keine allgemeine Befehlsqualität.

Offizielle Anleitung: [Externe Wyoming-Dienste mit Home Assistant verbinden](https://www.home-assistant.io/integrations/wyoming/). Nur im vertrauenswürdigen LAN nutzen; keine öffentliche Portweiterleitung.
