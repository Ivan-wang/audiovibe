from typing import NamedTuple, Optional
from enum import unique, auto, Enum
import numpy as np


@unique
class MessageT(Enum):
    MSG_RESERVED = auto()
    # stream control
    MSG_FLAG_ERROR = auto()
    MSG_FLAG_SUCCESS = auto()
    # stream control
    MSG_STREAM_ACQ = auto()
    MSG_STREAM_RESET = auto()
    MSG_STREAM_PULSE = auto()
    MSG_STREAM_RESUME = auto()
    MSG_STREAM_SEEK = auto()
    MSG_STREAM_STOP = auto()
    MSG_STREAM_DATA = auto()
    # IO control
    # device status
    MSG_STATUS_ACQ = auto()
    MSG_STATUS_ACK = auto()


class Message(NamedTuple):
    header: MessageT
    what: Optional[np.ndarray] = None
