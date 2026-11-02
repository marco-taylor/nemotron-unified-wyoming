"""Collect actual build dependency license texts; runs only inside the builder."""
import json
import pathlib
import shutil
import subprocess

out = pathlib.Path('/work/runtime-licenses')
out.mkdir(exist_ok=True)
metadata = json.loads(subprocess.check_output(['cargo','metadata','--locked','--offline','--format-version','1','--filter-platform','x86_64-unknown-linux-gnu']))
manifest = []
for package in metadata['packages']:
    manifest.append({key:package.get(key) for key in ['name','version','license','source','repository']})
    root = pathlib.Path(package['manifest_path']).parent
    dest = out / 'rust' / (package['name']+'-'+package['version'])
    for pattern in ['LICENSE*','LICENCE*','COPYING*','NOTICE*']:
        for source in root.glob(pattern):
            if source.is_file():
                dest.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,dest/source.name)
(out/'rust-dependencies.json').write_text(json.dumps(manifest,indent=2)+'\n')
roots = [pathlib.Path('/opt/sherpa/src')] + list(pathlib.Path('/opt/sherpa/build/_deps').glob('*-src'))
for root in roots:
    for pattern in ['LICENSE*','COPYING*','NOTICE*','*ThirdPartyNotices*']:
        for source in root.glob(pattern):
            dest = out/'native'/root.name/source.name
            dest.parent.mkdir(parents=True,exist_ok=True)
            if source.is_dir(): shutil.copytree(source,dest,dirs_exist_ok=True)
            elif source.is_file(): shutil.copy2(source,dest)
for name in ['LICENSE','THIRD_PARTY_NOTICES.md']:
    shutil.copy2('/work/'+name,out/name)
