import os
import pickle
import librosa
import numpy as np
import time
from .misc import BASE_HOP_LEN

class FeatureExtractionManager(object):
    """
    this class mainly takes care of acoustic feature extraction
    """
    stg_meta_funcs = {}
    stg_funcs = {}
    def __init__(self, audio=None, sr=None, len_hop=BASE_HOP_LEN, stg={}):
        super().__init__()
        # load audio data
        if isinstance(audio, str):
            self.audio_name = os.path.basename(audio).split('.')[0]
            self.audio, self.sr = librosa.load(audio, sr=sr)
        else:
            assert isinstance(audio, np.ndarray), 'audio should be a path-like object or np.ndarray'
            assert sr is not None, 'SR cannot be None if audio is np.ndarray'
            self.audio_name = 'audio_clip'
            self.audio = audio
            self.sr = sr

        # pad audio divisible by len_hop
        frame_num = self.audio.shape[-1] // len_hop + 1
        current_len = self.audio.shape[-1]
        expect_len = frame_num * len_hop
        if len(self.audio.shape)>1:    # multi channel case
            self.audio = np.pad(self.audio, ((0.0), (expect_len-current_len,0)), 'constant', constant_values=0)
        else:    # single channel case
            self.audio = np.pad(self.audio, (expect_len-current_len,0), 'constant', constant_values=0)
        print(f"we should have {len(self.audio)//len_hop} frames")

        self.len_hop = len_hop
        self.stg_names = list(stg.keys())
        self.stg = [self._init_stg(s, v) for s, v in stg.items()]

    def _init_stg(self, stg, kwargs):
        if stg in FeatureExtractionManager.stg_funcs:
            return FeatureExtractionManager.stg_funcs[stg]

        stg_name = stg
        if 'len_hop' not in kwargs:
            kwargs['len_hop'] = self.len_hop

        if stg_name in FeatureExtractionManager.stg_meta_funcs:
            func = FeatureExtractionManager.stg_meta_funcs[stg_name]
            def wfunc(autio, sr):
                return func(autio, sr, **kwargs)
            wfunc.__name__ = stg
            return wfunc
        else:
            raise NotImplementedError(f'{stg} is not implemented')

    @property
    def sound(self):
        return self.audio

    @sound.setter
    def sound(self, sound):
        self.audio = sound

    @property
    def strategy(self):
        return self.stg

    @strategy.setter
    def strategy(self, stg):
        self.stg_names = list(stg.keys())
        self.stg = [self._init_stg(s, v) for s, v in stg.items()]

    def audio_features(self, extract_list=[]):
        if self.audio is None: return {}

        features = {'audio': self.audio.copy(), 'sr': self.sr}
        for sname, func in zip(self.stg_names, self.stg):
            # ### debug print ###
            # print(f"preparing {sname}...")
            # ######
            if sname in extract_list:
                features.update({sname: func(self.audio, self.sr)})
        return features

    def save_features(self, features=None, root=None):
        if root is None:
            feat_dir = os.path.join('data', self.audio_name)
        else:
            feat_dir = os.path.join(root, self.audio_name)
        os.makedirs(feat_dir, exist_ok=True)

        # save features
        for n in self.stg_names:
            feat_file = os.path.join(feat_dir, n+'.pkl')
            if not os.path.exists(feat_file):
                if features is None:
                    features = self.audio_features(extract_list=[n])
                dump_data = features[n]
                with open(feat_file, 'wb') as f:
                    pickle.dump(dump_data, f)
                    features = None    # reset feature for next update

        # save meta
        meta = {"audio_name": self.audio_name, "sr": self.sr, "len_sample": self.audio.shape[0], "len_hop":
            self.len_hop}
        meta["audfeats"] = self.stg_names
        with open(os.path.join(feat_dir, 'meta.pkl'), 'wb') as f:
            pickle.dump(meta, f)

    @classmethod
    def from_config(cls, config):
        #TODO: compability check
        assert config['version'] > 0.1

        audio = config['audio']
        sr = config['sr']
        len_hop = config['len_hop']

        # TODO: check args for each strategy
        stgs = config['stgs']

        return cls(audio, sr, len_hop, stgs)

    @classmethod
    def register_vib_stg(cls, func):
        if func.__name__ in cls.stg_funcs:
            raise ValueError(f'Duplicate Function Name {func.__name__}')

        cls.stg_funcs.update({func.__name__: func})
        return func
    @classmethod
    def register_vib_meta_stg(cls, func):
        if func.__name__ in cls.stg_meta_funcs:
            raise ValueError(f'Duplicate Function Name {func.__name__}')

        cls.stg_meta_funcs.update({func.__name__: func})
        return func

if __name__ == '__main__':
    import yaml
    # load template config
    with open('configs/librosa_context.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # change configures
    # audio = 'audio/YellowRiverInstrument.wav'
    # config['audio'] = audio
    config['stgs']['beatplp']['len_frame'] = 50

    # add new configures
    # config['stgs']['rmse'] = {'len_window': 1024}

    # initial cxt from config
    ctx = FeatureExtractionManager.from_config(config)
    features = ctx.audio_features()
    ctx.save_features()