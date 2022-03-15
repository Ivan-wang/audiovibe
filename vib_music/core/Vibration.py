import numpy as np

class VibrationFormatError(Exception):
    pass

class Vibration(object):
    '''
    Generating vibrations, providing a file-like IO like wave lib for .wav files
    '''
    vibration_mode_func = {}
    def __init__(self, vibration:np.ndarray) -> None:
        self.vibration = vibration.ravel().astype(np.uint8)
        self.len_frame = len(self.vibration)
        self.pos_frame = 0

    def getnframes(self) -> int:
        return self.num_frame

    def readframes(self, n:int=1) -> np.ndarray:
        frames = self.vibration[self.frame_pos:self.frame_pos+n*self.len_frame]
        self.pos_frame = min(self.len_frame-1, self.pos_frame+n*self.len_frame)

        return frames

    def rewind(self) -> None:
        self.pos_frame = 0

    def tell(self) -> int:
        return self.pos_frame

    def setpos(self, pos:int) -> None:
        self.pos_frame = min(self.len_frame, self.pos_frame+pos)

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

