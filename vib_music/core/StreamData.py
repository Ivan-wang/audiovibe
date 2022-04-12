import abc


class StreamDataBase(abc.ABC):
    '''frame based stream data'''
    def __init__(self, chunks, len_frame:int) -> None:
        self.chunks = chunks
        self.len_frame = len_frame
    
    def getchunks(self):
        return self.chunks

    @abc.abstractmethod
    def init_stream(self) -> None:
        self.rewind()

    @abc.abstractmethod
    def getnframes(self) -> int:
        pass

    # return type depends on the chunks
    @abc.abstractmethod
    def readframe(self, n:int=1):
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

class AudioStream(StreamDataBase):
    @abc.abstractmethod
    def getsampwidth(self) -> int:
        pass

    @abc.abstractmethod
    def getnchannels(self) -> int:
        pass

    @abc.abstractmethod
    def getframerate(self) -> int:
        pass