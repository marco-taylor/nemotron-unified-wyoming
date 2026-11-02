"""Opt-in real model integration via pinned official Wyoming event classes.
No fixture transcripts: all reported text comes from the running server.
Requires an isolated test server with MAX_AUDIO_SECONDS=2; prefer scripts/test-release.sh.
Usage: PYTHONPATH=tests/reference python3 tests/real_server.py --host HOST --port PORT --wav WAV --output JSON
"""
import argparse
import json
import socket
import time
import wave
from wyoming.event import Event, read_event, write_event
from wyoming.info import Describe, Info, SelectProgram
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.error import Error

p=argparse.ArgumentParser()
p.add_argument('--host',default='127.0.0.1')
p.add_argument('--port',type=int,default=10300)
p.add_argument('--wav',required=True)
p.add_argument('--output',required=True)
p.add_argument('--chunk-ms',type=int,default=20)
p.add_argument('--max-chunk-bytes',type=int,default=320000)
a=p.parse_args()
assert 1<=a.chunk_ms<=1000
chunk_bytes=a.chunk_ms*32
records=[]
def connect():
    s=socket.create_connection((a.host,a.port),timeout=10)
    s.settimeout(90)
    return s,s.makefile('rwb',buffering=0)
def receive(f,kind):
    e=read_event(f)
    assert e is not None and e.type==kind,(kind,e)
    return e

def describe():
    s,f=connect()
    with s,f:
        write_event(Describe().event(),f)
        info=Info.from_event(receive(f,'info'))
        assert len(info.asr)==1
        program=info.asr[0]
        assert program.installed and program.requires_external_vad
        assert not program.supports_transcript_streaming
        assert program.models[0].languages==['de']
        return program.name

with wave.open(a.wav,'rb') as w:
    assert (w.getframerate(),w.getsampwidth(),w.getnchannels())==(16000,2,1)
    audio=w.readframes(w.getnframes())
    duration=w.getnframes()/16000
name=describe()
s,f=connect()
with s,f:
    write_event(SelectProgram(name=name).event(),f)
    for i in range(3):
        began=time.monotonic()
        write_event(Transcribe(language='de',name=name).event(),f)
        write_event(AudioStart(rate=16000,width=2,channels=1).event(),f)
        for pos in range(0,len(audio),chunk_bytes):
            write_event(AudioChunk(rate=16000,width=2,channels=1,audio=audio[pos:pos+chunk_bytes]).event(),f)
        write_event(AudioStop().event(),f)
        text=Transcript.from_event(receive(f,'transcript'))
        elapsed=time.monotonic()-began
        assert text.language=='de'
        records.append(dict(request=i+1,text=text.text,language=text.language,audio_seconds=duration,request_seconds=elapsed,request_rtf=elapsed/duration))
        assert text.text.strip(), 'real model returned empty transcription'
        # A separate client must remain usable while this connection is open.
        assert describe()==name
    write_event(Transcribe(language='en').event(),f)
    assert Error.from_event(receive(f,'error')).text
    write_event(Transcribe(language='de').event(),f)
    write_event(AudioStart(rate=8000,width=2,channels=1).event(),f)
    assert Error.from_event(receive(f,'error')).text
    write_event(Transcribe(language='de').event(),f)
    write_event(AudioStart(rate=16000,width=2,channels=1).event(),f)
    write_event(AudioChunk(rate=16000,width=2,channels=1,audio=b'\x01').event(),f)
    assert Error.from_event(receive(f,'error')).text
    # Test server is deliberately configured with MAX_AUDIO_SECONDS=2.
    write_event(Transcribe(language='de').event(),f)
    write_event(AudioStart(rate=16000,width=2,channels=1).event(),f)
    write_event(AudioChunk(rate=16000,width=2,channels=1,audio=b'\0'*96000).event(),f)
    assert 'duration limit' in Error.from_event(receive(f,'error')).text
    # Disconnect while an actual native session is active.
    write_event(Transcribe(language='de').event(),f)
    write_event(AudioStart(rate=16000,width=2,channels=1).event(),f)
    write_event(AudioChunk(rate=16000,width=2,channels=1,audio=audio[:640]).event(),f)
assert describe()==name
# Broken framing is rejected with a correctly framed official Error event.
s,f=connect()
with s,f:
    f.write(b'{"type":"audio-chunk","payload_length":320001}\n')
    assert Error.from_event(receive(f,'error')).code=='invalid-frame'
# Configured limit must reject immediately, without waiting for the declared payload.
s,f=connect()
with s,f:
    began=time.monotonic()
    f.write((json.dumps({'type':'audio-chunk','payload_length':a.max_chunk_bytes+2})+'\n').encode())
    error=Error.from_event(receive(f,'error'))
    assert error.code=='invalid-frame' and 'frame limit exceeded' in error.text
    assert time.monotonic()-began<3
result={'status':'passed','model':name,'records':records,'checks':['typed official info/asr/audio/error interoperability','three real requests on one connection','parallel describe','German-only validation','invalid sample rate','odd PCM payload','audio duration limit','active-session disconnect','oversized frame rejection']}
with open(a.output,'w') as out: json.dump(result,out,ensure_ascii=False,indent=2);out.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
