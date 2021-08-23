import os
import numpy as np
import glob
import pickle
import librosa
import librosa.display
import matplotlib.pyplot as plt

class PlotContext(object):
    stgs = {}
    def __init__(self, datadir, audio, vib_mode_func, plots=[]):
        super(PlotContext, self).__init__()

        self.plotdir = './plots'
        self.audio_name = audio
        self.datadir = datadir
        self.vib_mode_func = vib_mode_func
        self.plots = plots

    def save_plots(self):
        os.makedirs(self.plotdir, exist_ok=True)

        audio = os.path.basename(self.audio_name).split('.')[0]
        vibrations = glob.glob(f'{self.datadir}/{audio}/*.pkl')
        vibrations = {os.path.basename(v).split('.')[0] : v for v in vibrations}
        with open(vibrations['meta'], 'rb') as f:
            meta = pickle.load(f)

        audio_data, _ = librosa.load(self.audio_name, sr=meta['sr'])
        feature_bundle = {}
        for vib in meta['vibrations']:
            with open(vibrations[vib], 'rb') as f:
                feature_bundle[vib] = pickle.load(f)

        amp, freq = self.vib_mode_func(feature_bundle)
        feature_bundle.update({
            'amp': amp, 'freq': freq
        })
        for p in self.plots:
            PlotContext.stgs[p](self.plotdir, audio_data, meta, feature_bundle)

    @classmethod
    def register_plot(cls, func):
        name = func.__name__.split('_')[0]
        if name in cls.stgs:
            raise ValueError(f'Duplicated Plot Function Name {func.__func__}')
        
        cls.stgs.update({name: func})
        return func

@PlotContext.register_plot
def beatplp(plotdir, audio, meta, feature_bundle):
    # recover feature extraction environment
    sr = meta['sr']
    hop_len = meta['len_hop']
    beat_data = feature_bundle['beatplp']
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop_len)

    # mel-spectrogram for reference
    melspec = librosa.feature.melspectrogram(y=audio, sr=sr, hop_length=hop_len)

    nrows = 3
    fig, ax = plt.subplots(nrows=nrows, sharex=True, figsize=(10, 10))
    # draw mel-spectrogram
    librosa.display.specshow(
        librosa.power_to_db(melspec, ref=np.max), sr=sr,
            x_axis='time', y_axis='mel', ax=ax[0])
    ax[0].set(title='Mel spectrogram')
    ax[0].label_outer()

    # draw pulse and beats points
    min_tempo = beat_data['tempo_min']
    max_tempo = beat_data['tempo_max']
    pulse = beat_data['data']
    beats = np.flatnonzero(librosa.util.localmax(pulse))
    times = librosa.times_like(pulse, sr=sr, hop_length=hop_len)

    ax[1].plot(librosa.times_like(onset_env, sr=sr, hop_length=hop_len),
            librosa.util.normalize(onset_env),
            label='Onset strength')
    ax[1].plot(librosa.times_like(pulse, sr=sr, hop_length=hop_len),
        librosa.util.normalize(pulse),
        label='Predominant local pulse (PLP)')
    ax[1].vlines(times[beats], 0, 1, alpha=0.5, color='r', linestyle='--', label='PLP Beats')
    ax[1].set(title=f'Uniform tempo prior [{min_tempo}, {max_tempo}]')
    ax[1].label_outer()
    ax[1].legend()

    # draw vibraction function
    amp, freq = feature_bundle['amp'], feature_bundle['freq']
    ax[2].plot(times, amp, label='Vibration AMP')
    ax[2].plot(times, freq, label='Vibration FREQ')
    ax[2].set(title='Vibration Signals')
    ax[2].legend()

    fig.savefig(os.path.join(plotdir, 'beatplp.jpg'))

@PlotContext.register_plot
def pitch_plot(plotdir, audio, meta, feature_bundle):
    sr = meta['sr']
    hop_len = meta['len_hop']
    win_len = feature_bundle['pitch']['len_window']
    D = librosa.amplitude_to_db(
        np.abs(librosa.stft(y=audio, hop_length=hop_len, n_fft=win_len)), ref=np.max)

    fig, ax = plt.subplots(nrows=2, sharex = True, figsize=(10, 5))
    img = librosa.display.specshow(D, x_axis='time', y_axis='log', ax=ax[0])
    ax.set(title='Pitch Frequency Estimation')
    fig.colorbar(img, ax=ax[0], format='%+2.f dB')

    f0 = feature_bundle['pitch']['data']
    times = librosa.times_like(f0, sr=sr, hop_length=hop_len)
    ax[0].plot(times, f0, color='cyan', linewitdh=3)

    amp, freq = feature_bundle['amp'], feature_bundle['freq']
    ax[2].plot(times, amp, label='Vibration AMP')
    ax[2].plot(times, freq, label='Vibration FREQ')
    ax[2].set(title='Vibration Signals')
    ax[2].legend()

    fig.savefig(os.path.join(plotdir, 'pitch.jpg'))

@PlotContext.register_plot
def chrome_plot(plotdir, audio, meta, feature_bundle):
    sr = meta['sr']
    hop_len = meta['len_hop']
    melspec = librosa.feature.melspectrogram(y=audio, sr=sr, hop_length=hop_len)

    nrows = 3
    fig, ax = plt.subplots(nrows=nrows, sharex=True, figsize=(10, 10))
    # draw mel-spectrogram
    librosa.display.specshow(
        librosa.power_to_db(melspec, ref=np.max), sr=sr,
            x_axis='time', y_axis='mel', ax=ax[0])
    ax[0].set(title='Mel spectrogram')
    ax[0].label_outer()

    chroma = feature_bundle['chroma']['data']
    librosa.display.specshow(chroma, y_axis='chroma', x_axis='time', ax=ax[1])

    amp, freq = feature_bundle['amp'], feature_bundle['freq']
    times = librosa.times_like(amp, sr=sr, hop_length=hop_len)
    ax[2].plot(times, amp, label='Vibration AMP')
    ax[2].plot(times, freq, label='Vibration FREQ')
    ax[2].set(title='Vibration Signals')
    ax[2].legend()

    fig.savefig(os.path.join(plotdir, 'chroma.jpg'))

