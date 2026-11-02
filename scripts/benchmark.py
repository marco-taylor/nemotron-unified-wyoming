#!/usr/bin/env python3
"""Run in the native Docker build image. Real model required; downloads nothing."""
import argparse
import hashlib
import json
import os
import resource
import time
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--binary', default='/work/target/release/nemotron-unified-wyoming')
p.add_argument('--model', required=True)
p.add_argument('--manifest', required=True)
p.add_argument('--output', required=True)
p.add_argument('--repeats', type=int, default=3)
a = p.parse_args()
if a.repeats < 1:
    p.error('--repeats must be positive')
manifest = Path(a.manifest).resolve()
records = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
if not records:
    p.error('manifest is empty')
ids = set()
for record in records:
    if record.get('schema_example_only'):
        p.error('schema example is not a real audio corpus')
    if record['id'] in ids:
        p.error('duplicate corpus id')
    ids.add(record['id'])
    audio = (manifest.parent / record['audio']).resolve()
    if not audio.is_relative_to(manifest.parent):
        p.error('audio must stay within corpus directory')
    if hashlib.file_digest(audio.open('rb'), 'sha256').hexdigest() != record['sha256']:
        p.error('audio hash mismatch: ' + str(audio))
    record['_path'] = str(audio)
output = Path(a.output)
output.parent.mkdir(parents=True, exist_ok=True)
# Exclusive creation: preserve previous measurements.
with output.open('x') as dest, tempfile.TemporaryDirectory() as temp:
    for repeat in range(a.repeats):
        # Rotate thread order to reduce systematic thermal ordering bias.
        threads = [1, 2, 4]
        threads = threads[repeat % 3:] + threads[:repeat % 3]
        for thread in threads:
            for paced in [False, True]:
                for record in records:
                    reference = Path(temp) / 'reference.txt'
                    reference.write_text(record['reference'], encoding='utf-8')
                    command = [a.binary, 'benchmark', '--model', a.model, '--threads', str(thread), '--wav', record['_path'], '--reference', str(reference)]
                    if paced:
                        command.append('--paced')
                    env = dict(os.environ, OMP_NUM_THREADS=str(thread), OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
                    before_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
                    process_start = time.monotonic()
                    try:
                        completed = subprocess.run(command, env=env, text=True, capture_output=True, timeout=1800)
                    except subprocess.TimeoutExpired as error:
                        result = {'id':record['id'],'repeat':repeat,'threads':thread,'paced':paced,'status':'error','error':'timeout','stderr':str(error)}
                        dest.write(json.dumps(result, ensure_ascii=False)+'\n')
                        dest.flush()
                        continue
                    if completed.returncode:
                        result = {'id':record['id'],'repeat':repeat,'threads':thread,'paced':paced,'status':'error','stderr':completed.stderr,'returncode':completed.returncode}
                    else:
                        result = json.loads(completed.stdout)
                        result.update(id=record['id'],repeat=repeat,status='ok',speaker_group=record.get('speaker_group'),stderr=completed.stderr)
                        expected_duration = record.get('duration_seconds')
                        if expected_duration is not None and abs(result['audio_seconds']-expected_duration)>1/16000:
                            result.update(status='error', error='manifest duration mismatch')
                    after_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
                    wall = time.monotonic() - process_start
                    user = after_cpu.ru_utime - before_cpu.ru_utime
                    system = after_cpu.ru_stime - before_cpu.ru_stime
                    result.update(process_wall_seconds=wall, process_cpu_user_seconds=user,
                                  process_cpu_system_seconds=system,
                                  process_cpu_percent_one_core_100=100*(user+system)/wall,
                                  process_cpu_scope='whole subprocess including load, warmup, inference and hashes; not inference-only')
                    dest.write(json.dumps(result, ensure_ascii=False)+'\n')
                    dest.flush()
                    print(json.dumps({'id':record['id'],'threads':thread,'paced':paced,'repeat':repeat,'status':result['status']}),flush=True)
# Raw paired per-utterance values retained. Corpus WER uses summed counts.
rows = [json.loads(line) for line in output.read_text().splitlines()]
summary = []
for thread in [1,2,4]:
    for paced in [False,True]:
        group=[r for r in rows if r['threads']==thread and r['paced']==paced and r['status']=='ok']
        if not group:
            continue
        words=sum(r['reference_words'] for r in group)
        def percentile(key, q):
            v=sorted(r[key] for r in group if r.get(key) is not None)
            return v[min(len(v)-1, int((len(v)-1)*q+0.5))] if v else None
        summary.append({'threads':thread,'paced':paced,'runs':len(group),'corpus_wer':sum(r['word_errors'] for r in group)/words if words else None,
            'rtf_audio_weighted':sum(r['compute_seconds'] for r in group)/sum(r['audio_seconds'] for r in group),
            'first_partial_p50_ms':percentile('first_partial_from_start_ms',.5),'first_partial_p95_ms':percentile('first_partial_from_start_ms',.95),
            'final_after_stop_p50_ms':percentile('final_after_audio_stop_ms',.5),'final_after_stop_p95_ms':percentile('final_after_audio_stop_ms',.95),
            'max_peak_rss_bytes':max((r['peak_rss_bytes'] for r in group if r['peak_rss_bytes'] is not None), default=None)})
with output.with_suffix('.summary.json').open('x') as f:
    json.dump({'normalizer':'NFC-lower-alnum-spaces-v1','failed_runs':sum(r['status']!='ok' for r in rows),'groups':summary},f,indent=2)
