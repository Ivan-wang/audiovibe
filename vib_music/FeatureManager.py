import os
import glob
import pickle
import math
import numpy as np

class FeatureManager(object):
    """
    this class mainly takes care acoustic feature save and read, vibration signal generation
    """
    vibration_mode_func = {}
    def __init__(self, meta, features, mode):
        self.meta = meta
        self.features = features
        self.mode = mode
        self.vib_sequence = None

    def set_vibration_sequence(self, seq):
        if seq.dtype != np.uint8:
            seq = (np.clip(seq, 0, 1) * 255).astype(np.uint8)
        self.vib_sequence = seq

    def clear_vibration_sequence(self):
        self.vib_sequence = None

    def vibration_sequence(self, cached=True, **kwargs):
        if self.vib_sequence is not None and cached:
            return self.vib_sequence

        if self.mode in FeatureManager.vibration_mode_func:
            self.vib_sequence = FeatureManager.vibration_mode_func[self.mode](self,**kwargs)
            return self.vib_sequence
        else:
            raise KeyError("unknown vibration mode")

    def frame_len(self):
        return self.meta["len_hop"]

    def vibration_mode(self):
        return self.mode

    def sample_rate(self):
        return self.meta["sr"]

    def sample_len(self):
        return self.meta["len_sample"]

    def feature_names(self):
        return self.meta["audfeats"]

    def feature_data(self, name, prop="data"):
        if name in self.features:
            if prop in self.features[name]:
                return self.features[name][prop]
            else:
                return None
        else:
            return None

    def set_feature_data(self, name, data):
        if name in self.features:
            self.features[name]["data"] = data

    @classmethod
    def vibration_mode(cls, over_ride=False):
    # def vibration_mode(cls, mode_func):
        def register_vibration_mode(mode_func):
            if mode_func.__name__ in cls.vibration_mode_func and not over_ride:
                raise KeyError("Cannot register duplicated vibration mode {mode_func.__name__}")
            cls.vibration_mode_func.update({
                mode_func.__name__: mode_func
            })
            return mode_func
        return register_vibration_mode

    @classmethod
    def from_folder(cls, folder, mode):
        # load vibrations
        # audio = os.path.basename(folder).split(".")[0]
        vibrations = glob.glob(f"{folder}/*.pkl")
        vibrations = {os.path.basename(v).split(".")[0] : v for v in vibrations}
        print(f"find {len(vibrations)} from {folder}:")
        print(vibrations)

        try:
            with open(vibrations["meta"], "rb") as f:
                meta = pickle.load(f)
        except:
            print("cannot load audio meta information")
            return None

        features = {}
        # print("find %d in %s..." % (len(meta["feat_names"]), folder))
        for vib in meta["feat_names"]:
            with open(vibrations[vib], "rb") as f:
                print(f"loading {vib}...")
                features[vib] = pickle.load(f)

        return cls(meta, features, mode)

@FeatureManager.vibration_mode
def power_sequence_mode(fm:FeatureManager) -> np.ndarray:
    power = fm.feature_data("rmse")
