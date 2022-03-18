from enum import IntEnum, unique, auto
from typing import Optional, NamedTuple, Dict

from .core import StreamDataBase, StreamDriverBase
from .core import StreamEvent, StreamEventType
from .core import StreamError
from .drivers import AudioDriver
from .streams import WaveAudioStream

@unique
class AudioStreamEventType(IntEnum):
    # events handled by a stream driver
    STREAM_INIT = StreamEventType.STREAM_INIT
    STREAM_NEXT_FRAME = StreamEventType.STREAM_NEXT_FRAME
    STREAM_CLOSE = StreamEventType.STREAM_CLOSE
    # event handled by a stream data
    STREAM_SEEK = StreamEventType.STREAM_SEEK
    # events handled by a stream handler?
    STREAM_STATUS_ACQ = StreamEventType.STREAM_STATUS_ACQ
    STREAM_STATUS_ACK = StreamEventType.STREAM_STATUS_ACK

    AUDIO_START = auto()
    AUDIO_PULSE = auto()
    AUDIO_RESUME = auto()

class AudioStreamEvent(NamedTuple):
    head: AudioStreamEventType
    what: Dict

@unique
class StreamState(IntEnum):
    STREAM_INACTIVE = auto()
    STREAM_ACTIVE = auto()

class StreamHandler(object):
    def __init__(self, stream_data:StreamDataBase, stream_driver:StreamDriverBase) -> None:
        super(StreamHandler).__init__()

        self.stream_data = stream_data # inputs
        self.stream_driver = stream_driver # outputs
        self.stream_state = StreamState.STREAM_INACTIVE

        self.control_handle_funcs = {
            StreamEventType.STREAM_NEXT_FRAME: self.on_next_frame,
            StreamEventType.STREAM_INIT: self.on_init,
            StreamEventType.STREAM_SEEK: self.on_seek,
            # MessageT.MSG_STREAM_PULSE: self.on_pulse,
            StreamEventType.STREAM_CLOSE: self.on_close
        }
    
    def on_init(self) -> None:
        self.stream_driver.on_init()
        self.stream_data.rewind()
        self.stream_state = StreamState.STREAM_ACTIVE
    
    def on_seek(self, pos:int) -> None:
        self.stream_data.setpos(pos)

    def on_next_frame(self) -> None:
        if self.stream_state is not StreamState.STREAM_INACTIVE:
            return
        frame = self.stream_data.readframe()
        if len(frame) == 0:
            raise StreamError()
        self.stream_driver.on_next_frame(
            StreamEvent(StreamEventType.STREAM_NEXT_FRAME, {'frame': frame})
        )
    
    def on_close(self) -> None:
        self.stream_state = StreamState.STREAM_INACTIVE
        self.stream_driver.on_close()
        self.stream_data.close()
    
    def on_status_acq(self) -> StreamEvent:
        return self.stream_driver.on_status_acq()
    
    def handle(self, event:StreamEvent) -> Optional[StreamEvent]:
        return self.control_handle_funcs[event.head](event.what)

@unique
class AudioStreamState(IntEnum):
    STREAM_ACTIVATE = StreamState.STREAM_ACTIVE
    STREAM_INACTIVATE = StreamState.STREAM_INACTIVE

    AUDIO_RUNNING = auto()
    AUDIO_PULSE = auto()

class AudioStreamHandler(StreamHandler):
    def __init__(self, stream_data: WaveAudioStream, stream_driver: AudioDriver) -> None:
        super(AudioStreamHandler, self).__init__(stream_data, stream_driver)

        self.control_handle_funcs.update({
            AudioStreamEventType.AUDIO_PULSE: self.on_pulse,
            AudioStreamEventType.AUDIO_RESUME: self.on_resume,
            AudioStreamEventType.AUDIO_START: self.on_start,
        })
    
    def on_init(self) -> None:
        super(AudioStreamHandler, self).on_init()
        self.stream_state = AudioStreamState.STREAM_INACTIVE # audio waits for start signal

    def on_start(self) -> None:
        self.stream_state = AudioStreamState.STREAM_ACTIVE

    def on_pulse(self) -> None:
        self.stream_state = AudioStreamState.STREAM_INACTIVE
        self.stream_driver.on_pulse()
    
    def on_resume(self) -> None:
        self.stream_state = AudioStreamState.STREAM_ACTIVE
        self.stream_driver.on_resume()

