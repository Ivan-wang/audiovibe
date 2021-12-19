import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import FigureCanvasAgg, FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

import librosa
import pickle
import numpy as np
from tkinter import *
from tkinter import filedialog
from matplotlib.figure import Figure
from backend import load_music
# from AtomicWaveFrame import WaveDBFrame
# from AtomicWaveFrame import load_database

class MusicFrame(LabelFrame):
    def __init__(self, root=None, **args):
        LabelFrame.__init__(self, root, text='Load music', **args)

        self.musicName = StringVar()

        self.musicPathEntry = Entry(self, textvariable=self.musicName)
        self.browseBtn = Button(self, text='Browse...', command=self.__ask_music_name)
        self.loadBtn = Button(self, text='Load')

        self.musicPathEntry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        self.browseBtn.pack(side=LEFT, padx=5)
        self.loadBtn.pack(side=LEFT, padx=5)

    def __ask_music_name(self):
        self.musicName.set(filedialog.askopenfilename(
            initialdir='.'
        ))

from backend import draw_rmse

class MusicRMSEFrame(LabelFrame):
    def __init__(self, root=None, **args):
        LabelFrame.__init__(self, root, text='RMSE Waveform', **args)

        self.figure = Figure(figsize=(12, 3))
        self.ax = self.figure.subplots(1, 1)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()

        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=YES)

    def draw_rmse(self, audio, fm):
        draw_rmse(audio, fm, self.ax)

class _CurveFrame(LabelFrame):
    def __init__(self, root=None, text='', **args):
        LabelFrame.__init__(self, root, text=text, **args)

        self.figure = Figure(figsize=(3, 3))
        self.ax = self.figure.subplots(1, 1)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=YES, padx=5)

