from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

import numpy as np
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from matplotlib.figure import Figure
from backend import load_audio
from backend import draw_rmse
from backend import TransformQueue, Transform


class LibLoadFrame(LabelFrame):
    def __init__(self, root=None, **args):
        LabelFrame.__init__(self, root, text='Load Library', **args)

        self.audioPath = StringVar()
        self.vibModePath = StringVar()

        self.audioPathEntry = Entry(self, textvariable=self.audioPath)
        self.browseBtn = Button(self, text='Browse...', command=self.__ask_audio_path)
        self.loadBtn = Button(self, text='Load')
        self.playBtn = Button(self, text='Play')
        self.vibModeEntry = Entry(self, textvariable=self.vibModePath)
        self.browseBtn2 = Button(self, text='Browse...', command=self.__ask_vibmode_path)
        self.loadBtn2 = Button(self, text='Load')
        self.saveBtn = Button(self, text='save')

        Label(self, text='Audio: ').pack(side=LEFT, padx=5, pady=5)
        self.audioPathEntry.pack(side=LEFT, fill=X, expand=YES, padx=5, pady=5)
        self.browseBtn.pack(side=LEFT, pady=5)
        self.loadBtn.pack(side=LEFT, pady=5)
        self.playBtn.pack(side=LEFT, pady=5)
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

    def __ask_vibmode_path(self):
        self.vibModePath.set(filedialog.askopenfilename(
            initialdir='.'
        ))

    def get_audio_path(self):
        return self.audioPath.get()

    def get_vibmode_path(self):
        return self.vibModePath.get()

