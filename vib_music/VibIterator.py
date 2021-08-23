import numpy as np

from .invoker import MotorInvoker

class VibrationIterator(object):
    def __init__(self, audio_meta, feature):
        super(VibrationIterator, self).__init__()
        self._feature = feature

    def __iter__(self):
        return self
    
    @property
    def feature(self):
        return self._feature
    
    @feature.setter
    def feature(self, feature):
        self._feature = feature

@MotorInvoker.register_vib_iterator
class FrameIterator(VibrationIterator):
    alias = 'frame'
    def __init__(self, *args):
        super(FrameIterator, self).__init__(None, None)
        self.num_frame = -1

    def __next__(self):
        self.num_frame += 1
        return self.num_frame

class SequenceIterator(VibrationIterator):
    def __init__(self, audio_meta, feature):
        super().__init__(audio_meta, feature)
        self.num_frame = -1

    def __next__(self):
        self.num_frame += 1
        if self.num_frame < len(self._feature['data']):
            return self._feature['data'][self.num_frame]
        else:
            return None
    
def _default_beatplp_func(pulse):
    bins = np.linspace(pulse.min(), pulse.max(), num=129, endpoint=True)
    amp = np.digitize(pulse, bins).astype(np.uint8)
    freq = np.ones_like(amp, dtype=np.uint8) * 64

    return amp, freq

@MotorInvoker.register_vib_iterator
class AmpIterator(SequenceIterator):
    alias = 'amp'
    def __init__(self, audio_meta, amp):
        super().__init__(audio_meta, {'data': amp})

@MotorInvoker.register_vib_iterator
class FreqIterator(SequenceIterator):
    alias = 'freq'
    def __init__(self, audio_meta, freq):
        super().__init__(audio_meta, {'data': freq})

@MotorInvoker.register_vib_iterator
class BeatPLPIteartor(SequenceIterator):
    alias = 'beatplp'
    def __init__(self, audio_meta, data):
        super(BeatPLPIteartor, self).__init__(audio_meta, data)

@MotorInvoker.register_vib_iterator
class PitchIterator(SequenceIterator):
    alias = 'pitch'
    def __init__(self, audio_meta, data):
        super(PitchIterator, self).__init__(audio_meta, data)

@MotorInvoker.register_vib_iterator
class ChromaIterator(SequenceIterator):
    alias = 'chroma'
    def __init__(self, audio_meta, data):
        data['data'] = data['data'].T
        super(ChromaIterator, self).__init__(audio_meta, data)