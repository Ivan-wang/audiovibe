from boardInvoker import Motor
from pprint import pprint
import numpy as np
import librosa
import pickle
import glob
import os


from config import HOP_LEN

class ConsoleMotor(Motor):
    alias = 'console'
    stgs = {}
    def __init__(self, audioname):
        super().__init__([])
        self.audioname = audioname
        fnames = glob.glob(f'data/{audioname}/*.pkl')
        features = {os.path.basename(f).split('.')[0] : f for f in fnames}
        with open(features['meta'], 'rb') as f:
            self.meta = pickle.load(f)
        
        self.num_frame = self.meta['len_sample'] // HOP_LEN + 1
        print(f'Number of Frame {self.num_frame}')
        self.vib_data = {}
        for vib in self.meta['vibrations']:
            with open(features[vib], 'rb') as f:
                self.vib_data[vib] = pickle.load(f)

    def on_start(self):
        return super().on_start()

    def on_update(self, vib_t, vib):
        self.vibration[vib_t] = vib

    def on_running(self):
        pprint(self.vibration)

    def on_end(self):
        return super().on_end()

def console_motor_stg(func):
    if func.__name__ in ConsoleMotor.stgs:
        raise ValueError(f'Duplicated Function Name {func.__func__}')
    
    ConsoleMotor.stgs.update({func.__name__: func})
    return func

@console_motor_stg
def beatplp(data, sr, hop, len_frame):
    beats = np.flatnonzero(librosa.util.localmax(data)) # frame

    return beats

if __name__ == '__main__':
    motor = ConsoleMotor('YellowRiverInstrument')