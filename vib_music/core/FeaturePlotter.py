import os
import librosa
import librosa.display
import matplotlib.pyplot as plt

from .FeatureBundle import AudioFeatureBundle

class FeaturePlotter(object):
    plot_func = {}
    def __init__(self, audio:str, fb:AudioFeatureBundle, plots=[]):
        super(FeaturePlotter, self).__init__()

        self.plotdir = './plots'
        self.audio_name = audio
        self.fb = fb
        self.plots = plots

    def save_plots(self):
        os.makedirs(self.plotdir, exist_ok=True)
        audio_data, _ = librosa.load(self.audio_name, sr=self.fm.sample_rate())

        nrow = 2
        ncol = (len(self.plots)+nrow-1) // nrow
        fig, ax = plt.subplots(nrow, ncol, figsize=(10, 10))
        for p, a in zip(self.plots, ax.ravel()[:len(self.plots)]):
            FeaturePlotter.plot_func[p](a, audio_data, self.fm)

        plt.savefig(os.path.join(self.plotdir, 'feature_plots.png'))

    @classmethod
    def plot(cls, func):
        name = func.__name__
        if name in cls.plot_func:
            raise ValueError(f'Duplicated Plot Function Name {func.__func__}')

        cls.plot_func.update({name: func})
        return func