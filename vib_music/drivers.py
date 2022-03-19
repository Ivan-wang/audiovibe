from typing import Optional, Dict

from .core import StreamEvent, StreamEventType
from .core import StreamDriverBase, StreamError

class AudioDriver(StreamDriverBase):
    def __init__(self) -> None:
        super(AudioDriver, self).__init__()

        self.audio = None # PyAudio object
        self.stream = None
    
    def on_init(self, what: Dict) -> None:
        from .dependency import PyAudio
        self.audio = PyAudio()
        self.stream = self.audio.open(
            format=self.audio.get_format_from_width(what['format']),
            channels=what['channels'],
            rate = what['rate'],
            output=True
        )
    
    def on_close(self, what: Optional[Dict] = None) -> None:
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
    
    def on_pulse(self, what:Optional[Dict]=None) -> None:
        self.stream.stop_stream()

    def on_resume(self, what:Optional[Dict]=None) -> None:
        self.stream.start_stream()

    def on_next_frame(self, what: Optional[Dict] = None) -> None:
        if what is not None:
            try:
                self.stream.write(what['frame'])
            except:
                raise
    
    # TODO: report audio hardware status?
    def on_status_acq(self, what: Optional[Dict] = None) -> Optional[StreamEvent]:
        return None

class PCF8591Driver(StreamDriverBase):
    def __init__(self) -> None:
        super(PCF8591Driver, self).__init__()
        self.stream = None

    def on_init(self, what: Optional[Dict] = None) -> None:
        from .dependency import smbus
        self.stream = smbus.SMBus(1)
        # raise StreamError('Init PCF8591 failed. SMBus not installed.')

    def on_next_frame(self, what: Optional[Dict] = None) -> None:
        for a in what['frame']:
            self.stream.write_byte_data(0x48, 0x40, a)

    def on_close(self, what: Optional[Dict] = None) -> None:
        # close the device?
        return

    # TODO: return vibration hardware status
    def on_status_acq(self, what: Optional[Dict] = None) -> Optional[StreamEvent]:
        return StreamEvent(StreamEventType.STREAM_STATUS_ACK, {'status': 'PCF8591'})


class PWMDriver(StreamDriverBase):
    pass
