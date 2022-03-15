import abc
import numpy as np
from typing import Any, Optional
from .Message import Message, MessageT

class StreamError(Exception):
    pass

class AudioStreamError(StreamError):
    pass

class VibrationStreamError(StreamError):
    pass

class StreamDriverBase(abc.ABC):
    def __init__(self) -> None:
        super(StreamDriverBase, self).__init__()
        self.stream = None
        self._is_activate = False

        # stream handlers
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
    
    @property
    def is_activate(self) -> bool:
        # there is no setter for "is_activate"
        return self._is_activate

