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
from config import HOP_LEN

class ConsoleMotor(Motor):
    alias = 'console'
    def __init__(self, show_none=True, show_frame=True):
        super().__init__()
        self.show_none = show_none
        self.show_frame = show_frame

    def on_start(self, meta):
        total_frame = meta['len_sample'] // HOP_LEN
        if meta['len_sample'] % HOP_LEN != 0:
            total_frame += 1
        self.bar = tqdm(desc='[Console Motor]', unit=' frame', total=total_frame)

    def on_running(self, vibrations):
        vib_str = self._build_vibration_str(vibrations)
        if len(vib_str) > 0:
            tqdm.write(vib_str)
        self.bar.update()

    def on_end(self):
        self.bar.close()
    
    def _build_vibration_str(self, vibrations):
        vibs = []
        for k in vibrations:
            if k == 'frame':
                continue
            if self.show_none or vibrations[k] is not None:
                vibs.append('{} : {}'.format(k, vibrations[k]))
        if self.show_frame and len(vibs) > 0:
            vibs.append('{} : {}'.format('frame', vibrations['frame']))
        vib_str = ' | '.join(vibs)
        return vib_str