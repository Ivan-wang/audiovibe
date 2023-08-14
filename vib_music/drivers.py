import time
import logging
from typing import Optional, Dict

from vib_music.core.StreamEvent import StreamEvent

from .core import StreamEvent, StreamEventType
from .core import StreamDriverBase, StreamError

class LogDriver(StreamDriverBase):
    def __init__(self) -> None:
        super(LogDriver, self).__init__()
        self.stream = None
        self.use_logger = True
    
    def on_init(self, what:Optional[Dict]=None) -> None:
        self.stream = logging.getLogger('LogDriver')
        self.stream.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        self.stream.addHandler(ch)

        self.stream.info('LogDriver Handler Initialized!')

    def on_next_frame(self, what: Optional[Dict] = None) -> None:
        self.stream.info('LogDriver Move On Next Frame!')
    
    def on_pulse(self, what: Optional[Dict] = None) -> None:
        self.stream.info('LogDriver Pulsed!')
    
    def on_resume(self, what: Optional[Dict] = None) -> None:
        self.stream.info('LogDriver Resumed!')
    
    def on_status_acq(self, what: Optional[Dict] = None) -> Optional[StreamEvent]:
        self.stream.info('LogDriver Receives Status Req!')
        return StreamEvent(StreamEventType.STREAM_STATUS_ACK, {'status': 'LogDriver'})
    
    
    def on_close(self, what: Optional[Dict] = None) -> None:
        self.stream.info('LogDriver Is Closing...')
        handlers = self.stream.handlers[:]
        for h in handlers:
            self.stream.removeHandler(h)
            h.close()
        logging.shutdown()

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
        return StreamEvent(head=StreamEventType.STREAM_STATUS_ACK, what={'status': 'Music Stream'})
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

import serial
class UARTDriver(StreamDriverBase):
    CHANNEL_MAP = {'Z': 0b01, '0': 0b00, '1': 0b10}
    def __init__(self) -> None:
        super(UARTDriver, self).__init__()
        self.stream = None
        self.last_cmd = None
        self.last_feedback = None
    
    def on_init(self, what: Optional[Dict] = None) -> None:
        self.stream = serial.Serial('/dev/ttyS0', 115200, timeout=0.01)
        # send init signals?
    
    def on_next_frame(self, what: Optional[Dict] = None) -> None:
        if what is None:
            return

        CH0, CH1, CH2, CH3 = what.get('CH', '1 0 Z Z').split(' ')
        channel_control = 0
        for c in [CH3, CH2, CH1, CH0]:
            channel_control = (channel_control << 2) | self.CHANNEL_MAP[c]

        volt = what.get('voltage', 180)
        freq = what.get('freq', 1000)
        duty = what.get('duty', 50)

        self.last_cmd = f'BC01{channel_control:02X}{int(volt):02X}{duty*2+1:02X}{int(freq):04X}AFAAFFDF'
        bytes = bytearray.fromhex(self.last_cmd)
        self.stream.write(bytes)
        time.sleep(0.1)
        self.last_feedback = self.stream.read(7) # collect feed back
    
    def on_close(self, what: Optional[Dict] = None) -> None:
        self.stream.write(bytearray.fromhex('BC0100000000000000FFFFFFDF'))
        self.stream.close()
    
    def _translate_current(self, current:bytearray) -> str:
        return ' '.join([f'{int(x)/255*16:.2f}' for x in bytes[1:5]])
    
    def on_status_acq(self, what: Optional[Dict] = None) -> Optional[StreamEvent]:
        if self.last_cmd is None:
            return StreamEvent(StreamEventType.STREAM_STATUS_ACK, {})

        # need to repeat last command to get feed back
        self.stream.write(bytearray.fromhex(self.last_cmd))
        time.sleep(0.1)
        try:
            feedback = self.stream.read(7) # read a feed back
            current = self._translate_current(feedback)
        except Exception:
            return StreamEvent(StreamEventType.STREAM_STATUS_ACK, {'current': self._translate_current(self.last_feedback)})
        else:
            self.last_feedback = feedback
            return StreamEvent(StreamEventType.STREAM_STATUS_ACK, {'current': current})