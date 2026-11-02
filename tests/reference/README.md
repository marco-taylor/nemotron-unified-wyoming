Official Wyoming codec fixture source from OHF-Voice/wyoming at
08a0c258df83fea6e1643bcfe67e86243f01cf31 (MIT, license alongside).
Used only for Python/Rust wire interoperability, not recognition.

The adjacent ./wyoming-0.0.0.dist-info/METADATA is a local fixture stub so
upstream ./wyoming/version.py can resolve importlib.metadata without pip.
The actual upstream codec is unmodified; wire-version is not an ASR version.

Phase 5 additionally vendors the unchanged upstream audio/asr/info/error and
util/dataclasses_json modules at that same commit for typed response and real
TCP interoperability. Only Python standard library modules are needed.
The local ./interop.py test harness is project-owned; it is not upstream code.

The separate ./compose-spec.schema.json comes from compose-spec/compose-spec
(main, retrieved 2026-11-01); its separate Apache-2.0 license is preserved in
./compose-spec.LICENSE. SHA256 is recorded in docs/evidence/phase5/config-validation.log.
