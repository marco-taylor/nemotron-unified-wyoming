import io,tarfile,tempfile
from pathlib import Path
print('tarfile implementation:',tarfile.__file__)
with tempfile.TemporaryDirectory() as d:
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w') as t:
        info=tarfile.TarInfo('../escape.txt');info.size=1;t.addfile(info,io.BytesIO(b'x'))
    data.seek(0)
    try:
        with tarfile.open(fileobj=data) as t:t.extractall(d,filter='data')
    except tarfile.OutsideDestinationError:print('Path traversal correctly rejected')
    else:raise AssertionError('unsafe extraction accepted')
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w') as t:
        info=tarfile.TarInfo('safe.txt');info.size=1;t.addfile(info,io.BytesIO(b'x'))
    data.seek(0)
    with tarfile.open(fileobj=data) as t:t.extractall(d,filter='data')
    assert Path(d,'safe.txt').read_bytes()==b'x'
print('Safe extraction supported; filtering retained')
