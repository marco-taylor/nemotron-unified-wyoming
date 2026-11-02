import io
import sys
from wyoming.event import Event, read_event, write_event

expected = [Event(type="transcribe", data={"language":"de"}),
            Event(type="audio-start", data={"rate":16000,"width":2,"channels":1}),
            Event(type="audio-chunk", data={"rate":16000,"width":2,"channels":1}, payload=b"\x00\x80\xff\x7f\x0a\x00"),
            Event(type="audio-stop"),
            Event(type="transcript", data={"text":"Öffne die Tür.","language":"de"})]
if sys.argv[1] == "read-info":
    from wyoming.info import Info
    from wyoming.error import Error
    info = Info.from_event(read_event(sys.stdin.buffer))
    assert len(info.asr) == 1
    assert info.asr[0].installed
    assert info.asr[0].requires_external_vad
    assert not info.asr[0].supports_transcript_streaming
    assert info.asr[0].models[0].languages == ["de"]
    assert Error.from_event(read_event(sys.stdin.buffer)).text == "test-only error"
    assert read_event(sys.stdin.buffer) is None
elif sys.argv[1] == "write":
    for event in expected:
        write_event(event, sys.stdout.buffer)
else:
    for event in expected:
        actual = read_event(sys.stdin.buffer)
        assert actual is not None
        assert actual.type == event.type
        assert actual.data == event.data
        assert (actual.payload or b"") == (event.payload or b"")
    assert read_event(sys.stdin.buffer) is None
