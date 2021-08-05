import os
import glob
import pickle

# adafruit lib
# import board
# import busio
# import adafruit_drv2605

# dispatch vibration
class BoardInvoker(object):
    motor_t = {}
    iterator_t = {}
    def __init__(self, audio, motors=[]):
        super(BoardInvoker, self).__init__()
        # self.drv = None
        self.motors = self._init_motors(motors)

        vibrations = glob.glob(f'data/{audio}/*.pkl')
        vibrations = {os.path.basename(v).split('.')[0] : v for v in vibrations}
        with open(vibrations['meta'], 'rb') as f:
            self.meta = pickle.load(f)
        
        self.vib_iter = {'frame': FrameCounter()}
        for vib in self.meta['vibrations']:
            with open(vibrations[vib], 'rb') as f:
                self.vib_iter[vib] = self._build_vib_iter(vib, self.meta, pickle.load(f))
    
    def _build_vib_iter(self, vib_t, audio_meta, vib_data):
        if vib_t not in BoardInvoker.iterator_t:
            raise KeyError(f'Cannot build iterator for {vib_t}')
        
        return BoardInvoker.iterator_t[vib_t](audio_meta, vib_data)

    def _init_motors(self, motor_t):
        motors = []
        for (name, kwargs) in motor_t:
            if name in BoardInvoker.motor_t:
                motors.append(BoardInvoker.motor_t[name](**kwargs))
            else:
                print(f'Unrecongnized Motor Type {name}')

        return motors

    def on_start(self):
        for m in self.motors:
            m.on_start(self.meta)

    def on_update(self):
        bundle = {k: next(i) for k, i in self.vib_iter.items()}
        # print(bundle)
        for m in self.motors:
            m.on_running(bundle)

    def on_end(self):
        for m in self.motors:
            m.on_end()
    @classmethod
    def from_config(cls, config):
        return cls(config['audio'], config['motors'])

import numpy as np
import librosa

class VibrationIteratorMeta(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(VibrationIteratorMeta, cls).__new__(cls, clsname, bases, attrs)
        alias = getattr(newclass, 'alias', None)
        if alias is not None:
            BoardInvoker.iterator_t.update({alias: newclass})
        return newclass

from collections.abc import Iterator
class VibrationIterator(object, metaclass=VibrationIteratorMeta):
    def __init__(self):
        super(VibrationIterator, self).__init__()
    
    def __iter__(self):
        return self
    
class FrameCounter(VibrationIterator):
    def __init__(self):
        super(FrameCounter, self).__init__()
        self.num_frame = -1
    
    def __next__(self):
        self.num_frame += 1
        return self.num_frame

import numpy as np
class BeatPLPIteartor(VibrationIterator):
    alias = 'beatplp'
    def __init__(self, meta, vib_data):
        super(BeatPLPIteartor, self).__init__()
        pulse = vib_data['data']
        self.beats = np.flatnonzero(librosa.util.localmax(pulse))
        self.num_frame = -1

    def __next__(self):
        self.num_frame += 1
        if self.num_frame in self.beats:
            return True
        else:
            return None

class RmseIterator(VibrationIterator):
    alias = 'rmse'
    def __init__(self, meta, vib_data):
        super(RmseIterator, self).__init__()
        # TODO handle different HOP_LEN
        self.rmse = vib_data['data']
        self.num_frame = -1
    
    def __next__(self):
        self.num_frame += 1
        if self.num_frame < len(self.rmse):
            return self.rmse[self.num_frame]
        else:
            return None

# class Drv2605Motor(Motor):
#     def on_start(self):
#         pass
#         # i2c = busio.I2C(board.SCL, board.SDA)
#         # self.drv = adafruit_drv2605(i2c)

#     def on_running(self, features):
#         return super().on_running(features)

#     def on_end(self):
#         return super().on_end()
