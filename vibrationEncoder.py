import pandas as pd

from utils import get_feature

class VibrationEncoder(object):
    enc_funcs = {}
    def __init__(self, stg=None):
        super().__init__()
        if isinstance(stg, str):
            stg = [stg]
        self.stg_names = []
        self.stg_funcs = [self._init_enc_func(s) for s in stg]
    
    def _init_enc_func(self, stg):
        if stg in VibrationEncoder.enc_funcs:
            return VibrationEncoder.enc_funcs[stg]

    def fit(self, features):
        encoded = {'audio': features['audio'], 'sr': features['sr']}
        encoded.update({sname: func(features)
            for sname, func in zip(self.stg_names, self.stg_funcs)
        })

def vib_encoder_stg(func):
    if func.__name__ in VibrationEncoder.enc_funcs:
        raise ValueError(f'Duplicate Function Name {func.__name__}')

    VibrationEncoder.enc_funcs.update({func.__name__: func})
    return func

@vib_encoder_stg
def rmse_enc(features):
    rmse = get_feature(features, prefix='rmse')

    return pd.cut(rmse, bins=7, labels=False)

# @vib_encoder_stg
# def board_vibe_encoder():
    # pass
