import pickle
import numpy as np
from collections import namedtuple

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