import os, sys
import copy
import pickle
import numpy as np
from typing import Optional
from collections import namedtuple

from .AtomicWaveBackend import AtomicWaveBackend

sys.path.append('..')

from vib_music import FeatureBuilder, AudioFeatureBundle
from vib_music import FeaturePlotter

Transform = namedtuple('Transform', ('name', 'params'))

class TransformQueue(object):
    def __init__(self):
        self.transforms = []
        self.transform_func = {
            'linear': lambda data, slope, bias: self.__linear_transform(data, slope, bias),
            'power': lambda data, power: self.__power_transform(data, power),
            'norm-std': lambda data, mean, std: self.__norm_transform(data, mean, std),
            'log': lambda data, shift: self.__log_transform(data, shift),
            'norm-min-max': lambda data, min_val, max_val: self.__norm_min_max_transform(data, min_val, max_val)
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
        self.transforms[pos], self.transforms[pos - 1] = self.transforms[pos - 1], self.transforms[pos]

    def move_down(self, pos=-1):
        if pos == -1 or pos == len(self.transforms) - 1:
            return

        self.transforms[pos], self.transforms[pos + 1] = self.transforms[pos + 1], self.transforms[pos]

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
        out = data * slope + bias
        out = np.clip(out, 0, 1)
        return out

    def __power_transform(self, data, power):
        out = np.power(data, power)
        out = np.clip(out, 0, 1)
        return out

    def __norm_transform(self, data, mean, std):
        out = mean + (data - data.mean()) / data.std() * std
        out = np.clip(out, 0, 1)
        return out

    def __log_transform(self, data, gamma):
        out = np.log(1 + data) * gamma
        out = np.clip(out, 0, 1)
        return out

    def __norm_min_max_transform(self, data, min_val, max_val):
        if (min_val >= max_val):
            print('Min value is greater than max value')
            return data
        out = (data-data.min()) / (data.max()-data.min())
        out = out * (max_val-min_val) + min_val

        return out

class VibModeBackend(object):
    def __init__(self) -> None:
        self.audio = None
        self.loaded_feature_bundle = None
        self.running_feature_bundle = None
        self.transforms_queue = TransformQueue()
        self.atomic_wave_db = AtomicWaveBackend()
        self.feature_plotter = FeaturePlotter()

        self.feature_plotter.set_plots(['waveform', 'wavermse'])
    
    def load_audio(self, audio:str) -> None:
        self.audio = audio
        self.feature_plotter.set_audio(audio)

    def feature_bundle(self, use_cached:bool=True,
        sketch_transform:Optional[Transform]=None) -> Optional[AudioFeatureBundle]:
        if use_cached:
            return self.loaded_feature_bundle
        else:
            rmse = self.loaded_feature_bundle.feature_data('rmse').copy()
            vib = self.transforms_queue.apply_all(rmse, curve=False)
            if sketch_transform is not None:
                vib = self.transforms_queue.apply_transform(vib, sketch_transform, curve=False)
            self.running_feature_bundle['rmse']['data'] = vib
            return self.running_feature_bundle
    
    def atomic_waves(self) -> AtomicWaveBackend:
        return self.atomic_wave_db
    
    def transforms(self) -> TransformQueue:
        return self.transforms_queue
    
    def plotter(self) -> FeaturePlotter:
        return self.feature_plotter

    def load_atomic_wave_db(self, db:str) -> None:
        self.atomic_wave_db = AtomicWaveBackend(db)

    def init_features(self, audio:str, len_hop:int, use_cache:bool=False) -> None:
        # build feature dirs if necessary
        DATA_DIR = '../data/'
        os.makedirs(DATA_DIR, exist_ok=True)
        DATA_DIR = os.path.join(DATA_DIR, 'vib_editor')
        os.makedirs(DATA_DIR, exist_ok=True)

        feature_dir = os.path.basename(audio).split('.')[0]
        feature_dir = os.path.join(DATA_DIR, feature_dir)
        if not use_cache or not os.path.isdir(feature_dir):
            # extract and save features
            recipe = {
                'rmse': {
                    'len_window': 1024
                },
                'melspec': {
                    'len_window': 1024,
                    'n_mels': 128,
                    'fmax': None
                }
            }

            fbuilder = FeatureBuilder(audio, None, len_hop)
            fb = fbuilder.build_features(recipe)
            fb.save(feature_dir)
        else:
            fb = AudioFeatureBundle.from_folder(feature_dir)
        
        # don't set feature bundle to plotter
        # self.feature_plotter.set_audio_feature_bundle(fb)
        self.loaded_feature_bundle = fb
        self.running_feature_bundle = copy.deepcopy(fb)
