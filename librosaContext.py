import numpy as np
import librosa
from utils import load_audio

DEFAULT_FRAME_LEN = 4096
DEFAULT_WIN_LEN = 4096
DEFAULT_HOP_LEN = 1024
# Strategy Pattern
class LibrosaContext(object):
    stg_meta_funcs = {}
    stg_funcs = {}
    def __init__(self, audio='', sr=None, stg=None):
        super().__init__()
        if isinstance(audio, str):
            if len(audio) == 0:
                self.audio, self.sr = load_audio()
                self.audio = self.audio[:self.sr*3]
            else: 
                self.audio, self.sr = librosa.load(audio, sr=None)
        else:
            self.audio = audio
            self.sr = sr
            if self.audio is None:
                assert self.sr is not None
    
        if isinstance(stg, str):
            self.stg_names = [stg]
            self.stg = [self._init_stg(stg)]
        elif isinstance(stg, list):
            self.stg_names = stg
            self.stg = [self._init_stg(s) for s in stg]
        else:
            self.stg_names = []
            self.stg = None
    
    def _init_stg(self, stg):
        if stg in LibrosaContext.stg_funcs:
            return LibrosaContext.stg_funcs[stg]
        
        stg_name, *args = stg.split('_')
        if stg_name in LibrosaContext.stg_meta_funcs:
            func = LibrosaContext.stg_meta_funcs[stg_name]
            def wfunc(autio, sr):
                return func(autio, sr, *args)
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
        if isinstance(stg, str):
            self.stg_names = [stg]
            self.stg = [self._init_stg(stg)]
        elif isinstance(stg, list):
            self.stg_names = stg
            self.stg = [self._init_stg(s) for s in stg]
        else:
            self.stg_names = []
            self.stg = None

    def audio_features(self):
        if self.audio is None: return {}

        features = {'audio': self.audio.copy(), 'sr': self.sr}
        features.update({sname: func(self.audio, self.sr)
            for sname, func in zip(self.stg_names, self.stg)})
        return features

def librosa_stg(func):
    if func.__name__ in LibrosaContext.stg_funcs:
        raise ValueError(f'Duplicate Function Name {func.__name__}')

    LibrosaContext.stg_funcs.update({func.__name__: func})
    return func

def librosa_stg_meta(func):
    if func.__name__ in LibrosaContext.stg_meta_funcs:
        raise ValueError(f'Duplicate Function Name {func.__name__}')

    LibrosaContext.stg_meta_funcs.update({func.__name__: func})
    return func

@librosa_stg_meta
def rmse(audio, sr, frame=DEFAULT_FRAME_LEN, hop=DEFAULT_HOP_LEN):
    frame = int(frame)
    hop = int(hop)

    # Do not pad the frame
    return librosa.feature.rms(y=audio, frame_length=frame,
        hop_length=hop, center=False)

@librosa_stg
def stempo(audio, sr):
    onset_env = librosa.onset.onset_strength(audio, sr)
    return librosa.beat.tempo(onset_envelope=onset_env, sr=sr)

@librosa_stg
def dtempo(audio, sr):
    onset_env = librosa.onset.onset_strength(audio, sr)
    return librosa.beat.tempo(onset_envelope=onset_env, sr=sr,
        aggregate=None)

@librosa_stg_meta
def gramtempo(audio, sr, hop=512):
    hop = int(hop)
    onset_env = librosa.onset.onset_strength(audio, sr)
    return librosa.feature.tempogram(onset_envelope=onset_env, sr=sr,
        hop_length=hop, center=False)

@librosa_stg_meta
def pitchyin(audio, sr, frame=DEFAULT_FRAME_LEN, hop=DEFAULT_HOP_LEN, thres=0.8):
    frame = int(frame)
    hop = int(hop)
    thres = float(thres)

    fmin = librosa.note_to_hz('C2')
    fmax = librosa.note_to_hz('C7')

    return librosa.yin(audio, fmin=fmin, fmax=fmax, sr=sr,
        frame_length=frame, hop_length=hop, trough_threshold=thres, center=False)

@librosa_stg_meta
def pitchpyin(audio, sr, frame=DEFAULT_FRAME_LEN, hop=DEFAULT_HOP_LEN):
    frame = int(frame)
    hop = int(hop)

    fmin = librosa.note_to_hz('C2')
    fmax = librosa.note_to_hz('C7')

    f0, _, _ = librosa.pyin(audio, fmin=fmin, fmax=fmax, sr=sr,
        frame_length=frame, hop_length=hop, center=False)
    
    return f0

DEFAULT_N_MELS = 128
@librosa_stg_meta
def grammel(audio, sr, frame=DEFAULT_FRAME_LEN, hop=DEFAULT_HOP_LEN, n_mels=DEFAULT_N_MELS):
    frame = int(frame)
    hop = int(hop)
    n_mels = int(n_mels)

    S = librosa.feature.melspectrogram(y=audio, sr=sr,
        n_fft=frame, hop_length=hop,n_mels=n_mels, center=False)
    
    return librosa.power_to_db(S, ref=np.max)

if __name__ == '__main__':
    ctx = LibrosaContext(stg=['rmse_1024_512'])
    print(ctx.audio_features())