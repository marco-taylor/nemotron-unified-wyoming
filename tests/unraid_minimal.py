"""Real L37 smoke test with defaults; requires only a separately provisioned test server."""
import argparse
import json
import re
import socket
import wave
from pathlib import Path
from wyoming.event import Event, read_event, write_event

p = argparse.ArgumentParser()
p.add_argument('--port',type=int,default=10300)
p.add_argument('--output',required=True)
p.add_argument('--max-audio-chunk-bytes',type=int,default=320000)
p.add_argument('--chunk-ms',type=int,default=20)
a = p.parse_args()
assert 1 <= a.chunk_ms <= 1000
with wave.open('/project/benchmarks/audio/einsteigen-bitte.wav','rb') as w:
    assert (w.getframerate(),w.getsampwidth(),w.getnchannels()) == (16000,2,1)
    pcm = w.readframes(w.getnframes())
s = socket.create_connection(('127.0.0.1',a.port),timeout=10)
s.settimeout(90)
f = s.makefile('rwb',buffering=0)
def receive(kind):
    e = read_event(f)
    assert e is not None and e.type == kind, e
    return e
write_event(Event(type='describe'),f)
info=receive('info').data
assert info['asr'][0]['models'][0]['languages'] == ['de']
assert not info['asr'][0]['supports_transcript_streaming']
texts=[]
for i in range(3):
    write_event(Event(type='transcribe',data={'language':'de'}),f)
    write_event(Event(type='audio-start',data={'rate':16000,'width':2,'channels':1}),f)
    chunk_bytes=a.chunk_ms*32
    for pos in range(0,len(pcm),chunk_bytes):
        write_event(Event(type='audio-chunk',data={'rate':16000,'width':2,'channels':1},payload=pcm[pos:pos+chunk_bytes]),f)
    write_event(Event(type='audio-stop'),f)
    transcript=receive('transcript').data
    assert transcript['language'] == 'de'
    assert re.findall(r'\w+',transcript['text'].lower()) == ['einsteigen','bitte']
    texts.append(transcript['text'])
# The omitted MAX_AUDIO_CHUNK_BYTES must retain the 320000-byte frame limit.
f.write((json.dumps({'type':'audio-chunk','payload_length':a.max_audio_chunk_bytes+2})+'\n').encode())
error=receive('error')
assert 'frame limit exceeded' in error.data['text']
f.close()
s.close()
Path(a.output).write_text(json.dumps({'status':'passed','texts':texts,'language':'de','oversize_limit':a.max_audio_chunk_bytes},ensure_ascii=False,indent=2)+'\n')
print('Real L37 transcription, Wyoming and selected payload limit passed')
