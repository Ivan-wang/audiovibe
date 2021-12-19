import sys
sys.path.append('../..')

import pickle
import librosa
import numpy as np
from vib_music import AdcDriver
from vib_music import BoardProcess
from vib_music import FeatureManager
from vib_music import PlotManager
import time

FRAME_TIME = 0.0116

def launch_atomicwave_vibration(atomicwave, duration, scale=1):
    atomicwave *= scale
    print('Atomic Wave:', atomicwave)
    MAGIC_NUM = 1.4
    num_frame = int(duration / FRAME_TIME * MAGIC_NUM)
    est_time = FRAME_TIME * num_frame 
    # print(f'estimated duration {FRAME_TIME * num_frame:.3f}')
    sequence = np.stack([atomicwave]*num_frame, axis=0).astype(np.uint8)
    start = time.time()
    launch_vibration(sequence)
    end = time.time()
    act_time = end-start
    print(f'Running time {end-start:.3f} seconds.')
    print(f'Playing Done')
    

def launch_vibration(sequence):
    driver = AdcDriver(sequence)

    if not driver.on_start():
        raise RuntimeError('Driver initializing failed.')

    vib_proc = BoardProcess(driver, None)
    vib_proc.start()
    vib_proc.join()

def load_music():
    audio = np.load('../../audio/autio.npy')
    fm = FeatureManager.from_folder('../../audio/test_beat_short_1', mode='')

    return audio, fm

def build_plot_manager(audio, fm):
    pm = PlotManager(audio, fm)

    return pm

#TODO: reuse plot manager for drawing
def draw_rmse(audio, fm, ax):
    ax.cla()
    sr = fm.sample_rate()
    hop_len = fm.frame_len()

    librosa.display.waveplot(audio, sr=sr, ax=ax)

    rmse = fm.feature_data('rmse')
    times = librosa.times_like(rmse, sr=sr, hop_length=hop_len)

    ax.plot(times, rmse, 'r')
    ax.set_xlim(xmin=0, xmax=times[-1])


from collections import namedtuple

Transform = namedtuple('Transform', ('name', 'params'))

class TransformQueue(object):
    def __init__(self):
        self.transforms = []
        self.transform_func = {
            'linear': lambda data, start, end: self.__linear_transform(data, start, end),
            'power': lambda data, power: self.__power_transform(data, power),
            'norm': lambda data, mean, std: self.__norm_transform(data, mean, std),
            'shift': lambda data, shift: self.__shift_transform(data, shift)
        }

    def insert(self, trans, pos=-1):
        self.transforms.insert(pos, trans)

    def delete(self, pos=-1):
        self.transforms.remove(self.transforms[pos])

    def move_up(self, pos=-1):
        if pos == 0:
            return
        self.transforms[pos], self.transforms[pos-1] = self.transforms[pos-1], self.transforms[pos]

    def move_down(self, pos=-1):
        if pos == -1 or pos == len(self.transforms)-1:
            return

        self.transforms[pos], self.transforms[pos+1] = self.transforms[pos+1], self.transforms[pos]

    def transform_names(self):
        return [t.name for t in self.transforms]

    def apply_transform(self, data, t):
        return self.transform_func[t.name](data, **t.params)

    def apply_all(self, data):
        for t in self.transforms:
            data = self.apply_transform(data, t)
        return data

    def save_transforms(self, name):
        with open(name, 'wb') as f:
            pickle.dump(self.transforms, f)

    def load_transforms(self, name):
        with open(name, 'rb') as f:
            self.transforms = pickle.load(f)

    def __linear_transform(self, data, start, end):
        return

    def __power_transform(self, data, power):
        return

    def __norm_transform(self, data, mean, std):
        return

    def __shift_transform(self, data, shift):
        return

if __name__ == '__main__':
    waveform = np.array([0.01] * 8 + [0.99] * 4 + [0.01] * 8 + [0.99] * 4)
    scale = 75
    duration = 1.0
    launch_atomicwave_vibration(waveform, duration, scale)
