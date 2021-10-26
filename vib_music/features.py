import os
import pickle
import librosa
import numpy as np

from .misc import BASE_HOP_LEN

# Strategy Pattern
class FeatureExtractionManager(object):
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

    def audio_features(self):
        if self.audio is None: return {}

        features = {'audio': self.audio.copy(), 'sr': self.sr}
        features.update({sname: func(self.audio, self.sr)
            for sname, func in zip(self.stg_names, self.stg)})
        return features

    def save_features(self, features=None, root=None):
        if features is None:
            features = self.audio_features()

        if root is None:
            feat_dir = os.path.join('data', self.audio_name)
        else:
            feat_dir = os.path.join(root, self.audio_name)
        os.makedirs(feat_dir, exist_ok=True)
        # save meta
        meta = {'audio_name': self.audio_name, 'sr': features['sr'],
            'len_sample': self.audio.shape[0], 'len_hop': self.len_hop}
        meta['vibrations'] = self.stg_names
        with open(os.path.join(feat_dir, 'meta.pkl'), 'wb') as f:
            pickle.dump(meta, f)

        # save features
        for n in self.stg_names:
            with open(os.path.join(feat_dir, n+'.pkl'), 'wb') as f:
                pickle.dump(features[n], f)

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

@FeatureExtractionManager.register_vib_meta_stg
def melspec(audio, sr, len_hop, len_window=2048, n_mels=128, fmax=None):
    mel = librosa.feature.melspectrogram(y=audio,
        sr=sr, n_fft=len_window, hop_length=len_hop, n_mels=n_mels, fmax=fmax)
    ret = {'len_window': len_window, 'n_mels': n_mels,
        'fmax': fmax, 'data': mel
    }
    return ret

@FeatureExtractionManager.register_vib_meta_stg
def contrastspec(audio, sr, len_hop, len_window=2048, n_bands=6, band_width=200, use_linear=True):
    contrast = librosa.feature.spectral_contrast(
        y=audio, sr=sr, n_fft=len_window, hop_length=len_hop,
        fmin=band_width, n_bands=n_bands, linear=use_linear
    )
    ret = {'len_window': len_window, 'n_bands': n_bands,
        'band_width': 200, 'use_linear': use_linear, 'data': contrast
    }
    return ret

@FeatureExtractionManager.register_vib_meta_stg
def centroidspec(audio, sr, len_hop, len_window=2048, freqs=None):
    centroid = librosa.feature.spectral_centroid(
        y=audio, sr=sr, n_fft=len_window, hop_length=len_hop,
        freq=freqs
    )

    ret = {'len_window': len_window, 'freqs': freqs,
        'data': centroid
    }
    return ret

@FeatureExtractionManager.register_vib_meta_stg
def beatplp(audio, sr, len_hop, len_frame=300, tempo_min=30, tempo_max=300):
    len_frame = int(len_frame)
    tempo_min = int(tempo_min)
    tempo_max = int(tempo_max)

    # onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=len_hop)
    pulse = librosa.beat.plp(y=audio, sr=sr, hop_length=len_hop,
        win_length=len_frame, tempo_min=tempo_min, tempo_max=tempo_max)
    ret = {
        'len_hop': len_hop, 'len_frame': len_frame,
        'tempo_min': tempo_min, 'tempo_max': tempo_max,
        'data': pulse
    }

    return ret

@FeatureExtractionManager.register_vib_meta_stg
def rmse(audio, sr, len_hop, len_window=2048):
    len_window = int(len_window)

    mse = librosa.feature.rms(y=audio, frame_length=len_window,
        hop_length=len_hop, center=True)
    mse = mse.reshape((-1, ))
    ret = {'len_frame': len_window, 'data': mse}

    return ret

@FeatureExtractionManager.register_vib_meta_stg
def pitchyin(audio, sr, len_hop, len_window=2048, fmin='C2', fmax='C7', thres=0.8):
    len_window = int(len_window)
    thres = float(thres)

    if isinstance(fmin, str):
        fmin = librosa.note_to_hz('C2')
    if isinstance(fmax, str):
        fmax = librosa.note_to_hz('C7')

    f0 = librosa.yin(audio, fmin=fmin, fmax=fmax, sr=sr,
        frame_length=len_window, hop_length=len_hop, trough_threshold=thres, center=True)

    ret = {'len_hop': len_hop, 'len_window': len_window, 'fmin': fmin, 'fmax': fmax,
        'thres': thres, 'data': f0}
    return ret

@FeatureExtractionManager.register_vib_meta_stg
def pitchpyin(audio, sr, len_hop, len_window=2048, fmin='C2', fmax='C7'):
    len_window = int(len_window)

    if isinstance(fmin, str):
        fmin = librosa.note_to_hz('C2')
    if isinstance(fmax, str):
        fmax = librosa.note_to_hz('C7')

    f0, _, _ = librosa.pyin(audio, fmin=fmin, fmax=fmax, sr=sr,
        frame_length=len_window, hop_length=len_hop, center=True)

    ret = {'len_hop': len_hop, 'len_window': len_window, 'fmin': fmin, 'fmax': fmax,
        'data': f0}
    return ret

@FeatureExtractionManager.register_vib_meta_stg
def chromastft(audio, sr, len_hop, len_window=2048, n_chroma=12, tuning=0.0):
    len_window = int(len_window)
    chroma = librosa.feature.chroma_stft(y=audio, sr=sr, n_fft=len_window,
        n_chroma=n_chroma, tuning=tuning)
    chroma = chroma.T # use time at first axis

    ret = {'len_hop': len_hop, 'len_window': len_window, 'data': chroma}
    return ret

@FeatureExtractionManager.register_vib_meta_stg
def chromacqt(audio, sr, len_hop, fmin='C1', n_chroma=12, tuning=0.0):
    # len_window = int(len_window)
    fmin = librosa.note_to_hz(fmin)
    chroma = librosa.feature.chroma_cqt(y=audio, sr=sr, fmin=fmin,
        n_chroma=n_chroma, tuning=tuning)
    chroma = chroma.T # use time at first axis

    ret = {'len_hop': len_hop, 'fmin': fmin, 'data': chroma}
    return ret

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