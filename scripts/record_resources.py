import datetime,json,shutil,subprocess,sys
from pathlib import Path
sizes={}
for name in ['models','export','benchmarks']:
    sizes[name]=int(subprocess.check_output(['du','-sb',name],text=True).split()[0])
mem={line.split(':')[0]:line.split(':')[1].strip() for line in Path('/proc/meminfo').read_text().splitlines()}
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':sys.argv[1],
   'logical_directory_bytes':sizes,'free_disk_bytes':shutil.disk_usage('.').free,
   'mem_available':mem['MemAvailable'],'mem_free':mem['MemFree']}
with Path('docs/evidence/phase4-resource-history.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
print(json.dumps(r))
