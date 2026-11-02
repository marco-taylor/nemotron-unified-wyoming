"""Schema and preparation checks, only in an isolated validation container."""
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import jsonschema
import yaml

schema=Path('tests/reference/compose-spec.schema.json')
compose=yaml.safe_load(Path('docker-compose.yml').read_text())
jsonschema.validate(compose,json.loads(schema.read_text()))
print('Compose: passed official compose-spec JSON schema; sha256='+hashlib.sha256(schema.read_bytes()).hexdigest())
root=ET.parse('config/unraid-template.xml').getroot()
assert root.tag=='Container' and root.attrib['version']=='2'
assert root.findtext('Privileged')=='false'
assert root.findtext('Repository')=='ghcr.io/marco-taylor/nemotron-unified-wyoming:latest'
assert any(c.attrib.get('Target')=='/models' and c.attrib.get('Mode')=='rw' for c in root.findall('Config'))
assert root.findtext('Network')=='bridge'
assert root.findtext('Icon')=='https://raw.githubusercontent.com/marco-taylor/nemotron-unified-wyoming/main/assets/icons/nemotron-lowq.png'
assert Path('assets/icons/nemotron-lowq.png').is_file()
assert Path('assets/icons/nemotron-hq.png').is_file()
assert 'net.unraid.docker.icon="'+root.findtext('Icon')+'"' in Path('Dockerfile').read_text()
print('Unraid XML: parsed; local template invariants passed (not a CA acceptance test)')
for path in Path('.github/workflows').glob('*.yml'):
    workflow=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
    assert 'on' in workflow and 'jobs' in workflow
    if path.name=='publish-ghcr.yml':
        assert workflow['on']['push']['branches']==['main']
        assert workflow['on']['workflow_dispatch']['inputs']['publish']['default']=='false'
        assert 'refs/heads/main' in workflow['jobs']['build-and-publish']['if']
        assert workflow['jobs']['build-and-publish']['permissions']['packages']=='write'
        assert 'linux/amd64' in path.read_text()
        assert 'v1.0.0' not in path.read_text()
        publish=workflow['jobs']['build-and-publish']['steps'][-1]['run']
        for tag in ['latest','dev','sha-$COMMIT_SHA']:
            assert 'docker tag nemotron-reviewed:main "$IMAGE:'+tag+'"' in publish
            assert 'docker push "$IMAGE:'+tag+'"' in publish
        assert publish.index('docker push "$IMAGE:latest"') > publish.index('docker push "$IMAGE:dev"')
    print(str(path)+': YAML parsed and release safeguards checked; not remotely executed')

rows=json.loads(Path("config/variables.json").read_text())
names={row[0] for row in rows}
assert len(names)==19
regular_image='ghcr.io/marco-taylor/nemotron-unified-wyoming:latest'
assert compose['services']['nemotron-wyoming']['image']=='${IMAGE:-'+regular_image+'}'
for example in ['.env.example','config/unraid.env.example']:
    assert 'IMAGE='+regular_image in Path(example).read_text()
xml_variables={c.attrib["Target"] for c in root.findall("Config") if c.attrib.get("Type")=="Variable"}
advanced_names={"MAX_AUDIO_SECONDS", "MAX_CONNECTIONS", "CLIENT_TIMEOUT_SECONDS",
                "LOG_LEVEL", "LOG_TRANSCRIPTS", "PUID", "PGID"}
omitted_names={"WYOMING_HOST", "WYOMING_PORT", "LANGUAGE", "STT_DEVICE", "MODEL_DIR",
               "ENCODER_PATH", "DECODER_PATH", "JOINER_PATH", "TOKENS_PATH",
               "MAX_AUDIO_CHUNK_BYTES", "INFERENCE_CHUNK_MS"}
assert xml_variables==advanced_names | {"THREADS"}
assert names - xml_variables == omitted_names and len(omitted_names)==11
configs=root.findall("Config")
assert len(configs)==10
assert len({(c.attrib["Type"], c.attrib["Target"]) for c in configs})==len(configs)
assert len(xml_variables)==sum(c.attrib["Type"]=="Variable" for c in configs)
assert {(c.attrib["Type"], c.attrib["Target"]) for c in configs if c.attrib["Display"]=="always"}=={
    ("Port", "10300"), ("Path", "/models"), ("Variable", "THREADS")}
assert {c.attrib["Target"] for c in configs if c.attrib["Display"]=="advanced"}==advanced_names
defaults={r[0]:r[1] for r in rows}
for c in configs:
    assert {"Name", "Target", "Default", "Mode", "Description", "Type", "Display", "Required", "Mask"} <= set(c.attrib)
    assert c.attrib["Name"].strip() and c.attrib["Description"].strip()
    assert c.attrib["Type"] in {"Port", "Path", "Variable"} and c.attrib["Mask"]=="false"
    assert c.attrib["Display"] in {"always", "advanced"}
    if c.attrib["Type"]=="Variable":
        assert c.attrib["Default"]==defaults[c.attrib["Target"]]
        assert c.text==c.attrib["Default"] and c.attrib["Required"]=="false"
port=next(c for c in configs if c.attrib["Type"]=="Port")
assert port.attrib["Target"]=="10300" and port.attrib["Mode"]=="tcp"
assert port.attrib["Default"]==port.text=="10310" and port.attrib["Required"]=="true"
model=next(c for c in configs if c.attrib["Type"]=="Path")
assert model.attrib["Default"]==model.text=="/mnt/user/appdata/nemotron-unified-wyoming/models/L37-runtime"
assert model.attrib["Target"]=="/models" and model.attrib["Mode"]=="rw" and model.attrib["Required"]=="true"
extra=root.findtext("ExtraParams")
for flag in ["--read-only", "--cap-drop=ALL", "--cap-add=SETUID", "--cap-add=SETGID", "--security-opt=no-new-privileges:true"]:
    assert flag in extra
assert set(re.findall(r'--cap-add[= ]([A-Z_]+)',extra))=={"SETUID", "SETGID"}
assert set(compose["services"]["nemotron-wyoming"]["environment"])==names
for example in [".env.example", "config/unraid.env.example"]:
    assert all((name+"=") in Path(example).read_text() for name in names)
assert {"SETUID","SETGID"} == set(compose["services"]["nemotron-wyoming"]["cap_add"])
assert "user" not in compose["services"]["nemotron-wyoming"]
print(f"All {len(names)} variables retained in Compose/examples; XML: 3 basic settings, 7 advanced variables, 11 omitted defaults; minimal identity-bootstrap caps checked")
