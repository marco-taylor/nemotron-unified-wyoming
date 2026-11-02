"""Keep idle/partial-header and real native-session sockets open until SIGTERM."""
import json
import socket
import sys
from pathlib import Path
from wyoming.event import read_event,write_event
from wyoming.asr import Transcribe
from wyoming.audio import AudioStart,AudioChunk
from wyoming.info import Describe

ready,output=sys.argv[1:3]
port=int(sys.argv[3]) if len(sys.argv)>3 else 10300
sockets=[]
files=[]
try:
    for _ in range(2):
        s=socket.create_connection(('127.0.0.1',port),timeout=10)
        s.settimeout(15)
        sockets.append(s)
        files.append(s.makefile('rwb',buffering=0))
    files[0].write(b'{"type":')
    write_event(Transcribe(language='de').event(),files[1])
    write_event(AudioStart(rate=16000,width=2,channels=1).event(),files[1])
    write_event(AudioChunk(rate=16000,width=2,channels=1,audio=b'\0'*640).event(),files[1])
    write_event(Describe().event(),files[1])
    assert read_event(files[1]).type=='info'
    Path(ready).write_text('ready\n')
    for f in files:
        assert read_event(f) is None, 'shutdown must close the connection, not fabricate a transcript'
    Path(output).write_text(json.dumps({'status':'passed','checks':['partial-header connection closed','active native session connection closed'],'transcripts_emitted':0},indent=2)+'\n')
finally:
    for f in files: f.close()
    for s in sockets: s.close()
