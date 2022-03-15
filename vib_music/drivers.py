import numpy as np
from typing import Any, Optional
from .core import Message, MessageT
from .core import StreamDriverBase

from .env import AUDIO_RUNTIME_READY
if AUDIO_RUNTIME_READY:
    from pyaudio import PyAudio

class AudioDriver(StreamDriverBase):
    def __init__(self) -> None:
        super(AudioDriver, self).__init__()

        self.audio = None
        self.stream = None
    
    def on_start(self, what: Any = None) -> Message:
        self.audio = PyAudio()
        try:
            self.stream = self.audio.open(
                format=self.audio.get_format_from_width(what['samplewidth']),
                channels=what['channels'],
                rate = what['rate'],
                output=True
            )
        except:
            return Message(header=MessageT.MSG_FLAG_ERROR)
        else:
            self.is_activate = True
            return Message(header=MessageT.MSG_FLAG_SUCCESS)
    
    def on_close(self, what: Any = None) -> Message:
        try:
            self.is_activate = False
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
        except:
            return Message(header=MessageT.MSG_FLAG_ERROR)
        else:
            return Message(header=MessageT.MSG_FLAG_SUCCESS)

    def on_pulse(self, what: Any = None) -> Message:
        try:
            self.is_activate = False
            self.stream.stop_stream()
        except:
            return Message(MessageT.MSG_FLAG_ERROR)
        else:
            return Message(MessageT.MSG_FLAG_SUCCESS)
    
    def on_resume(self, what: Any = None) -> Message:
        try:
            self.is_activate = True
            self.stream.start_stream()
        except:
            return Message(MessageT.MSG_FLAG_ERROR)
        else:
            return Message(MessageT.MSG_FLAG_SUCCESS)
    
    def on_receive_frame(self, what: Optional[np.ndarray] = None) -> Message:
        if what is not None:
            try:
                self.stream.write(what)
            except:
                return Message(MessageT.MSG_FLAG_ERROR)
            else:
                return Message(MessageT.MSG_FLAG_SUCCESS)
        else:
            return Message(MessageT.MSG_FLAG_SUCCESS)
    
    # TODO: return audio hardware status
    def on_status_acq(self, what: Any = None) -> Message:
        return Message(MessageT.MSG_STATUS_ACK)


from .env import ADC_ENV_READY
if ADC_ENV_READY:
    import smbus

# NOTE: each sample accept at most 8 operations
import numpy as np
class PCF8591Driver(StreamDriverBase):
    def __init__(self) -> None:
        super(PCF8591Driver, self).__init__()
        self.stream = None

    def on_start(self, what:Any=None) -> Message:
        if ADC_ENV_READY:
            try:
                self.stream = smbus.SMBus(1)
            except:
                return Message(header=MessageT.MSG_FLAG_ERROR)
            else:
                self.is_activate = True
                return Message(header=MessageT.MSG_FLAG_SUCCESS)
        else:
            return Message(header=MessageT.MSG_FLAG_ERROR)

    def on_receive_frame(self, what:Optional[np.ndarray]=None) -> Message:
        for a in what:
            try:
                self.stream.write_byte_data(0x48, 0x40, a)
            except:
                return Message(header=MessageT.MSG_FLAG_ERROR)
        return Message(header=MessageT.MSG_STREAM_ACQ)

    def on_close(self, what:Any=None) -> Message:
        # close the device?
        self.is_activate = False
        return Message(header=MessageT.MSG_FLAG_SUCCESS)

    def on_pulse(self, what:Any=None) -> Message:
        self.is_activate = False
        return Message(header=MessageT.MSG_FLAG_SUCCESS)
    
    def on_resume(self, what:Any=None) -> Message:
        self.is_activate = True
        return Message(header=MessageT.MSG_FLAG_SUCCESS)
    
    # TODO: return vibration hardware status
    def on_status_acq(self, what:Any=None) -> Message:
        return Message(header=MessageT.MSG_STATUS_ACK)
