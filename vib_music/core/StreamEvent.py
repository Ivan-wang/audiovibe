from typing import Dict, NamedTuple
from enum import unique, auto, IntEnum

@unique
class StreamEventType(IntEnum):
    # events handled by a stream driver
    STREAM_INIT = auto()
    STREAM_NEXT_FRAME = auto()
    STREAM_CLOSE = auto()
    # event handled by a stream data
    STREAM_SEEK = auto()
    # events handled by a stream handler?
    STREAM_STATUS_ACQ = auto()
    STREAM_STATUS_ACK = auto()

class StreamEvent(NamedTuple):
    head: StreamEventType 
    what: Dict = {}
