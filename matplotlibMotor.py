import os
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt

from librosaContext import DEFAULT_FRAME_LEN
from librosaContext import DEFAULT_HOP_LEN
from librosaContext import DEFAULT_WIN_LEN
from utils import get_feature

from boardInvoker import Motor
class MatplotlibMotor(Motor):
    alias = 'plot'
    commands = {}
    def __init__(self, vibration_t, save_dir='.'):
        super(MatplotlibMotor, self).__init__()
        self.save_dir = save_dir
        for k in self.vibration:
            self.vibration[k] = []
        
        # by default, store the audio
        if 'audio' not in self.vibration_t:
            self.vibration_t.append('audio')
            self.vibration['audio'] = []
        
        # add 'sr' in vibration_t to catch the sr
        if 'sr' not in self.vibration_t:
            self.vibration_t.append['sr']
        self.sr = None

    def on_start(self):
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)

    def on_update(self, vib_t, vib):
        if vib_t == 'sr':
            if self.sr is None:
                self.sr = vib
            return
        
        self.vibration_t[vib_t].append(vib)

    def on_running(self):
        return super().on_running()

    def on_end(self):
        for name in self.vibration:
            if name == 'audio':
                # need more efforts to recover the audio
                audios = self.vibration[name]
                step = DEFAULT_FRAME_LEN-DEFAULT_HOP_LEN

                audios = [s[:step] for s in audios] + [audios[-1]]
                self.vibration[name] = np.concatenate(audios, axis=-1)
            else:
                self.vibration[name] = np.concatenate(self.vibration[name], axis=-1)

        self.vibration['sr'] = self.sr

        for name in self.vibration:
            # name = k.split('_')[0] 
            if name in MatplotlibMotor.commands:
                print(f'Command matches feature: {name}')
                MatplotlibMotor.commands[name](self.save_dir, self.vibration)

def matplotlib_commands(alias=[]):
    def command(func):
        alias.append(func.__name__)

        for n in alias:
            if n in MatplotlibMotor.commands:
                raise ValueError(f'Duplicate Function Name {func.__name__}')
            MatplotlibMotor.commands.update({n: func})
        return func
    return command

@matplotlib_commands
def stempo(save_dir, features):
    tempo = features['stempo'].item()
    audio, sr = features['audio'], features['sr']
    hop = DEFAULT_HOP_LEN 

    onset_env = librosa.onset.onset_strength(audio, sr=sr)
    ac = librosa.autocorrelate(onset_env, 2 * sr // hop)
    freqs = librosa.tempo_frequencies(len(ac), sr=sr, hop_length=hop)


    fig, ax = plt.subplots()
    ax.semilogx(freqs[1:], librosa.util.normalize(ac)[1:],
        label='Onset autocorrelation', basex=2)
    ax.axvline(tempo, 0, 1, alpha=0.75, linestyle='--', color='r',
        label=f'Tempo: {tempo:.2f} BPM')
    ax.set(xlabel='Tempo (BPM)', title='Static Tempo Estimation')
    ax.grid(True)
    ax.legend()

    fig.savefig(os.path.join(save_dir, 'stempo_plot.jpg'))

@matplotlib_commands
def dtempo(save_dir, features):
    tg = get_feature(features, prefix='gramtempo')

    dtempo = features['dtempo']
    fig, ax = plt.subplots()
    librosa.display.specshow(tg, x_axis='time',
        y_axis='tempo', cmap='magma', ax=ax)
    ax.plot(librosa.times_like(dtempo), dtempo, color='c', linewidth=1.5,
        linestyle='--', label='Tempo Estimation')
    ax.set(title='Dynamic Tempo Estimation')
    ax.legend()

    plt.savefig(os.path.join(save_dir, 'dtempo_plot.jpg'))

@matplotlib_commands
def rmse(save_dir, features):
    S, phase = librosa.magphase(librosa.stft(features['audio'],
        n_fft=DEFAULT_WIN_LEN, hop_length=DEFAULT_HOP_LEN))
    rmse_f = get_feature(features, prefix='rmse')

    fig, ax = plt.subplots(2, 1)
    ax[0].semilogy(rmse_f.T, label='RMS Energy')
    ax[0].set_xticks([])
    ax[0].set_xlim([0, rmse_f.shape[-1]])
    ax[0].legend(loc='best')
    librosa.display.specshow(librosa.amplitude_to_db(S, ref=np.max),
                             y_axis='log', x_axis='time', ax=ax[1])

    ax[1].set(title='log Power spectrogram')
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'rmse_plot.jpg'))

@matplotlib_commands(['pitchpyin'])
def pitchyin(save_dir, features):
    D = librosa.amplitude_to_db(
        np.abs(librosa.stft(features['audio'])), ref=np.max)

    fig, ax = plt.subplots()
    img = librosa.display.specshow(D, x_axis='time', y_axis='log', ax=ax)
    ax.set(title='fundamental frequency estimation')
    fig.colorbar(img, ax=ax, format="%+2.f dB")
    f0 = get_feature(features, prefix='pitchyin')
    if f0 is None:
        f0 = get_feature(features, prefix='pitchpyin')

    ax.plot(librosa.times_like(f0), f0, label='f0', color='cyan', linewidth=3)
    ax.legend(loc='upper right')

    plt.savefig(os.path.join(save_dir, 'pitch_f0_plot.jpg'))

@matplotlib_commands
def grammel(save_dir, features):
    S_db = get_feature(features, prefix='grammel')
    sr = get_feature(features, k='sr')

    fig, ax = plt.subplots()
    img = librosa.display.specshow(
        S_db, x_axis='time', y_axis='mel', sr=sr, fmax=8000, ax=ax
    )

    fig.colorbar(img, ax=ax, format='%+2.0f dB')
    ax.set(title='Mel-frequency spectrogram')

    plt.save(os.path.join(save_dir, 'mel_spec_plot.jpg'))
