import abc
from typing import Dict, Optional

from .StreamEvent import StreamEventType, StreamEvent

class StreamError(Exception):
    pass

class StreamDriverBase(abc.ABC):
    def __init__(self) -> None:
        super(StreamDriverBase, self).__init__()
        self.stream = None

        # stream handlers
        self.handlers = {
            StreamEventType.STREAM_INIT: self.on_init,
            StreamEventType.STREAM_NEXT_FRAME:self.on_next_frame,
            StreamEventType.STREAM_CLOSE: self.on_close,

            StreamEventType.STREAM_STATUS_ACQ: self.on_status_acq,
        }
    
    @abc.abstractmethod
    def on_status_acq(self, what:Optional[Dict]=None) -> Optional[StreamEvent]:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_init(self, what:Optional[Dict]=None) -> None:
        raise NotImplementedError()
    
    # @abc.abstractmethod
    def on_pulse(self, what:Optional[Dict]=None) -> None:
        raise NotImplementedError()
    
    # @abc.abstractmethod
    def on_resume(self, what:Optional[Dict]=None) -> None:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def on_next_frame(self, what:Optional[Dict]=None) -> None:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def on_close(self, what:Optional[Dict]=None) -> None:
        raise NotImplementedError()
    
    def on_event(self, event:StreamEvent) -> Optional[StreamEvent]:
        return self.handlers[event.header](event.what)
    