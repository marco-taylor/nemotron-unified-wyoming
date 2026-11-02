import json,tarfile
from pathlib import Path
archive=Path('export/downloads/nemo-43dd97ddf.tar.gz')
dest=Path('export/source');dest.mkdir(exist_ok=True)
with tarfile.open(archive) as t:
    members=t.getmembers();total=sum(m.size for m in members)
    assert total<1024**3,'unexpectedly large extracted source'
    base=dest.resolve()
    skipped=[]
    for m in members:
        target=(base/m.name).resolve()
        assert target.is_relative_to(base), 'archive path escapes project directory'
        if m.isdir():target.mkdir(parents=True,exist_ok=True)
        elif m.isfile():
            target.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(m) as src, target.open('wb') as dst:
                import shutil
                shutil.copyfileobj(src,dst)
        else:skipped.append(m.name)
    print('Skipped non-regular source entries:',skipped)
report={'archive_bytes':archive.stat().st_size,'extracted_logical_bytes':total,'entries':len(members)}
Path('export/reports/nemo-source-size.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
