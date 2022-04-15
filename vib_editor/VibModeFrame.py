import sys
from typing import Optional
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

import numpy as np
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from matplotlib.figure import Figure

from .backends import VibModeBackend, Transform
from .utils import launch_vib_with_rmse_transforms

sys.path.append('..')

from vib_music import FeaturePlotter, AudioFeatureBundle


class LibLoadFrame(LabelFrame):
    def __init__(self, master=None, **args):
        LabelFrame.__init__(self, master, text='Load Data', **args)

        self.audioPath = StringVar()
        self.vibModePath = StringVar()

        self.audioPathEntry = Entry(self, textvariable=self.audioPath)
        self.browseBtn = Button(self, text='Browse...', command=self.__ask_audio_path)
        self.loadBtn = Button(self, text='Load')
        self.vibModeEntry = Entry(self, textvariable=self.vibModePath)
        self.browseBtn2 = Button(self, text='Browse...', command=self.__ask_vib_mode_path)
        self.loadBtn2 = Button(self, text='Load')
        self.saveBtn = Button(self, text='save')

        Label(self, text='Audio: ').pack(side=LEFT, padx=5, pady=5)
        self.audioPathEntry.pack(side=LEFT, fill=X, expand=YES, padx=5, pady=5)
        self.browseBtn.pack(side=LEFT, pady=5)
        self.loadBtn.pack(side=LEFT, pady=5)
        ttk.Separator(self).pack(side=LEFT, fill=BOTH)
        Label(self, text='Vib Mode: ').pack(side=LEFT, padx=5, pady=5)
        self.vibModeEntry.pack(side=LEFT, fill=X, expand=YES, padx=5, pady=5)
        self.browseBtn2.pack(side=LEFT, pady=5)
        self.loadBtn2.pack(side=LEFT, pady=5)
        self.saveBtn.pack(side=LEFT, pady=5)

    def __ask_audio_path(self):
        self.audioPath.set(filedialog.askopenfilename(
            initialdir='.'
        ))

    def __ask_vib_mode_path(self):
        self.vibModePath.set(filedialog.askopenfilename(
            initialdir='.'
        ))

    def get_audio_path(self):
        return self.audioPath.get()

    def get_vib_mode_path(self):
        return self.vibModePath.get()


class AudioPlayFrame(LabelFrame):
    def __init__(self, master=None, **args):
        LabelFrame.__init__(self, master, text='Audio Play', **args)

        self.backend = None

        self.atomicDbPath = StringVar()
        self.atomicDbname = StringVar()
        self.atomicWaveName = StringVar()

        self.atomicDbEntry = Entry(self, textvariable=self.atomicDbPath)
        self.browseBtn = Button(self, text='Browse...', command=self.__ask_atomic_db_path)
        self.loadBtn = Button(self, text='Load', command=self.__on_load_atomic_db)
        self.playBtn = Button(self, text='Play')
        self.atomicDataBaseOptMenu = OptionMenu(self, self.atomicDbname, *[''])
        self.atomicWaveOptMenu = OptionMenu(self, self.atomicWaveName, *[''])

        Label(self, text='Atomic Wave DB Path: ').pack(side=LEFT, padx=5, pady=5)
        self.atomicDbEntry.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)
        self.browseBtn.pack(side=LEFT, pady=5)
        self.loadBtn.pack(side=LEFT, pady=5)
        Label(self, text='Atomic Wave DB: ').pack(side=LEFT, padx=5, pady=5)
        self.atomicDataBaseOptMenu.pack(side=LEFT, padx=5, pady=5)
        Label(self, text='Atomic Wave: ').pack(side=LEFT, padx=5, pady=5)
        self.atomicWaveOptMenu.pack(side=LEFT, padx=5, pady=5)
        self.playBtn.pack(side=LEFT, pady=5, padx=5)

        self.__lock_atomic_wave_options()
        self.playBtn.configure(state='disable')

    def set_backend(self, backend:VibModeBackend):
        self.backend = backend

    def __ask_atomic_db_path(self):
        self.atomicDbPath.set(filedialog.askopenfilename(
            initialdir='.'
        ))

    def __lock_atomic_wave_options(self):
        self.atomicDataBaseOptMenu.configure(state='disable')
        self.atomicWaveOptMenu.configure(state='disable')

    def __unlock_atomic_wave_options(self):
        self.atomicDataBaseOptMenu.configure(state='normal')
        self.atomicWaveOptMenu.configure(state='normal')

    def __on_load_atomic_db(self):
        self.backend.load_atomic_wave_db(self.atomicDbPath.get())

        atomicDbnames = self.backend.atomic_waves().list_atomic_family_name()
        self.__unlock_atomic_wave_options()

        self.atomicDbname.set('')
        self.atomicDataBaseOptMenu['menu'].delete(0, END)
        for c in atomicDbnames:
            self.atomicDataBaseOptMenu['menu'].add_command(label=c, command=lambda x=c: self.__on_atomic_db_change(x))
        self.__on_atomic_db_change(atomicDbnames[0])

    def __on_atomic_db_change(self, db):
        self.atomicDbname.set(db)

        self.atomicWaveOptMenu['menu'].delete(0, END)
        self.atomicWaveName.set('')
        self.playBtn.configure(state='disable')

        if db == '':
            atomicWaveNames = []
        else:
            atomicWaveNames = self.backend.atomic_waves().list_atomic_wave_names(db)

        for c in atomicWaveNames:
            self.atomicWaveOptMenu['menu'].add_command(label=c, command=tk._setit(self.atomicWaveName, c))

        if len(atomicWaveNames) > 0:
            self.atomicWaveName.set(atomicWaveNames[0])
            self.playBtn.configure(state='normal')

    def get_atomic_wave(self):
        db = self.atomicDbname.get()
        wave = self.atomicWaveName.get()

        if db == 'none' or wave == 'none':
            return None
        else:
            return self.backend.atomic_waves().get_atomic_wave(db, wave)


