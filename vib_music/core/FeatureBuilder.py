import os
import librosa
import numpy as np
from typing import Dict, Optional, Union

from .FeatureBundle import AudioFeatureBundle

class FeatureBuilder(object):
    """
    this class mainly takes care of acoustic feature extraction
    """
    stg_funcs = {}
    def __init__(self, audio:Union[str, np.ndarray], sr:Optional[int]=None, len_hop:Optional[int]=512):
        super(FeatureBuilder, self).__init__()

        if isinstance(audio, str):
            self.audio_name = os.path.basename(audio).split('.')[0]
            audio, self.sr = librosa.load(audio, sr=sr)
        else:
            assert sr is not None, 'SR cannot be None if audio is np.ndarray'
            self.sr = sr
            self.audio_name = 'audio_clip'

        self.len_hop = len_hop

        frame_num = (audio.shape[-1]+len_hop-1) // len_hop
        audio_shape = (frame_num*len_hop) if len(audio.shape) == 1 else (2, frame_num*len_hop)

        self.audio = np.zeros(audio_shape, dtype=audio.dtype)
        self.audio[..., :audio.shape[-1]] = audio

    def _extract_func(self, stg:str, kwargs:Dict):
        kwargs.setdefault('len_hop', self.len_hop)

        if stg in FeatureBuilder.stg_funcs:
            func = FeatureBuilder.stg_funcs[stg]
            def wfunc(audio, sr):
                return func(audio, sr, **kwargs)
            wfunc.__name__ = stg
            return wfunc
        else:
            raise NotImplementedError(f'{stg} is not implemented')
    
    
    def build_features(self, recipe:Dict[str,Dict]) -> AudioFeatureBundle:
        fb = AudioFeatureBundle()

        fb.update({'meta':{
            "audio_name": self.audio_name,
            "sr": self.sr,
            "len_sample": self.audio.shape[0], 
            "len_hop": self.len_hop,
            "recipe": list(recipe.keys())
            }})
        
        for stg, kwargs in recipe.items():
            fb.update({stg: self._extract_func(stg, kwargs)(self.audio, self.sr)})

        return fb

    @classmethod
    def feature_build_stg(cls, func):
        if func.__name__ in cls.stg_funcs:
            raise ValueError(f'Duplicate Function Name {func.__name__}')

        cls.stg_funcs.update({func.__name__: func})
        return func

    @classmethod
    def available_build_stgs(cls):
        return list(cls.feature_build_stg.keys())