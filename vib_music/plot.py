import os
import numpy as np
import glob
import pickle
import librosa
import librosa.display
import matplotlib.pyplot as plt

from .FeatureManager import FeatureManager
class PlotManager(object):
    plot_func = {}
    def __init__(self, audio, fm, plots=[]):
        super(PlotManager, self).__init__()

        self.plotdir = './plots'
        self.audio_name = audio
        self.fm = fm
        self.plots = plots

    def save_plots(self):
        os.makedirs(self.plotdir, exist_ok=True)
        audio_data, _ = librosa.load(self.audio_name, sr=self.fm.sample_rate())

        nrow = 2
        ncol = (len(self.plots)+nrow-1) // nrow
        fig, ax = plt.subplots(nrow, ncol, figsize=(10, 10))
        for p, a in zip(self.plots, ax.ravel()[:len(self.plots)]):
            PlotManager.plot_func[p](a, audio_data, self.fm)

        plt.savefig(os.path.join(self.plotdir, 'feature_extraction.png'))

    @classmethod
    def plot(cls, func):
        name = func.__name__
        if name in cls.plot_func:
            raise ValueError(f'Duplicated Plot Function Name {func.__func__}')

        cls.plot_func.update({name: func})
        return func

@PlotManager.plot
def melspec(ax, audio, fm:FeatureManager):
    # recover feature extraction environment
    sr = fm.sample_rate()
    hop_len = fm.frame_len()
    # mel-spectrogram for reference
    melspec = librosa.feature.melspectrogram(y=audio, sr=sr, hop_length=hop_len)

    librosa.display.specshow(
        librosa.power_to_db(melspec, ref=np.max), sr=sr,
            x_axis='time', y_axis='mel', ax=ax)
    ax.set(title='Mel spectrogram')
    ax.label_outer()

@PlotManager.plot
def beatplp(ax, audio, fm:FeatureManager):
    # fig, ax = plt.subplots(nrows=nrows, sharex=True, figsize=(10, 10))
    # draw pulse and beats points
    sr = fm.sample_rate()
    hop_len = fm.frame_len()
    min_tempo = fm.feature_data('beatplp', 'tempo_min')
    max_tempo = fm.feature_data('beatplp', 'tempo_max')
    pulse = fm.feature_data('beatplp')

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

@PlotManager.plot
def vibration_drv2605(ax, audio, fm:FeatureManager):
    sr = fm.sample_rate()
    hop_len = fm.frame_len()
    vibration_seq = fm.vibration_sequence()
    amp, freq = vibration_seq[:, 0], vibration_seq[:, 1]
    times = librosa.times_like(amp, sr=sr, hop_length=hop_len)
    ax.plot(times, amp, label='Vibration AMP')
    ax.plot(times, freq, label='Vibration FREQ')
    ax.set(title='Vibration Signals')
    ax.legend()

@PlotManager.plot
def pitch(ax, audio, fm:FeatureManager):
    sr = fm.sample_rate()
    hop_len = fm.frame_len()
    pitch_t = 'pitchyin' if 'pitchyin' in fm.feature_names() else 'pitchpyin'
    win_len = fm.feature_data(pitch_t, 'len_window')

    D = librosa.amplitude_to_db(
        np.abs(librosa.stft(y=audio, hop_length=hop_len,
            n_fft=win_len)), ref=np.max)

    img = librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', ax=ax)
    ax.set(title='Pitch Frequency Estimation')
    # fig.colorbar(img, ax=ax[0], format='%+2.f dB')

    f0 = fm.feature_data(pitch_t)
    times = librosa.times_like(f0, sr=sr, hop_length=hop_len, n_fft=win_len)
    ax.plot(times, f0, color='cyan', linewidth=3, label='F0')
    ax.legend(loc='upper right')

@PlotManager.plot
def chroma(ax, audio, fm:FeatureManager):
    sr = fm.sample_rate()
    hop_len = fm.frame_len()

    chroma_t = 'chromastft' if 'chromastft' in fm.feature_names() else 'chromacqt'
    chroma = fm.feature_data(chroma_t)
    chroma = chroma.T # feature extraction puts time at 1st axis. now transpose it.
    librosa.display.specshow(chroma, sr=sr, y_axis='chroma', x_axis='time', ax=ax)

