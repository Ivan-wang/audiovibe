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
class BeatPLPIteartor(VibrationIterator):
    alias = 'beatplp'
    def __init__(self, meta, vib_data, vib_func=None):
        super(BeatPLPIteartor, self).__init__()
        pulse = vib_data['data']
        if vib_func is not None:
            self.amp, self.freq = vib_func(pulse)
        else:
            bins = np.linspace(pulse.min(), pulse.max(), num=129, endpoint=True)
            self.amp = np.digitize(pulse, bins).astype(np.uint8)
            self.freq = np.ones_like(self.amp, dtype=np.uint8) * 64

        self.num_frame = -1
        # self.beats = np.flatnonzero(librosa.util.localmax(pulse))

    def __next__(self):
        self.num_frame += 1
        if self.num_frame < len(self.amp):
            return (self.amp[self.num_frame], self.freq[self.num_frame])
        else:
            return (None, None)

# class RmseIterator(VibrationIterator):
#     alias = 'rmse'
#     def __init__(self, meta, vib_data):
#         super(RmseIterator, self).__init__()
#         # TODO handle different HOP_LEN
#         self.rmse = vib_data['data']
#         self.num_frame = -1

#     def __next__(self):
#         self.num_frame += 1
#         if self.num_frame < len(self.rmse):
#             return self.rmse[self.num_frame]
#         else:
#             return None