class AudioRMSEFrame(LabelFrame):
    def __init__(self, root=None, **args):
        LabelFrame.__init__(self, root, text='RMSE Waveform', **args)

        self.figure = Figure(figsize=(12, 3))
        self.ax = self.figure.subplots(1, 1)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()

        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=YES)

    def draw_rmse(self, plotter:FeaturePlotter, data:AudioFeatureBundle) -> None:
        print(f'AudioRMSE drawing...')
        plotter.plot_feature(self.ax, ['waveform', 'wavermse'], data)

        self.ax.grid(which='both')
        self.ax.grid(which='minor', alpha=0.2)
        self.ax.grid(which='major', alpha=0.5)

        self.canvas.draw()
    
class _CurveFrame(LabelFrame):
    def __init__(self, master=None, text='', **args):
        LabelFrame.__init__(self, master, text=text, **args)

        self.figure = Figure(figsize=(3, 3))
        self.ax = self.figure.subplots(1, 1)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=YES, padx=5)


class VibHistFrame(_CurveFrame):
    def __init__(self, master=None, **args):
        _CurveFrame.__init__(self, master, text='Histogram', **args)

    def draw_hist(self, data):
        self.ax.cla()
        bins, _, _ = self.ax.hist(data, bins=256, range=(0., 1), density=False)

        self.ax.set_xlim((0, 1))
        self.ax.set_xticks(np.linspace(0, 1, 5))
        self.ax.set_xticks(np.linspace(0, 1, 50), minor=True)
        self.ax.set_xticklabels(['0', '64', '128', '191', '255'])

        self.ax.set_ylim((0, max(bins) // 10 * 10))
        self.ax.set_yticks(np.linspace(0, (max(bins) + 9) // 10 * 10, 5))
        self.ax.set_yticklabels(np.linspace(0, (max(bins) + 9) // 10 * 10, 5))
        self.ax.set_yticks(np.linspace(0, (max(bins) + 9) // 10 * 10, 50), minor=True)

        self.ax.set_xticklabels(self.ax.get_xticklabels(), fontsize=8)
        self.ax.set_yticklabels(self.ax.get_yticklabels(), fontsize=8)

        self.ax.grid(which='both')
        self.ax.grid(which='minor', alpha=0.2)
        self.ax.grid(which='major', alpha=0.5)

        self.canvas.draw()


class CurveFrame(_CurveFrame):
    def __init__(self, master=None, **args):
        _CurveFrame.__init__(self, master, text='Curve', **args)

        self.line, = self.ax.plot(np.linspace(0, 1, 1000), np.linspace(0, 1, 1000))

        self.ax.set_xticks(np.linspace(0, 1, 5))
        self.ax.set_xticks(np.linspace(0, 1, 50), minor=True)
        self.ax.set_xticklabels(np.linspace(0, 1, 5))
        # self.ax.set_xticklabels(['0', '64', '128', '191', '255'])
        self.ax.set_yticks(np.linspace(0, 1, 5))
        self.ax.set_yticks(np.linspace(0, 1, 50), minor=True)
        self.ax.set_yticklabels(np.linspace(0, 1, 5))
        # self.ax.set_xticklabels(['0', '64', '128', '191', '255'])
        self.ax.set_xticklabels(self.ax.get_xticklabels(), fontsize=8)
        self.ax.set_yticklabels(self.ax.get_xticklabels(), fontsize=8)

        self.ax.grid(which='both')
        self.ax.grid(which='minor', alpha=0.2)
        self.ax.grid(which='major', alpha=0.5)

    def draw_curve(self, data):
        self.line.set_ydata(data)
        self.canvas.draw()


class TransformFrame(LabelFrame):
    def __init__(self, master=None, **args):
        LabelFrame.__init__(self, master, text='Transforms', **args)

        self.transName = StringVar()

        self.transEditFrame = LabelFrame(self, text='Trans. Params')
        self.transParamFrames = {}
        self.transParamVars = {}
        params = [
            ('linear', [('slope', (0, 1, 0.01)), ('bias', (0, 1, 0.01))]),
            ('norm-std', [('mean', (0, 1, 0.01)), ('std', (0, 1, 0.001))]),
            ('power', [('power', (0, 2, 0.01))]),
            ('log', [('gamma', (0, 1, 0.01))]),
            ('norm-min-max', [('min', (0, 1, 0.01)), ('max', (0, 1, 0.01))])
        ]
        for t, p in params:
            frame, vars = self.__build_trans_param_frame(name=t, params=p)
            self.transParamFrames.update({t: frame})
            self.transParamVars.update({t: vars})

        self.transName.set(params[0][0])
        self.__on_transform_selection_change()

        applyFrame = Frame(self.transEditFrame)
        self.applyBtn = Button(applyFrame, text='Apply Transform')

        self.opQueueFrame = LabelFrame(self, text='Trans. Queue')
        self.opQueueListbox = Listbox(self.opQueueFrame, selectmode=SINGLE, exportselection=False)
        buttonFrame = Frame(self.opQueueFrame)
        self.addBtn = Button(buttonFrame, text='add')
        self.delBtn = Button(buttonFrame, text='del')
        self.moveUpBtn = Button(buttonFrame, text='up')
        self.moveDownBtn = Button(buttonFrame, text='down')

        for f in self.transParamFrames:
            self.transParamFrames[f].pack(side=TOP, fill=X, expand=YES, pady=5, padx=5)

        self.applyBtn.pack(side=RIGHT, padx=5, pady=5)
        applyFrame.pack(side=TOP, fill=X, expand=YES)
        self.transEditFrame.pack(side=LEFT, padx=5, pady=5)

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

    def __build_trans_param_frame(self, name, params, **args):
        frame = LabelFrame(self.transEditFrame, text=name, **args)

        paramVars = []
        paramSpinBox = []
        paramLabels = []
        enableBtn = Radiobutton(frame, value=name, variable=self.transName,
                                command=self.__on_transform_selection_change)

        for p, r in params:
            paramVars.append(DoubleVar())
            paramLabels.append(Label(frame, text=p))
            paramSpinBox.append(Spinbox(frame, from_=r[0], to=r[1], increment=r[2],
                                        width=6, textvariable=paramVars[-1]))

        enableBtn.pack(side=LEFT)
        for l, s in zip(paramLabels, paramSpinBox):
            l.pack(side=LEFT, padx=5, pady=5)
            s.pack(side=LEFT, padx=5, pady=5)

        return frame, paramVars

    def __on_transform_param_change(self):
        pass

    def __on_transform_selection_change(self):
        selected = self.transName.get()
        for f in self.transParamFrames:
            if f == selected:
                for child in self.transParamFrames[f].winfo_children():
                    child.configure(state='normal')
            else:
                for child in self.transParamFrames[f].winfo_children():
                    if not isinstance(child, Radiobutton):
                        child.configure(state='disable')

    def list_transforms(self, transforms):
        self.opQueueListbox.delete(0, END)
        for t in transforms:
            self.opQueueListbox.insert(END, str(t))

    def get_active_transform(self):
        active_trans = self.transName.get()
        params = [v.get() for v in self.transParamVars[active_trans]]
        return active_trans, params

    def get_selected_transform_idx(self):
        return self.opQueueListbox.curselection()

    def set_active_transform(self, t):
        self.transName.set(t.name)
        for p, v in zip(self.transParamVars[t.name], t.params):
            p.set(v)
        self.__on_transform_selection_change()


class VibTuneFrame(LabelFrame):
    def __init__(self, root=None, **args):
        LabelFrame.__init__(self, root, text='Tune Vibration Mode', **args)

        self.histFrame = VibHistFrame(self)
        self.curveFrame = CurveFrame(self)
        self.transFrame = TransformFrame(self)

        self.histFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5)
        self.curveFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5)
        self.transFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5, expand=YES)

    def draw_histogram(self, data):
        self.histFrame.draw_hist(data)

    def draw_curve(self, data):
        self.curveFrame.draw_curve(data)

    def get_active_transform(self):
        name, params = self.transFrame.get_active_transform()
        return Transform(name, params)

    def set_active_transform(self, t):
        self.transFrame.set_active_transform(t)

    def get_selected_transform_idx(self):
        return self.transFrame.get_selected_transform_idx()

    def list_transforms(self, transforms):
        self.transFrame.list_transforms(transforms)


class VibModeFrame(Frame):
    def __init__(self, root, backend:Optional[VibModeBackend]=None):
        Frame.__init__(self, root)

        self.backend = VibModeBackend() if backend is None else backend

        # self.audio, self.fm = None, None
        self.inPlaceEdit = None

        self.audioPathFrame = LibLoadFrame(self)
        self.rmseFrame = AudioRMSEFrame(self)
        self.tuneFrame = VibTuneFrame(self)
        self.playFrame = AudioPlayFrame(self)
        self.playFrame.set_backend(self.backend)

        self.audioPathFrame.loadBtn.bind('<ButtonRelease-1>', lambda e: self.__load_music())
        self.audioPathFrame.loadBtn2.bind('<ButtonRelease-1>', lambda e: self.__load_vib_mode())
        self.audioPathFrame.saveBtn.bind('<ButtonRelease-1>', lambda e: self.__save_vib_mode())
        self.tuneFrame.transFrame.addBtn.bind('<ButtonRelease-1>', lambda e: self.__on_add_transform())
        self.tuneFrame.transFrame.delBtn.bind('<ButtonRelease-1>', lambda e: self.__on_delete_transform())
        self.tuneFrame.transFrame.moveUpBtn.bind('<ButtonRelease-1>', lambda e: self.__on_move_up_transform())
        self.tuneFrame.transFrame.moveDownBtn.bind('<ButtonRelease-1>', lambda e: self.__on_move_down_transform())
        self.tuneFrame.transFrame.opQueueListbox.bind('<Double-1>', lambda e: self.__on_transform_selected())
        self.tuneFrame.transFrame.applyBtn.bind('<ButtonRelease-1>', lambda e: self.__on_transform_param_change(True))
        self.playFrame.playBtn.bind('<ButtonRelease-1>', lambda e: self.__play_music())

        self.audioPathFrame.pack(side=TOP, fill=X, pady=5, padx=5)
        self.rmseFrame.pack(side=TOP, fill=X, pady=5, padx=5)
        self.tuneFrame.pack(side=TOP, fill=X, expand=YES, pady=5, padx=5)
        self.playFrame.pack(side=TOP, fill=X, expand=YES, pady=5, padx=5)

        self.__lock_load_vib_mode()
        self.__lock_transform_queue()

    def __on_add_transform(self):
        trans = self.tuneFrame.get_active_transform()
        self.backend.transforms().append(trans=trans)
        self.tuneFrame.list_transforms(self.backend.transforms().transform_list())
        self.__on_transform_param_change()

    def __on_delete_transform(self):
        if len(self.backend.transforms()) == 0:
            return

        idx = self.tuneFrame.get_selected_transform_idx()  # tuple
        self.backend.transforms().delete(pos=idx[0])
        self.tuneFrame.list_transforms(self.backend.transforms().transform_list())
        self.__on_transform_param_change()

    def __on_move_up_transform(self):
        idx = self.tuneFrame.get_selected_transform_idx()  # tuple
        self.backend.transforms().move_up(idx[0])
        self.tuneFrame.list_transforms(self.backend.transforms().transform_list())
        self.__on_transform_param_change()

    def __on_move_down_transform(self):
        idx = self.tuneFrame.get_selected_transform_idx()  # tuple
        self.backend.transforms().move_down(idx[0])
        self.tuneFrame.list_transforms(self.backend.transforms().transform_list())
        self.__on_transform_param_change()

    def __lock_load_vib_mode(self):
        self.audioPathFrame.browseBtn2.configure(state='disable')
        self.audioPathFrame.loadBtn2.configure(state='disable')
        self.audioPathFrame.saveBtn.configure(state='disable')

    def __unlock_load_vib_mode(self):
        self.audioPathFrame.browseBtn2.configure(state='normal')
        self.audioPathFrame.loadBtn2.configure(state='normal')
        self.audioPathFrame.saveBtn.configure(state='normal')

    def __lock_transform_queue(self):
        self.tuneFrame.transFrame.addBtn.configure(state='disable')
        self.tuneFrame.transFrame.delBtn.configure(state='disable')
        self.tuneFrame.transFrame.moveUpBtn.configure(state='disable')
        self.tuneFrame.transFrame.moveDownBtn.configure(state='disable')

    def __unlock_transform_queue(self):
        self.tuneFrame.transFrame.addBtn.configure(state='normal')
        self.tuneFrame.transFrame.delBtn.configure(state='normal')
        self.tuneFrame.transFrame.moveUpBtn.configure(state='normal')
        self.tuneFrame.transFrame.moveDownBtn.configure(state='normal')

    def __on_transform_selected(self):
        idx = self.tuneFrame.get_selected_transform_idx()  # tuple
        trans = self.backend.transforms().get_transform(idx[0])
        if trans is not None:
            self.tuneFrame.set_active_transform(trans)
        self.inPlaceEdit = idx[0]
        self.__lock_transform_queue()

    def __on_transform_param_change(self, include_active=False):
        trans = self.tuneFrame.get_active_transform()
        if self.inPlaceEdit is not None:
            self.backend.transforms().update(trans.params, self.inPlaceEdit)
        self.tuneFrame.list_transforms(
            self.backend.transforms().transform_list())

        # curve mapping data
        x = np.linspace(0, 1, 1000)
        curve = self.backend.transforms().apply_all(x, curve=True)
        if self.inPlaceEdit is None and include_active:
            curve = self.backend.transforms().apply_transform(curve, trans, curve=True)
        self.tuneFrame.draw_curve(curve)

        # rmse data
        if self.backend.feature_bundle() is not None:
            if self.inPlaceEdit is None and include_active:
                fb = self.backend.feature_bundle(use_cached=False, sketch_transform=trans)
            else:
                fb = self.backend.feature_bundle(use_cached=False)
            self.__draw_audio_data(fb)

        self.inPlaceEdit = None
        self.__unlock_transform_queue()

    def __load_music(self):
        audioPath = self.audioPathFrame.get_audio_path()
        if len(audioPath) == 0:
            return

        self.backend.load_audio(audioPath)
        self.backend.init_features(audioPath, 512)

        self.__draw_audio_data(self.backend.feature_bundle())
        self.__unlock_load_vib_mode()
        self.__unlock_transform_queue()

    def __play_music(self):
        atomic_wave = self.playFrame.get_atomic_wave()
        # print(atomic_wave)
        audioPath = self.audioPathFrame.get_audio_path()
        launch_vib_with_rmse_transforms(self.master,
            audioPath, self.backend.feature_bundle(),
            self.backend.transforms(), atomic_wave)

    def __load_vib_mode(self):
        vibModePath = self.audioPathFrame.get_vib_mode_path()
        if len(vibModePath) == 0:
            return
        self.backend.transforms().load_transforms(vibModePath)
        self.__on_transform_param_change()

    def __save_vib_mode(self):
        vibModePath = self.audioPathFrame.get_vib_mode_path()
        if len(vibModePath) == 0:
            return

        self.backend.transforms().save_transforms(vibModePath)

    def __draw_audio_data(self, features=None):
        if features is None:
            features = self.backend.feature_bundle()
        self.rmseFrame.draw_rmse(self.backend.plotter(), features)
        self.tuneFrame.draw_histogram(features.feature_data('rmse'))


if __name__ == '__main__':
    root = Tk()
    f = VibModeFrame(root)
    f.pack()
    root.mainloop()
