import abc
import numpy as np
from typing import Any, Optional
from .message import Message, MessageT

class VibrationDriverBase(abc.ABC):
    def __init__(self) -> None:
        super(VibrationDriverBase, self).__init__()

        self.handlers = {
            MessageT.MSG_STREAM_RESET: self.on_start,
            MessageT.MSG_STREAM_PULSE: self.on_pulse,
            MessageT.MSG_STREAM_RESUME: self.on_resume,
            MessageT.MSG_STREAM_STOP: self.on_close,
            MessageT.MSG_STREAM_DATA: self.on_receive_frame,

            MessageT.MSG_STATUS_ACQ: self.on_status_acq,
        }
    
    @abc.abstractmethod
    def on_status_acq(self, what:Any=None) -> Message:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_start(self, what:Any=None) -> Message:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def on_pulse(self, what:Any=None) -> Message:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def on_resume(self, what:Any=None) -> Message:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def on_receive_frame(self, what:Optional[np.ndarray]=None) -> Message:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def on_close(self, what:Any=None) -> Message:
        raise NotImplementedError()
    
    def on_receive_message(self, msg:Message) -> Message:
        return self.handlers[msg.header](msg.what)

from .env import ADC_ENV_READY
if ADC_ENV_READY:
    import smbus

# NOTE: each sample accept at most 8 operations
import numpy as np
class PCF8591Driver(VibrationDriverBase):
    def __init__(self) -> None:
        super(PCF8591Driver, self).__init__()

    def on_start(self, what:Any=None) -> Message:
        if ADC_ENV_READY:
            self.device = smbus.SMBus(1)
            return Message(header=MessageT.MSG_FLAG_SUCCESS)
        else:
            return Message(header=MessageT.MSG_FLAG_ERROR)

    def on_receive_frame(self, what:Optional[np.ndarray]=None) -> Message:
        for a in what:
            try:
                self.device.write_byte_data(0x48, 0x40, a)
            except:
                return Message(header=MessageT.MSG_FLAG_ERROR)
        return Message(header=MessageT.MSG_STREAM_ACQ)

    def on_close(self, what:Any=None) -> Message:
        # close the device?
        return Message(header=MessageT.MSG_FLAG_SUCCESS)

    def on_pulse(self, what:Any=None) -> Message:
        return Message(header=MessageT.MSG_FLAG_SUCCESS)
    
    def on_resume(self, what:Any=None) -> Message:
        return Message(header=MessageT.MSG_FLAG_SUCCESS)
    
    def on_status_acq(self, what:Any=None) -> Message:
        return Message(header=MessageT.MSG_STATUS_ACK)
