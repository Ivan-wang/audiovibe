import wave
import numpy as np

from .core import StreamDataI, AudioStreamI
from .core import AudioFeatureBundle

class WaveAudioStream(AudioStreamI):
    def __init__(self, wavefile:str, len_frame:int) -> None:
        # NOTE: avoid opening the wave here, opening files may have problems when sharing by difference process
        super(WaveAudioStream, self).__init__()
        self.wavefile = wavefile
        self.len_frame = len_frame
    
    def init_stream(self) -> None:
        try:
            self.chunks = wave.open(self.wavefile, 'rb')
        except:
            # NOTE: error cannot open wave file
            self.chunks = None
        return super().init_stream()
    def getnframes(self) -> int:
        return (self.chunks.getnframes()+self.len_frame-1) // self.len_frame

    def readframe(self, n: int = 1):
        return self.chunks.readframes(n*self.len_frame)

    def tell(self) -> int:
        return self.chunks.tell() // self.len_frame
    
    def setpos(self, pos:int) -> None:
        if self.chunks is not None:
            self.chunks.setpos(pos*self.len_frame)
    
    def rewind(self) -> None:
        self.chunks.rewind()
    
    def close(self) -> None:
        self.chunks.close()
    
    def getsampwidth(self) -> int:
        return self.chunks.getsampwidth()
    
    def getnchannels(self) -> int:
        return self.chunks.getnchannels()
    
    def getframerate(self) -> int:
        return self.chunks.getframerate()

class VibrationFormatError(Exception):
    pass
    
class VibrationStream(StreamDataI):
    '''
    Generating vibrations, providing a file-like IO like wave lib for .wav files
    '''
    vibration_mode_func = {}
    def __init__(self, chunks:np.ndarray, len_frame:int) -> None:
        super(VibrationStream, self).__init__()
        self.chunks = chunks.ravel().astype(np.uint8)
        self.len_frame = len_frame
        self.pos = 0

    def init_stream(self) -> None:
        self.rewind()

    def getnframes(self) -> int:
        return (self.chunks.shape[0]+self.len_frame-1) // self.len_frame

    def readframe(self, n:int=1) -> np.ndarray:
        frames = self.chunks[self.pos*self.len_frame:(self.pos+n)*self.len_frame]
        self.pos = min(self.getnframes(), self.pos+n)

        return frames

    def rewind(self) -> None:
        self.pos = 0

    def tell(self) -> int:
        return self.pos

    def setpos(self, pos:int) -> None:
        self.pos = min(self.getnframes(), pos)

    def close(self) -> None:
        pass

    @classmethod
    def vibration_mode(cls, over_ride=False):
        def register_vibration_mode(mode_func):
            if mode_func.__name__ in cls.vibration_mode_func and not over_ride:
                raise KeyError("Duplicated vibration mode {mode_func.__name__}")
            cls.vibration_mode_func.update({
                mode_func.__name__: mode_func
            })
            return mode_func
        return register_vibration_mode
    
    @classmethod
    def from_feature_bundle(cls, fb:AudioFeatureBundle, len_frame:int, mode:str):
        if mode in VibrationStream.vibration_mode_func:
            return cls(VibrationStream.vibration_mode_func[mode](fb), len_frame)
        else:
            raise VibrationFormatError(f'vibration mode {mode} not defined.')

class LiveVibrationStream(StreamDataI):
    live_vibration_mode_func = {}
    def __init__(self) -> None:
        super().__init__()

    def getnframes(self) -> int:
        return -1

    # live stream position is always latest, just return -1
    def tell(self) -> int:
        return -1

    # cannot rewind a live stream data
    def rewind(self) -> None:
        self.clear_buffer()
    
    def close(self) -> None:
        return None
    
    def setpos(self, pos: int) -> None:
        self.clear_buffer()
    
    def clear_buffer(self) -> None:
        return None
