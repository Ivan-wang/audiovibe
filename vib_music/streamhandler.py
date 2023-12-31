from enum import IntEnum, unique, auto
from typing import Optional, NamedTuple, Dict, Any, Callable
from tqdm import tqdm
from vib_music.core import StreamEvent

from .core import AudioStreamI, StreamDriverBase, StreamDataI
from .core import StreamEvent, StreamEventType
from .drivers import AudioDriver

class StreamEndException(Exception):
    pass

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
    what: Dict = {}

@unique
class StreamState(IntEnum):
    STREAM_INACTIVE = auto()
    STREAM_ACTIVE = auto()

class StreamHandler(object):
    def __init__(self, stream_data:StreamDataI, stream_driver:StreamDriverBase) -> None:
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
    
    def on_init(self, what:Optional[Dict]=None) -> None:
        self.stream_data.init_stream()
        self.stream_driver.on_init(what)
        self.stream_state = StreamState.STREAM_ACTIVE
    
    def on_seek(self, what:Optional[Dict]=None) -> None:
        self.stream_data.setpos(what['pos'])

    def on_next_frame(self, what:Optional[Dict]=None) -> None:
        if not self.is_activate():
            return

        if what is not None and 'frame' in what:
            frame = what.get('frame', None)
        else:
            frame = self.stream_data.readframe()
        if frame is None or len(frame) == 0:
            raise StreamEndException('no more frames')
        self.stream_driver.on_next_frame({'frame': frame})
    
    def on_close(self, what:Optional[Dict]=None) -> None:
        self.stream_state = StreamState.STREAM_INACTIVE
        self.stream_driver.on_close(what)
        self.stream_data.close()
    
    def on_status_acq(self, what:Optional[Dict]=None) -> StreamEvent:
        return self.stream_driver.on_status_acq(what)
    
    def handle(self, event:StreamEvent) -> Optional[StreamEvent]:
        if event.head in self.control_handle_funcs:
            return self.control_handle_funcs[event.head](event.what)
    
    def is_activate(self) -> bool:
        return self.stream_state == StreamState.STREAM_ACTIVE
    
    def tell(self) -> int:
        return self.stream_data.tell()
    
    def num_frame(self) -> int:
        return self.stream_data.getnframes()

class AudioStreamHandler(StreamHandler):
    def __init__(self, stream_data: AudioStreamI, stream_driver: AudioDriver) -> None:
        super(AudioStreamHandler, self).__init__(stream_data, stream_driver)

        self.control_handle_funcs.update({
            AudioStreamEventType.AUDIO_PULSE: self.on_pulse,
            AudioStreamEventType.AUDIO_RESUME: self.on_resume,
            AudioStreamEventType.AUDIO_START: self.on_start,
        })

        self.enable_bar = True
        self.bar = None

    def disable_bar(self) -> None:
        self.enable_bar = False
    
    def on_init(self, what:Optional[Dict]=None) -> StreamEvent:
        # override
        self.stream_data.init_stream()
        what = {} if what is None else what
        what.setdefault('format', self.stream_data.getsampwidth())
        what.setdefault('channels', self.stream_data.getnchannels())
        what.setdefault('rate', self.stream_data.getframerate())

        self.stream_driver.on_init(what)
        num_frame = self.stream_data.getnframes()
        if self.enable_bar:
            self.bar = tqdm(desc='[audio]', unit=' frame', total=num_frame)

        self.stream_state = StreamState.STREAM_INACTIVE # audio waits for start signal

        return StreamEvent(StreamEventType.STREAM_STATUS_ACK, what={'num_frame': num_frame})

    def on_start(self, what:Optional[Dict]=None) -> None:
        self.stream_state = StreamState.STREAM_ACTIVE

    def on_pulse(self, what:Optional[Dict]=None) -> None:
        self.stream_state = StreamState.STREAM_INACTIVE
        self.stream_driver.on_pulse(what)
    
    def on_resume(self, what:Optional[Dict]=None) -> None:
        self.stream_state = StreamState.STREAM_ACTIVE
        self.stream_driver.on_resume(what)
    
    def on_seek(self, what: Optional[Dict] = None) -> None:
        if self.bar is not None:
            self.bar.n = what['pos']
            self.bar.last_print_n = what['pos']
            self.bar.refresh()
        return super().on_seek(what)

    def on_next_frame(self, what: Optional[Dict] = None) -> None:
        try:
            super(AudioStreamHandler, self).on_next_frame(what)
        except StreamEndException as e:
            raise e
        else:
            if self.bar is not None: self.bar.update()
   
    def on_close(self, what: Optional[Dict] = None) -> None:
        if self.bar is not None: self.bar.close()
        return super().on_close(what)

class LiveStreamHandler(StreamHandler):
    def __init__(self, live_data_stream:StreamDataI, stream_driver:StreamDriverBase) -> None:
        super(LiveStreamHandler, self).__init__(live_data_stream, stream_driver)
    
    def on_next_frame(self, what:Optional[Dict]=None) -> None:
        if not self.is_activate():
            return
        
        frame = what.get('frame', None)
        if frame is None:
            raise StreamEndException('no more frames')
        else:
            frame = self.stream_data.readframe(frame)
        
        if frame is not None:
            self.stream_driver.on_next_frame(frame)
    