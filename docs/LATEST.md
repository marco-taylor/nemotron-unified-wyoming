# Regulärer Imagekanal latest

Reguläre Installation: `ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest`.

Der erfolgreiche main-Workflow veröffentlicht latest, dev und sha-COMMIT aus demselben geprüften linux/amd64-Image. dev bleibt für bestehende Installationen erhalten; bestehende Tags werden nicht gelöscht. latest wird nach Rust-Prüfungen, Architektur-/Runtime-Audit und nach dem Commit-/dev-Tag gepusht. Kein offizieller v1.0.0-Release.

config/unraid-template.xml, ./docker-compose.yml, ./.env.example und config/unraid.env.example verwenden latest für reguläre Installationen. Sämtliche 19 wirksamen Variablen bleiben unverändert. Das Unraid-Template und Docker-Image-Label verwenden ausschließlich das Low-Q-Icon unter assets/icons/nemotron-lowq.png.

Status vor dem Push: lokale Konfigurations-/Index-/Historien-/Imageprüfung wird ausgeführt. Workflow-Ergebnis, Quellcommit, tatsächliche Registry-Digests sowie anonymer Pull und L37-/Healthcheck werden nach dem veröffentlichten Build ergänzt. Noch kein erfolgreicher latest-Pull behauptet.

Keine produktiven Container werden aktualisiert oder neu gestartet. Die vollständige ursprüngliche Git-Sicherung und bisherige Veröffentlichung sind in docs/PHASE6.md dokumentiert; die rein lokale Archivhistorie wird nicht gepusht.
