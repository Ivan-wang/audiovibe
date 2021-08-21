import numpy as np

from .MotorInvoker import MotorInvoker

class VibrationIterator(object):
    def __init__(self, vib_matrix=None):
        super(VibrationIterator, self).__init__()
        self._vib_matrix = vib_matrix

    def __iter__(self):
        return self

    @property
    def vib_matrix(self):
        return self._vib_matrix

    @vib_matrix.setter
    def vib_matrix(self, vib_matrix):
        self._vib_matrix = vib_matrix

@MotorInvoker.register_vib_iterator
class FrameCounter(VibrationIterator):
    alias = 'frame'
    def __init__(self, meta=None, vib_func=None):
        super(FrameCounter, self).__init__()
        self.num_frame = -1

    def __next__(self):
        self.num_frame += 1
        return self.num_frame


@MotorInvoker.register_vib_iterator
class LambdaIterator(VibrationIterator):
    def __init__(self, meta, vib_data, vib_func):
        super().__init__()
        data = vib_data['data']
        self.amp, self.freq = vib_func(data)
    
        self.num_frame = -1

    def __next__(self):
        self.num_frame += 1
        if self.num_frame < len(self.amp):
            return (self.amp[self.num_frame], self.freq[self.num_frame])
        else:
            return (None, None)


def _default_beatplp_func(pulse):
    bins = np.linspace(pulse.min(), pulse.max(), num=129, endpoint=True)
    amp = np.digitize(pulse, bins).astype(np.uint8)
    freq = np.ones_like(amp, dtype=np.uint8) * 64

    return amp, freq

@MotorInvoker.register_vib_iterator
class BeatPLPIteartor(LambdaIterator):
    alias = 'beatplp'
    def __init__(self, meta, vib_data, vib_func=_default_beatplp_func):
        super(BeatPLPIteartor, self).__init__(meta, vib_data, vib_func)

def _default_pitch_func(pitch):
    return [], []

@MotorInvoker.register_vib_iterator
class PitchIterator(LambdaIterator):
    alias = 'pitch'
    def __init__(self, meta, vib_data, vib_func=_default_beatplp_func):
        super(PitchIterator, self).__init__(meta, vib_data, vib_func)
