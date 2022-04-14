import os
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, List

from .FeatureBundle import AudioFeatureBundle

class PlotterError(Exception):
    pass

class FeaturePlotter(object):
    plot_func = {}
    def __init__(self, audio:Optional[str]=None, 
        fb:Optional[AudioFeatureBundle]=None, plots:List[str]=[]):
        super(FeaturePlotter, self).__init__()

        self.plotdir = './plots'
        self.fb = fb
        self.plots = plots
        if audio is not None:
            self.audio = self.set_audio(audio)
        else:
            self.audio = None
    
    def set_audio_feature_bundle(self, fb:AudioFeatureBundle) -> None:
        self.fb = fb
    
    def set_audio(self, audio:str) -> None:
        self.audio, _ = librosa.load(audio, sr=None)
    
    def set_plots(self, plots:List[str]) -> None:
        self.plots = list(filter(lambda p: p in FeaturePlotter.plot_func, plots))

    # HACK: improve this API
    def plot_feature(self, ax:plt.Axes, plots:List[str]=[], data:Optional[AudioFeatureBundle]=None) -> None:
        ax.cla()
        if len(plots) == 0:
            plots = self.plots
        else:
            plots = list(filter(lambda p: p in FeaturePlotter.plot_func, plots))

        for p in self.plots:
            print(f'drawing plots {p}')
            if data is None:
                FeaturePlotter.plot_func[p](ax, self.audio, self.fb)
            else:
                FeaturePlotter.plot_func[p](ax, self.audio, data)

    def save_plots(self):
        os.makedirs(self.plotdir, exist_ok=True)
        audio_data, _ = librosa.load(self.audio, sr=self.fm.sample_rate())

        nrow = 2
        ncol = (len(self.plots)+nrow-1) // nrow
        fig, ax = plt.subplots(nrow, ncol, figsize=(10, 10))
        for p, a in zip(self.plots, ax.ravel()[:len(self.plots)]):
            FeaturePlotter.plot_func[p](a, audio_data, self.fb)

        plt.savefig(os.path.join(self.plotdir, 'feature_plots.png'))

    @classmethod
    def plot(cls, func):
        name = func.__name__
        if name in cls.plot_func:
            raise ValueError(f'Duplicated Plot Function Name {name}')

        cls.plot_func.update({name: func})
        return func