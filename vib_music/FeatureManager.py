import os
import glob
import pickle
import math
import numpy as np

class FeatureManager(object):
    vibration_mode_func = {}
    # def __init__(self, num_frame, vib_iterators, motors):
    def __init__(self, meta, features, mode):
        self.meta = meta
        self.features = features
        self.mode = mode

    def vibration_sequence(self):
        if self.mode in FeatureManager.vibration_mode_func:
            return FeatureManager.vibration_mode_func[self.mode](self)
        else:
            raise KeyError('unknown vibration mode')

    def frame_len(self):
        return self.meta['len_hop']

    def vibration_mode(self):
        return self.mode

    def sample_rate(self):
        return self.meta['sr']

    def sample_len(self):
        return self.meta['len_sample']

    def feature_names(self):
        return self.meta['vibrations']

    def feature_data(self, name, prop='data'):
        if name in self.features:
            if prop in self.features[name]:
                return self.features[name][prop]
            else:
                return None
        else:
            return None

    @classmethod
    def vibration_mode(cls, mode_func):
        if mode_func.__name__ in cls.vibration_mode_func:
            raise KeyError('Cannot register duplicated vibration mode {mode_func.__name__}')
        cls.vibration_mode_func.update({
            mode_func.__name__: mode_func
        })
        return mode_func

    @classmethod
    def from_folder(cls, folder, mode):
        # load vibrations
        # audio = os.path.basename(folder).split('.')[0]
        vibrations = glob.glob(f'{folder}/*.pkl')
        vibrations = {os.path.basename(v).split('.')[0] : v for v in vibrations}
        print(f'find {len(vibrations)} from {folder}:')
        print(vibrations)

        try:
            with open(vibrations['meta'], 'rb') as f:
                meta = pickle.load(f)
        except:
            print('cannot load audio meta information')
            return None

        features = {}
        print(f'find {len(meta["vibrations"])} in {folder}...')
        for vib in meta['vibrations']:
            with open(vibrations[vib], 'rb') as f:
                print(f'loading {vib}...')
                features[vib] = pickle.load(f)

        return cls(meta, features, mode)

@FeatureManager.vibration_mode
def power_sequence_mode(fm:FeatureManager) -> np.ndarray:
    power = fm.feature_data('rmse')