class VibHistFrame(_CurveFrame):
    def __init__(self, root=None, **args):
        _CurveFrame.__init__(self, root, text='Histogram', **args)

    def draw_hist(self, data):
        self.ax.cla()
        bins, _, _ = self.ax.hist(data, bins=256, range=(0., 1), density=False)

        self.ax.set_xlim((0, 1))
        self.ax.set_xticks(np.linspace(0, 1, 5), labels=np.linspace(0, 1, 5))
        self.ax.set_xticks(np.linspace(0, 1, 50), minor=True)
        self.ax.set_ylim((0, max(bins)//10 * 10))
        self.ax.set_yticks(np.linspace(0, (max(bins)+9)//10 * 10, 5),
                           labels=np.linspace(0, (max(bins)+9)//10 * 10, 5))
        self.ax.set_yticks(np.linspace(0, (max(bins)+9)//10 * 10, 50), minor=True)
        self.ax.set_xticklabels(self.ax.get_xticklabels(), fontsize=8)
        self.ax.set_xticklabels(self.ax.get_xticklabels(), fontsize=8)
        self.ax.set_yticklabels(self.ax.get_yticklabels(), fontsize=8)

        self.ax.grid(which='both')
        self.ax.grid(which='minor', alpha=0.2)
        self.ax.grid(which='major', alpha=0.5)

class CurveFrame(_CurveFrame):
    def __init__(self, root=None, **args):
        _CurveFrame.__init__(self, root, text='Curve', **args)

        self.line, = self.ax.plot(np.linspace(0, 1, 1000), np.linspace(0, 1, 1000))

        self.ax.set_xticks(np.linspace(0, 1, 5), labels=np.linspace(0, 1, 5))
        self.ax.set_xticks(np.linspace(0, 1, 50), minor=True)
        self.ax.set_yticks(np.linspace(0, 1, 5), labels=np.linspace(0, 1, 5))
        self.ax.set_yticks(np.linspace(0, 1, 50), minor=True)
        self.ax.set_xticklabels(self.ax.get_xticklabels(), fontsize=8)
        self.ax.set_yticklabels(self.ax.get_xticklabels(), fontsize=8)

        self.ax.grid(which='both')
        self.ax.grid(which='minor', alpha=0.2)
        self.ax.grid(which='major', alpha=0.5)

    def draw_curve(self, data):
        self.line.set_ydata(data)
        self.canvas.draw()

from backend import TransformQueue, Transform

class TransformParamFrame(LabelFrame):
    def __init__(self, root=None, text='', params=[], **args):
        LabelFrame.__init__(self, root, text=text, **args)

        self.paramVars = []
        self.paramSpinBox = []
        self.paramLabels = []
        self.enableBtn = Radiobutton(self, value=text)

        for p, r in params:
            self.paramVars.append(DoubleVar())
            self.paramLabels.append(
                Label(self, text=p)
            )
            self.paramSpinBox.append(
                Spinbox(self, from_=r[0], to=r[1], increment=r[2],
                        width=6, textvariable=self.paramVars[-1])
            )

        self.enableBtn.pack(side=LEFT)
        for l, s in zip(self.paramLabels, self.paramSpinBox):
            l.pack(side=LEFT, padx=5, pady=5)
            s.pack(side=LEFT, padx=5, pady=5)

    def set_params(self, *args):
        for v, arg in zip(self.paramVars, args):
            v.set(arg)

    def get_params(self):
        return [v.get() for v in self.paramVars]

    def enable_frame(self):
        for s in self.paramSpinBox:
            s.config(state='enable')

    def disable_frame(self):
        for s in self.paramSpinBox:
            s.config(state='disable')

class TransformFrame(LabelFrame):
    def __init__(self, root=None, **args):
        LabelFrame.__init__(self, root, text='Transforms', **args)

        self.opQueueFrame = LabelFrame(self, text='Trans. Queue')
        self.opQueueListbox = Listbox(self.opQueueFrame, selectmode=SINGLE, exportselection=False)
        buttonFrame = Frame(self.opQueueFrame)
        self.addBtn = Button(buttonFrame, text='add')
        self.delBtn = Button(buttonFrame, text='del')
        self.moveUpBtn = Button(buttonFrame, text='up')
        self.moveDownBtn = Button(buttonFrame, text='down')

        self.transEditFrame = LabelFrame(self, text='Trans. Params')
        self.transParamFrames = []
        params = [
            ('linear', [('start', (0, 1, 0.01)), ('end', (0, 1, 0.01))]),
            ('norm', [('mean', (0, 1, 0.01)), ('std', (0, 1, 0.001))]),
            ('power', [('power', (0, 2, 0.01))]),
            ('shift', [('shift', (0, 1, 0.01))])
        ]
        for t, p in params:
            self.transParamFrames.append(TransformParamFrame(self.transEditFrame, t, p))
        applyFrame = Frame(self.transEditFrame)
        self.applyBtn = Button(applyFrame, text='Apply Transform')

        self.addBtn.grid(row=0, column=0, sticky=EW)
        self.delBtn.grid(row=0, column=1, sticky=EW)
        self.moveUpBtn.grid(row=1, column=0, sticky=EW)
        self.moveDownBtn.grid(row=1, column=1, sticky=EW)
        buttonFrame.grid_columnconfigure(0, weight=1)
        buttonFrame.grid_columnconfigure(1, weight=1)
        buttonFrame.grid_rowconfigure(0, weight=1)
        buttonFrame.grid_rowconfigure(1, weight=1)

        self.opQueueListbox.pack(side=TOP, fill=BOTH, expand=YES, padx=5)
        buttonFrame.pack(side=TOP, fill=BOTH, pady=5, padx=5)
        self.opQueueFrame.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        for f in self.transParamFrames:
            f.pack(side=TOP, fill=X, expand=YES, pady=5, padx=5)
        self.applyBtn.pack(side=RIGHT, padx=5, pady=5)
        applyFrame.pack(side=TOP, fill=X, expand=YES)
        self.transEditFrame.pack(side=LEFT, padx=5, pady=5)


class VibTuneFrame(LabelFrame):
    def __init__(self, root=None, **args):
        LabelFrame.__init__(self, root, text='Tune Vibration Mode', **args)

        self.histFrame = VibHistFrame(self)
        self.curveFrame = CurveFrame(self)
        self.transFrame = TransformFrame(self)

        self.histFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5)
        self.curveFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5)
        self.transFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5, expand=YES)

    def draw_data(self, data):
        self.histFrame.draw_hist(data)


class VibModeFrame(Frame):
    def __init__(self, root):
        Frame.__init__(self, root)

        self.audio, self.fm = self.__load_music()
        self.loadMusicFrame = MusicFrame(self)
        self.rmseFrame = MusicRMSEFrame(self)
        self.tuneFrame = VibTuneFrame(self)
        # self.waveDB = load_database()

        # self.waveDFrame = WaveDBFrame(self, self.waveDB, height=200)

        self.loadMusicFrame.pack(side=TOP, fill=X, pady=5, padx=5)
        self.rmseFrame.pack(side=TOP, fill=X, pady=5, padx=5)
        self.tuneFrame.pack(side=TOP, fill=X, expand=YES, pady=5, padx=5)

        self.rmseFrame.draw_rmse(self.audio, self.fm)
        self.tuneFrame.draw_data(self.fm.feature_data('rmse'))

    def __load_music(self):
        audio, fm = load_music()
        return audio, fm


if __name__ == '__main__':
    root = Tk()
    f = VibModeFrame(root)
    f.pack()
    root.mainloop()
