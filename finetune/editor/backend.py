import sys
sys.path.append('../..')

import os
import pickle
import librosa
import numpy as np
from vib_music import AdcDriver
from vib_music import BoardProcess
from vib_music import FeatureManager
from vib_music import FeatureExtractionManager
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

from vib_music.misc import init_vibration_extraction_config
def load_audio(audio_path, use_cache=False):
    # load audio data
    audio, _ = librosa.load(audio_path, sr=None)

    # extract or load features
    DATA_DIR = './features'
    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)

    feature_folder = os.path.basename(audio_path).split('.')[0]
    feature_folder = os.path.join(DATA_DIR, feature_folder)
    if not use_cache or not os.path.isdir(feature_folder):
        # extract and save features
        librosa_config = init_vibration_extraction_config()
        librosa_config['audio'] = audio_path
        librosa_config['len_hop'] = 512 # hardcoded: HOP_LEN = 512

        librosa_config['stgs']['rmse'] = {
            'len_window': 2048, # harded coded: WIN_LEN = 2048
        }
        librosa_config['stgs']['melspec'] = {
            'len_window': 2048, # hard coded: WIN_LEN = 2048
            'n_mels': 128, # hard coded: N_MELS = 128
            'fmax': None # hard coded: F_MAX = NONE
        }

        ctx = FeatureExtractionManager.from_config(librosa_config)
        ctx.save_features(root=DATA_DIR)

    fm = FeatureManager.from_folder(feature_folder, mode='')

    return audio, fm

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
            'linear': lambda data, slope, bias: self.__linear_transform(data, slope, bias),
            'power': lambda data, power: self.__power_transform(data, power),
            'norm': lambda data, mean, std: self.__norm_transform(data, mean, std),
            'log': lambda data, shift: self.__log_transform(data, shift)
        }

    def get_transform(self, idx):
        if idx < len(self.transforms):
            return self.transforms[idx]
        else:
            return None

    def append(self, trans):
        self.transforms.append(trans)

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

    def update(self, params, pos):
        self.transforms[pos] = Transform(self.transforms[pos].name, params)

    def transform_list(self):
        return self.transforms

    def apply_transform(self, data, t, curve=True):
        if curve and t.name == 'norm':
            return data
        else:
            return self.transform_func[t.name](data, *t.params)

    def apply_all(self, data, curve=True):
        for t in self.transforms:
            data = self.apply_transform(data, t, curve)
        return data

    def save_transforms(self, name):
        with open(name, 'wb') as f:
            pickle.dump(self.transforms, f)

    def load_transforms(self, name):
        with open(name, 'rb') as f:
            self.transforms = pickle.load(f)

    def __len__(self):
        return len(self.transforms)

    def __linear_transform(self, data, slope, bias):
        out = data*slope + bias
        out = np.clip(out, 0, 1)
        return out

    def __power_transform(self, data, power):
        out = np.power(data, power)
        out = np.clip(out, 0, 1)
        return out

    def __norm_transform(self, data, mean, std):
        out = mean + (data-data.mean()) / data.std() * std
        out = np.clip(out, 0, 1)
        return out

    def __log_transform(self, data, gamma):
        out = np.log(1+data) * gamma
        out = np.clip(out, 0, 1)
        return out

if __name__ == '__main__':
    waveform = np.array([0.01] * 8 + [0.99] * 4 + [0.01] * 8 + [0.99] * 4)
    scale = 75
    duration = 1.0
    launch_atomicwave_vibration(waveform, duration, scale)
