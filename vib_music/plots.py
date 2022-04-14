import os
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt

from .core import AudioFeatureBundle
from .core import FeaturePlotter

@FeaturePlotter.plot
def waveform(ax:plt.Axes, audio:np.ndarray, fb:AudioFeatureBundle):
    sr = fb.sample_rate()
    librosa.display.waveplot(audio, sr=sr, ax=ax)
    ax.set_title('Time Domain Waveform')

@FeaturePlotter.plot
def wavermse(ax:plt.Axes, audio:np.ndarray, fb:AudioFeatureBundle):
    sr = fb.sample_rate()
    hop_len = fb.frame_len()

    librosa.display.waveplot(audio, sr=sr, ax=ax)

    rmse = fb.feature_data('rmse')
    times = librosa.times_like(rmse, sr=sr, hop_length=hop_len)

    ax.plot(times, rmse, 'r')
    ax.set_xlim(xmin=0, xmax=times[-1])
    ax.set_title('RMSE Waveform')

@FeaturePlotter.plot
def melspec(ax:plt.Axes, audio:np.ndarray, fb:AudioFeatureBundle):
    # recover feature extraction environment
    sr = fb.sample_rate()
    hop_len = fb.frame_len()

    melspec = fb.feature_data('melspec')
    if melspec is not None:
        fmax = fb.feature_data('melspec', 'fmax')
    else:
        # melspec is not one of the features
        melspec = librosa.feature.melspectrogram(y=audio, sr=sr, hop_length=hop_len)
        fmax = None

    librosa.display.specshow(
        librosa.power_to_db(melspec, ref=np.max), sr=sr, fmax=fmax,
            x_axis='time', y_axis='mel', ax=ax)
    ax.set(title='Mel spectrogram')
    ax.label_outer()

@FeaturePlotter.plot
def contrastspec(ax:plt.Axes, audio:np.ndarray, fb:AudioFeatureBundle):
    constrast = fb.feature_data('contrastspec')
    librosa.display.specshow(
        constrast, x_axis='time', ax=ax
    )
    ax.set(ylabel='Frequency bands', title='Spectral Contrast')

@FeaturePlotter.plot
def beatplo(ax:plt.Axes, audio:np.ndarray, fb:AudioFeatureBundle):
    # fig, ax = plt.subplots(nrows=nrows, sharex=True, figsize=(10, 10))
    # draw pulse and beats points
    sr = fb.sample_rate()
    hop_len = fb.frame_len()
    min_tempo = fb.feature_data('beatplp', 'tempo_min')
    max_tempo = fb.feature_data('beatplp', 'tempo_max')
    pulse = fb.feature_data('beatplp')

    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop_len)
    beats = np.flatnonzero(librosa.util.localmax(pulse))
    times = librosa.times_like(pulse, sr=sr, hop_length=hop_len)

    ax.plot(librosa.times_like(onset_env, sr=sr, hop_length=hop_len),
            librosa.util.normalize(onset_env),
            label='Onset strength')
    ax.plot(librosa.times_like(pulse, sr=sr, hop_length=hop_len),
        librosa.util.normalize(pulse),
        label='Predominant local pulse (PLP)')
    ax.vlines(times[beats], 0, 1, alpha=0.5, color='r', linestyle='--', label='PLP Beats')
    ax.set(title=f'Uniform tempo prior [{min_tempo}, {max_tempo}]')
    ax.label_outer()
    ax.legend()

@FeaturePlotter.plot
def vibration_adc(ax:plt.Axes, audio:np.ndarray, fb:AudioFeatureBundle):
    sr = fb.sample_rate()
    hop_len = fb.frame_len()
    vibration_seq = fb.build_vibration()
    times = librosa.times_like(vibration_seq, sr=sr, 
        hop_length=hop_len)
    ax.plot(times, vibration_seq, label='Sigmal AMP')
    ax.set(title='ADC Vibration Signals')
    ax.set_xlim(xmin=0, xmax=times[-1])
    ax.legend()

@FeaturePlotter.plot
def picth(ax:plt.Axes, audio:np.ndarray, fb:AudioFeatureBundle):
    sr = fb.sample_rate()
    hop_len = fb.frame_len()
    pitch_t = 'pitchyin' if 'pitchyin' in fb.feature_names() else 'pitchpyin'
    win_len = fb.feature_data(pitch_t, 'len_window')

    D = librosa.amplitude_to_db(
        np.abs(librosa.stft(y=audio, hop_length=hop_len,
            n_fft=win_len)), ref=np.max)

    img = librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', ax=ax)
    ax.set(title='Pitch Frequency Estimation')
    # fig.colorbar(img, ax=ax[0], format='%+2.f dB')

    f0 = fb.feature_data(pitch_t)
    times = librosa.times_like(f0, sr=sr, hop_length=hop_len, n_fft=win_len)
    ax.plot(times, f0, color='cyan', linewidth=3, label='F0')
    ax.legend(loc='upper right')

@FeaturePlotter.plot
def chromaspec(ax:plt.Axes, audio:np.ndarray, fb:AudioFeatureBundle):
    sr = fb.sample_rate()
    hop_len = fb.frame_len()

    chroma_t = 'chromastft' if 'chromastft' in fb.feature_names() else 'chromacqt'
    chroma = fb.feature_data(chroma_t)
    chroma = chroma.T # feature extraction puts time at 1st axis. now transpose it.
    librosa.display.specshow(chroma, sr=sr, y_axis='chroma', x_axis='time', ax=ax)

