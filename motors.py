from boardInvoker import BoardInvoker

from abc import ABC, abstractmethod

class MotorMeta(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(MotorMeta, cls).__new__(cls, clsname, bases, attrs)
        alias = getattr(newclass, 'alias', None)
        if alias is not None:
            BoardInvoker.motor_t.update({alias: newclass})
        return newclass

class Motor(object, metaclass=MotorMeta):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_running(self, vibrations):
        pass

    @abstractmethod
    def on_end(self):
        pass

from tqdm import tqdm
from config import BASE_HOP_LEN

class ConsoleMotor(Motor):
    alias = 'console'
    def __init__(self, show_none=True, show_frame=True):
        super().__init__()
        self.show_none = show_none
        self.show_frame = show_frame

    def on_start(self, meta):
        total_frame = meta['len_sample'] // BASE_HOP_LEN
        if meta['len_sample'] % BASE_HOP_LEN != 0:
            total_frame += 1
        self.bar = tqdm(desc='[Console Motor]', unit=' frame', total=total_frame)

    def on_running(self, vibrations):
        vib_str = self._build_vibration_str(vibrations)
        if len(vib_str) != 0:
            if len(vib_str) > 80:
                tqdm.write(vib_str)
            else:
                self.bar.set_postfix(vibrations, refresh=True)
        self.bar.update()

    def on_end(self):
        self.bar.close()
    
    def _build_vibration_str(self, vibrations):
        vibs = []
        for k in vibrations:
            if k == 'frame':
                continue
            if vibrations[k] is not None:
                vibs.append('{} : {:.4f}'.format(k, vibrations[k]))
            elif self.show_none:
                vibs.append('{} : {}'.format(k, vibrations[k]))
            else:
                pass

        if self.show_frame and len(vibs) > 0:
            vibs.append('{} : {}'.format('frame', vibrations['frame']))
        vib_str = ' | '.join(vibs)
        return vib_str

import numpy as np
class BoardMotor(Motor):
    alias = 'board'
    def __init__(self, vib_queue):
        self.vib_queue = vib_queue
    
    def on_start(self, meta):
        pass
    
    def on_running(self, vibrations):
        amp, freq = self._handle_vibrations(vibrations)

        if amp is not None:
            self.vib_queue.put((amp, freq, False))
        else:
            self.vib_queue.put((0, 0, True))

    def on_end(self):
        pass
    
    def _handle_vibrations(self, vibrations):
        next_amp = vibrations['beatplp'] # Int, 1 - 128

        # handle amp , and freq here
        if next_amp is None:
            return None, None
        else:
            next_freq = 64
            return next_amp, next_freq