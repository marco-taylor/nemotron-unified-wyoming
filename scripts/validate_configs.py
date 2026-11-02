"""Schema and preparation checks, only in an isolated validation container."""
import hashlib
import json
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
assert root.findtext('Repository')=='ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest'
assert any(c.attrib.get('Target')=='/models' and c.attrib.get('Mode')=='ro' for c in root.findall('Config'))
assert root.findtext('Network')=='bridge'
assert root.findtext('Icon')=='https://raw.githubusercontent.com/marco-taylor/nemotron-unified-rust-wyoming/main/assets/icons/nemotron-lowq.png'
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
regular_image='ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest'
assert compose['services']['nemotron-wyoming']['image']=='${IMAGE:-'+regular_image+'}'
for example in ['.env.example','config/unraid.env.example']:
    assert 'IMAGE='+regular_image in Path(example).read_text()
xml_variables={c.attrib["Target"] for c in root.findall("Config") if c.attrib.get("Type")=="Variable"}
assert xml_variables==names
assert set(compose["services"]["nemotron-wyoming"]["environment"])==names
assert all(c.attrib.get("Display")=="always" and c.attrib.get("Required")=="false" for c in root.findall("Config") if c.attrib.get("Type")=="Variable")
for example in [".env.example", "config/unraid.env.example"]:
    assert all((name+"=") in Path(example).read_text() for name in names)
assert {"SETUID","SETGID"} == set(compose["services"]["nemotron-wyoming"]["cap_add"])
assert "user" not in compose["services"]["nemotron-wyoming"]
print(f"All {len(names)} variables present in Compose, visible optional XML fields and .env example; minimal identity-bootstrap caps checked")
