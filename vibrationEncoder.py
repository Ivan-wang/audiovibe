import pandas as pd
import numpy as np

# from utils import get_feature
def get_feature(features, k=None, prefix=None):
    if k is not None and k in features:
        return features[k]
    
    for name in features:
        if name.startswith(prefix):
            return features[name]

    return None 
class VibrationEncoder(object):
    enc_funcs = {}
    def __init__(self, stg=None):
        super().__init__()
        if isinstance(stg, str):
            stg = [stg]
        self.stg_names = stg
        self.stg_funcs = [self._init_enc_func(s) for s in stg]
    
    def _init_enc_func(self, stg):
        if stg in VibrationEncoder.enc_funcs:
            return VibrationEncoder.enc_funcs[stg]

    def fit(self, features):
        encoded = {'audio': features['audio'], 'sr': features['sr']}
        encoded.update({sname: func(features)
            for sname, func in zip(self.stg_names, self.stg_funcs)
        })

        return encoded

def vib_encoder_stg(func):
    if func.__name__ in VibrationEncoder.enc_funcs:
        raise ValueError(f'Duplicate Function Name {func.__name__}')

    VibrationEncoder.enc_funcs.update({func.__name__: func})
    return func

@vib_encoder_stg
def rmse_level(features):
    rmse = get_feature(features, prefix='rmse')
    bins = np.linspace(0, 0.5, num=7, endpoint=False)

    # TODO: select a suitable bins
    return pd.cut(rmse.reshape((-1,)), bins=bins, labels=False)

# @vib_encoder_stg
# def board_vibe_encoder():
    # pass
