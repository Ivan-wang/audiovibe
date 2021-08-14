import os
import numpy as np
import glob
import pickle
import librosa
import librosa.display
import matplotlib.pyplot as plt

class PlotContext(object):
    stgs = {}
    def __init__(self, datadir, audio, plot_kwargs={}):
        super(PlotContext, self).__init__()

        self.plotdir = './plots'
        self.audio_name = audio
        self.datadir = datadir
        self.plot_kwargs = plot_kwargs

    def save_plots(self):
        os.makedirs(self.plotdir, exist_ok=True)

        audio = os.path.basename(self.audio_name).split('.')[0]
        vibrations = glob.glob(f'{self.datadir}/{audio}/*.pkl')
        vibrations = {os.path.basename(v).split('.')[0] : v for v in vibrations}
        with open(vibrations['meta'], 'rb') as f:
            meta = pickle.load(f)

        audio_data, _ = librosa.load(self.audio_name, sr=meta['sr'])
        for vib in meta['vibrations']:
            with open(vibrations[vib], 'rb') as f:
                vib_data = pickle.load(f)
            PlotContext.stgs[vib](self.plotdir, audio_data, meta,
                vib_data, **self.plot_kwargs.get(vib, {}))

    @classmethod
    def register_plot(cls, func):
        if func.__name__ in cls.stgs:
            raise ValueError(f'Duplicated Plot Function Name {func.__func__}')

        cls.stgs.update({func.__name__: func})
        return func

@PlotContext.register_plot
def beatplp(plotdir, audio, meta, beat_data, vib_func=None):
    # recover feature extraction environment
    sr = meta['sr']
    hop_len = meta['len_hop']
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop_len)

    # mel-spectrogram for reference
    melspec = librosa.feature.melspectrogram(y=audio, sr=sr, hop_length=hop_len)

    nrows = 2 if vib_func is None else 3
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
    if vib_func is not None:
        amp, freq = vib_func(pulse)
        ax[2].plot(times, amp, label='Vibration AMP')
        ax[2].plot(times, freq, label='Vibration FREQ')
        ax[2].set(title='Vibration Signals')
        ax[2].legend()

    fig.savefig(os.path.join(plotdir, 'beatplp.jpg'))