class AudioRMSEFrame(LabelFrame):
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
        self.canvas.draw()


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
        self.ax.set_ylim((0, max(bins) // 10 * 10))
        self.ax.set_yticks(np.linspace(0, (max(bins) + 9) // 10 * 10, 5),
                           labels=np.linspace(0, (max(bins) + 9) // 10 * 10, 5))
        self.ax.set_yticks(np.linspace(0, (max(bins) + 9) // 10 * 10, 50), minor=True)
        self.ax.set_xticklabels(self.ax.get_xticklabels(), fontsize=8)
        self.ax.set_xticklabels(self.ax.get_xticklabels(), fontsize=8)
        self.ax.set_yticklabels(self.ax.get_yticklabels(), fontsize=8)

        self.ax.grid(which='both')
        self.ax.grid(which='minor', alpha=0.2)
        self.ax.grid(which='major', alpha=0.5)

        self.canvas.draw()


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


class TransformFrame(LabelFrame):
    def __init__(self, root=None, **args):
        LabelFrame.__init__(self, root, text='Transforms', **args)

        self.transName = StringVar()

        self.transEditFrame = LabelFrame(self, text='Trans. Params')
        self.transParamFrames = {}
        self.transParamVars = {}
        params = [
            ('linear', [('slope', (0, 1, 0.01)), ('bias', (0, 1, 0.01))]),
            ('norm', [('mean', (0, 1, 0.01)), ('std', (0, 1, 0.001))]),
            ('power', [('power', (0, 2, 0.01))]),
            ('log', [('gamma', (0, 1, 0.01))])
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
    def __init__(self, root):
        Frame.__init__(self, root)

        self.audio, self.fm = None, None
        self.rmseCopy = None
        self.transformQueue = TransformQueue()
        self.inPlaceEdit = None

        self.audioPathFrame = LibLoadFrame(self)
        self.rmseFrame = AudioRMSEFrame(self)
        self.tuneFrame = VibTuneFrame(self)

        self.audioPathFrame.loadBtn.bind('<Button-1>', lambda e: self.__load_music())
        self.audioPathFrame.loadBtn2.bind('<Button-1>', lambda e: self.__load_vib_mode())
        self.audioPathFrame.saveBtn.bind('<Button-1>', lambda  e: self.__save_vib_mode())
        self.tuneFrame.transFrame.addBtn.bind('<Button-1>', lambda e: self.__on_add_transform())
        self.tuneFrame.transFrame.delBtn.bind('<Button-1>', lambda e: self.__on_delete_transform())
        self.tuneFrame.transFrame.moveUpBtn.bind('<Button-1>', lambda e: self.__on_move_up_transform())
        self.tuneFrame.transFrame.moveDownBtn.bind('<Button-1>', lambda e: self.__on_move_down_transform())
        self.tuneFrame.transFrame.opQueueListbox.bind('<Double-1>', lambda e: self.__on_transform_selected())
        self.tuneFrame.transFrame.applyBtn.bind('<Button-1>', lambda e: self.__on_transform_param_change())

        self.audioPathFrame.pack(side=TOP, fill=X, pady=5, padx=5)
        self.rmseFrame.pack(side=TOP, fill=X, pady=5, padx=5)
        self.tuneFrame.pack(side=TOP, fill=X, expand=YES, pady=5, padx=5)

    def __on_add_transform(self):
        trans = self.tuneFrame.get_active_transform()
        self.transformQueue.append(trans=trans)
        self.tuneFrame.list_transforms(self.transformQueue.transform_list())
        self.__on_transform_param_change(ignore_active=True)

    def __on_delete_transform(self):
        if len(self.transformQueue) == 0:
            return

        idx = self.tuneFrame.get_selected_transform_idx() # tuple
        self.transformQueue.delete(pos=idx[0])
        self.tuneFrame.list_transforms(self.transformQueue.transform_list())
        self.__on_transform_param_change(ignore_active=True)

    def __on_move_up_transform(self):
        idx = self.tuneFrame.get_selected_transform_idx() # tuple
        self.transformQueue.move_up(idx[0])
        self.tuneFrame.list_transforms(self.transformQueue.transform_list())
        self.__on_transform_param_change(ignore_active=True)

    def __on_move_down_transform(self):
        idx = self.tuneFrame.get_selected_transform_idx() # tuple
        self.transformQueue.move_down(idx[0])
        self.tuneFrame.list_transforms(self.transformQueue.transform_list())
        self.__on_transform_param_change(ignore_active=True)

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
        idx = self.tuneFrame.get_selected_transform_idx() # tuple
        trans = self.transformQueue.get_transform(idx[0])
        if trans is not None:
            self.tuneFrame.set_active_transform(trans)
        self.inPlaceEdit = idx[0]
        self.__lock_transform_queue()

    def __on_transform_param_change(self, ignore_active=False):
        trans = self.tuneFrame.get_active_transform()
        if self.inPlaceEdit is not None:
            self.transformQueue.update(trans.params, self.inPlaceEdit)
        self.tuneFrame.list_transforms(self.transformQueue.transform_list())

        # curve mapping data
        x = np.linspace(0, 1, 1000)
        curve = self.transformQueue.apply_all(x, curve=True)
        if self.inPlaceEdit is None and not ignore_active:
            curve = self.transformQueue.apply_transform(curve, trans)
        self.tuneFrame.draw_curve(curve)

        if self.fm is not None:
            data = self.transformQueue.apply_all(self.rmseCopy.copy(), curve=False)
            self.fm.set_feature_data('rmse', data)
            self.__draw_audio_data()

        self.inPlaceEdit = None
        self.__unlock_transform_queue()

    def __load_music(self):
        self.audio, self.fm = None, None
        audioPath = self.audioPathFrame.get_audio_path()
        self.audio, self.fm = load_audio(audioPath)
        self.rmseCopy = self.fm.feature_data('rmse').copy()
        self.__draw_audio_data()

    def __play_music(self):
        pass

    def __load_vib_mode(self):
        vibModePath = self.audioPathFrame.get_vibmode_path()
        self.transformQueue.load_transforms(vibModePath)
        self.__on_transform_param_change()

    def __save_vib_mode(self):
        vibModePath = self.audioPathFrame.get_vibmode_path()
        self.transformQueue.save_transforms(vibModePath)

    def __draw_audio_data(self):
        self.rmseFrame.draw_rmse(self.audio, self.fm)
        self.tuneFrame.draw_histogram(self.fm.feature_data('rmse'))

if __name__ == '__main__':
    root = Tk()
    f = VibModeFrame(root)
    f.pack()
    root.mainloop()
