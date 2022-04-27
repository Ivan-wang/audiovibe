# 3/2/22
# Fei Tao
# taofei@feathervibe.com
# we define feature functions here

import librosa
import numpy as np
from .FeatureExtractionManager import FeatureExtractionManager


@FeatureExtractionManager.register_vib_meta_stg
def melspec(audio, sr, len_hop, len_window=2048, n_mels=128, fmax=None, **kwargs):
    mel = librosa.feature.melspectrogram(y=audio,
        sr=sr, n_fft=len_window, hop_length=len_hop, n_mels=n_mels, fmax=fmax, power=2.0)
    mel_freq = librosa.mel_frequencies(n_mels=n_mels, fmax=sr//2)
    mel_freq = np.round(mel_freq)
    ret = {'len_window': len_window, 'n_mels': n_mels,
        'fmax': fmax, 'mel_freq': mel_freq, 'data': mel
    }
    return ret


@FeatureExtractionManager.register_vib_meta_stg
def stft(audio, sr, len_hop, len_window=512, **kwargs):
    X = librosa.stft(audio, n_fft=len_window, hop_length=len_hop, win_length=len_window, window='hann',
                     center=True, pad_mode='constant')
    stft_freq = librosa.fft_frequencies(sr=sr, n_fft=len_window)
    ret = {'len_window': len_window, 'data': X, "stft_freq":stft_freq}
    return ret

@FeatureExtractionManager.register_vib_meta_stg
def contrastspec(audio, sr, len_hop, len_window=2048, n_bands=6, band_width=200, use_linear=True, **kwargs):
    contrast = librosa.feature.spectral_contrast(
        y=audio, sr=sr, n_fft=len_window, hop_length=len_hop,
        fmin=band_width, n_bands=n_bands, linear=use_linear
    )
    ret = {'len_window': len_window, 'n_bands': n_bands,
        'band_width': 200, 'use_linear': use_linear, 'data': contrast
    }
    return ret


@FeatureExtractionManager.register_vib_meta_stg
def centroidspec(audio, sr, len_hop, len_window=2048, freqs=None, **kwargs):
    centroid = librosa.feature.spectral_centroid(
        y=audio, sr=sr, n_fft=len_window, hop_length=len_hop,
        freq=freqs
    )

    ret = {'len_window': len_window, 'freqs': freqs,
        'data': centroid
    }
    return ret


@FeatureExtractionManager.register_vib_meta_stg
def beatplp(audio, sr, len_hop, len_frame=300, tempo_min=30, tempo_max=300, **kwargs):
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
def rmse(audio, sr, len_hop, len_window=2048, **kwargs):
    len_window = int(len_window)

    mse = librosa.feature.rms(y=audio, frame_length=len_window,
        hop_length=len_hop, center=True)
    mse = mse.reshape((-1, ))
    ret = {'len_frame': len_window, 'data': mse}

    return ret


@FeatureExtractionManager.register_vib_meta_stg
def pitchyin(audio, sr, len_hop, len_window=2048, fmin='C2', fmax='C7', thres=0.8, **kwargs):
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
def pitchpyin(audio, sr, len_hop, pitch_len_window=2048, fmin='C2', fmax='C7', **kwargs):
    # ### debug print ###
    # print(f"pitch len window is {pitch_len_window}")
    # ######
    len_window = int(pitch_len_window)

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
def chromastft(audio, sr, len_hop, len_window=2048, n_chroma=12, tuning=0.0, **kwargs):
    len_window = int(len_window)
    chroma = librosa.feature.chroma_stft(y=audio, sr=sr, n_fft=len_window,
        n_chroma=n_chroma, tuning=tuning)
    chroma = chroma.T # use time at first axis

    ret = {'len_hop': len_hop, 'len_window': len_window, 'data': chroma}
    return ret


@FeatureExtractionManager.register_vib_meta_stg
def chromacqt(audio, sr, len_hop, fmin='C1', n_chroma=12, tuning=0.0, **kwargs):
    # len_window = int(len_window)
    fmin = librosa.note_to_hz(fmin)
    chroma = librosa.feature.chroma_cqt(y=audio, sr=sr, fmin=fmin,
        n_chroma=n_chroma, tuning=tuning)
    chroma = chroma.T # use time at first axis

    ret = {'len_hop': len_hop, 'fmin': fmin, 'data': chroma}
    return ret