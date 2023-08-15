import abc
from typing import Any


class StreamDataI(abc.ABC):
    '''frame based stream data'''
    def __init__(self) -> None:
        super().__init__()
    
    @abc.abstractmethod
    def init_stream(self) -> None:
        pass

    @abc.abstractmethod
    def getnframes(self) -> int:
        pass

    # return type depends on the chunks
    @abc.abstractmethod
    def readframe(self, what:Any=1):
        pass

    @abc.abstractmethod
    def tell(self) -> int:
        pass

    @abc.abstractmethod
    def setpos(self, pos:int) -> None:
        pass

    @abc.abstractmethod
    def rewind(self) -> None:
        pass

    @abc.abstractmethod
    def close(self) -> None:
        pass

class AudioStreamI(StreamDataI):
    @abc.abstractmethod
    def getsampwidth(self) -> int:
        pass

    @abc.abstractmethod
    def getnchannels(self) -> int:
        pass

    @abc.abstractmethod
    def getframerate(self) -> int:
        pass
