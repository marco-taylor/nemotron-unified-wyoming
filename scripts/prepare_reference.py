#!/usr/bin/env python3
"""Prepare the published CC0 human recording; no generated speech or ASR output."""
import audioop,hashlib,json,wave
from pathlib import Path
root=Path('benchmarks/audio')
source=root/'einsteigen-bitte.original.wav'
with wave.open(str(source),'rb') as w:
    spec={'rate':w.getframerate(),'channels':w.getnchannels(),'width':w.getsampwidth(),'frames':w.getnframes()}
    pcm=w.readframes(w.getnframes())
assert spec['channels']==1 and spec['width']==2
converted,_=audioop.ratecv(pcm,2,1,spec['rate'],16000,None)
dest=root/'einsteigen-bitte.wav'
with wave.open(str(dest),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(converted)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'id':'commons-daniel-mietchen-einsteigen-bitte','audio':'audio/einsteigen-bitte.wav',
    'sha256':sha(dest),'duration_seconds':len(converted)/32000,'speaker_group':'Daniel Mietchen',
    'reference':'Einsteigen bitte!','reference_origin':'Published transcription in Wikimedia Commons description',
    'license':'CC0-1.0','human_recording':True,'original_sha256':sha(source),
    'source_url':'https://commons.wikimedia.org/wiki/File:LL-Q188_(deu)-Daniel_Mietchen-Einsteigen_bitte!.wav',
    'preprocessing':'Python 3.11 audioop.ratecv, mono PCM16 to 16000 Hz; no trimming', 'original_format':spec}
Path('benchmarks/manifest.real.jsonl').write_text(json.dumps(record,ensure_ascii=False)+'\n')
Path('benchmarks/reference.txt').write_text(record['reference']+'\n')
Path('benchmarks/REFERENCE.md').write_text('# Human German reference recording\n\nSpeaker/recorder: Daniel Mietchen. CC0 1.0.\n\nPublished transcription: Einsteigen bitte!\n\n'+record['source_url']+'\n\nOriginal and resampled audio hashes and preprocessing are in ./benchmarks/manifest.real.jsonl (relative to project root).\nThis short two-word sample is a smoke test, not a representative German WER corpus.\n')
print(json.dumps(record,ensure_ascii=False,indent=2))
