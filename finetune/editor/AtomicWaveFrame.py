from tkinter import *
import tkinter.ttk as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


import numpy as np
import pickle

from numpy.core.arrayprint import DatetimeFormat

def load_database():
    with open('atomic-wave.pkl', 'rb') as f:
        data = pickle.load(f)
    
    return data 

class WavePlotFrame(LabelFrame):
    def __init__(self, master=None, **args):
        LabelFrame.__init__(self, master=master, text='Atomic Wave Plot', **args)

        data = np.clip(np.random.randn(24), 0., 1)
        x, y = self.__make_plot_data(data)

        self.figure = Figure(figsize=(6, 3))
        self.ax = self.figure.subplots(1, 1)
        self.ax.plot(x, y)
        self.ax.set_xticks(np.arange(0, 25, 1))
        self.ax.set_yticks(np.arange(0, 1.01, 0.2))
        self.ax.set_yticks(np.arange(0, 1.01, 0.1), minor=True)
        self.ax.grid(which='both')
        self.ax.grid(which='minor', alpha=0.2)
        self.ax.grid(which='major', alpha=0.5)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()

        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=YES)

    def __make_plot_data(self, x):
        xdata = np.linspace(0, 24, num=1000, endpoint=False)
        ydata = x[np.floor(xdata).astype(np.int64)]
        return xdata, ydata

class WaveDBFrame(LabelFrame):
    def __init__(self, master=None, database={}, **args):
        LabelFrame.__init__(self, master=master, text='Atomic Wave Database', **args)
        
        self.database = database

        self.newDBName = StringVar()
        self.newWaveName = StringVar()
        self.dbNames = sorted(list(self.database.keys()))
        self.waveNames = []

        self.selFrame = Frame(self)
        self.dBframe = LabelFrame(self.selFrame, text='Database Name')
        self.waveFrame = LabelFrame(self.selFrame, text='Wave Name')
        self.dbOptions = Listbox(self.dBframe, selectmode=SINGLE, exportselection=False)
        for name in self.dbNames:
            self.dbOptions.insert(END, name)
        self.waveOptions = Listbox(self.waveFrame, selectmode=SINGLE, exportselection=False)

        self.btnFrame = Frame(self)
        self.newDB = Button(self.btnFrame, text='New Database', command=self.__add_wave_database)
        self.newDBName = Entry(self.btnFrame, textvariable=self.newDBName)
        self.newWave = Button(self.btnFrame, text='New Wave')
        self.newWaveName = Entry(self.btnFrame, textvariable=self.newWaveName)

        self.dbOptions.bind('<Double-1>', self.__on_database_selected)
        # self.waveOptions.bind('<Double-1>', self.__on_waveform_selected)

        self.dbOptions.pack(side=TOP, fill=X, padx=5, expand=YES)
        self.waveOptions.pack(side=TOP, fill=X, padx=5, expand=YES)

        self.dBframe.pack(side=LEFT, fill=X, padx=5, expand=YES)
        # ttk.Separator(self.selFrame, orient=VERTICAL).pack(side=LEFT, fill=Y, expand=YES)
        self.waveFrame.pack(side=LEFT, fill=X, padx=5, expand=YES)

        self.newDB.pack(side=LEFT, padx=5, expand=NO)
        self.newDBName.pack(side=LEFT, fill=X, padx=5, expand=YES)
        self.newWave.pack(side=LEFT, padx=5, expand=NO)
        self.newWaveName.pack(side=LEFT, fill=X, padx=5, expand=YES)

        self.selFrame.pack(side=TOP, fill=X, expand=YES, padx=5)
        self.btnFrame.pack(side=TOP, fill=X, expand=YES, padx=5, pady=5)
    
    def set_wave_database_list(self, dbs):
        self.dbOptions.delete(0, END)
        for d in dbs:
            self.dbOptions.insert(END, d)

    def set_waveform_list(self, waves):
        self.waveOptions.delete(0, END)
        for w in waves:
            self.waveOptions.insert(END, w)
    
    def get_wave_database_selection(self):
        sel = self.dbOptions.curselection()
        return self.dbOptions.get(sel)
    
    def get_waveform_selection(self):
        sel = self.waveOptions.curselection()
        return self.waveOptions.get(sel)

    def get_new_waveform_name(self):
        return self.newWaveName.get()
   
    def __on_database_selected(self, event):
        dbName = self.get_wave_database_selection()
        waves = sorted(list(self.database[dbName].keys()))
        self.set_waveform_list(waves)
    
    def __add_wave_database(self):
        name = self.newDBName.get()
        if len(name) == 0: return
        if name not in self.database:
            self.database.setdefault(name, {})
            self.set_wave_database_list(
                sorted(list(self.database.keys()))
            )
        #TODO: save new name here...


class SliderPanel(LabelFrame):
    def __init__(self, master=None, **args):
        LabelFrame.__init__(self, master=master, text='Atomic Wave Sliders', **args)

        self.vars = []
        self.sliders = []
        self.labels = []

        for i in range(24):
            self.vars.append(DoubleVar(value=0.05))
            self.sliders.append(Scale(self, from_=1., to=0., digits=3, resolution=0.01,
                                      orient=VERTICAL, showvalue=False, sliderlength=30, variable=self.vars[-1]))
            self.labels.append(Label(self, textvariable=self.vars[-1]))

        for i, (s, l) in enumerate(zip(self.sliders, self.labels)):
            # s.grid(row=0, column=i, padx=10, pady=10)
            s.grid(row=0, column=i, padx=1)
            l.grid(row=1, column=i, padx=1)

    def get_values(self):
        return np.array([v.get() for v in self.vars])

    def set_values(self, values):
        for v, val in zip(self.vars, values[:24]):
            v.set(val)

class SliderFrame(Frame):
    def __init__(self, root=None, **args):
        # args.setdefault('height', 400)
        # args.setdefault('width', 800)
        Frame.__init__(self, root, **args)

        self.waveScaleVar = DoubleVar()

        self.sliderPanel = SliderPanel(self, height=400, width=800)
        self.controlPanel = LabelFrame(self, text='Wave Scale')

        Label(self.controlPanel, textvariable=self.waveScaleVar).pack(side=LEFT, padx=5)
        self.scaleSlider = Scale(self.controlPanel, from_=0., to=1., resolution=0.1,
                                 orient=HORIZONTAL, showvalue=False, tickinterval=0.1,
                                 variable=self.waveScaleVar)

        self.scaleSlider.pack(side=LEFT, padx=5, fill=X, expand=YES)

        self.sliderPanel.pack(side=TOP, fill=X, padx=5, pady=5, expand=NO)
        self.controlPanel.pack(side=TOP, fill=X, padx=5, pady=5, expand=NO)
        self.sliderPanel.pack_propagate(0) # keep the panel size
        ttk.Separator(self, orient=HORIZONTAL).pack(side=BOTTOM, fill=X, expand=YES)
    
    def set_values(self, values):
        self.sliderPanel.set_values(values)
    
    def get_values(self):
        return self.sliderPanel.get_values()

    def sel_scale(self, value):
        self.waveScaleVar.set(value)

    def get_scale(self, value):
        return self.waveScaleVar.get()

class WavePlayFrame(LabelFrame):
    def __init__(self, master=None, **args):
        LabelFrame.__init__(self, master=master, text='Atomic Wave Playing', **args)

        self.wave_len = DoubleVar()
        self.wave_scale = IntVar()
        self.radioFrame = LabelFrame(self, text='Wave Length (in Time)')
        self.wave_len_options = []
        for t in [0.5, 1., 2., 5.]:
            self.wave_len_options.append(
                Radiobutton(self.radioFrame, text=f'{t} Sec.', variable=self.wave_len,
                value=t)
            )
            self.wave_len_options[-1].pack(anchor=W)
        self.buttonFrame = Frame(self)
        Label(self.buttonFrame, text='Scale Used for Playing').pack(side=TOP)
        Label(self.buttonFrame, text='(1 ~ 255)').pack(side=TOP, pady=(0, 5))
        self.scaleSpinbox = Spinbox(self.buttonFrame, from_=1, to=255, increment=1,
                                    textvariable=self.wave_scale)
        self.playButton = Button(self.buttonFrame, text='Play')

        self.scaleSpinbox.pack(side=TOP, pady=(0, 5))
        self.playButton.pack(side=BOTTOM)

        self.radioFrame.pack(side=TOP, padx=5)
        self.buttonFrame.pack(side=TOP)

    def get_duration(self):
        return self.wave_len.get()

    def get_scale(self):
        return self.wave_scale.get()
       
class AtomicWaveFrame(Frame):
    def __init__(self, root=None):
        Frame.__init__(self, root, height=600, width=800)

        self.data = load_database()

        self.plotFrame = WavePlotFrame(self)
        self.sliderFrame = SliderFrame(self, height=400)
        self.controlFrame = Frame(self)
        self.waveDBFrame = WaveDBFrame(self.controlFrame, database=self.data, height=200)
        self.playFrame = WavePlayFrame(self.controlFrame)

        self.waveDBFrame.set_wave_database_list(
            sorted(list(self.data.keys()))
        )

        self.waveDBFrame.waveOptions.bind('<Double-1>', self.__update_sliders)
        self.waveDBFrame.newWave.bind('<Button-1>', self.__save_atomic_wave)
        self.playFrame.playButton.bind('<Button-1>', self.__launch_vibration)

        self.waveDBFrame.pack(side=LEFT, padx=10, fill=X, expand=YES)
        self.playFrame.pack(side=RIGHT, padx=10, fill=X, expand=NO)

        self.plotFrame.pack(side=TOP, pady=5, fill=BOTH, expand=YES)
        self.sliderFrame.pack(side=TOP, pady=5, padx=10)
        self.controlFrame.pack(side=TOP, fill=X, pady=5, padx=10)

    def __update_sliders(self, event):
        dbName = self.waveDBFrame.get_wave_database_selection()
        waveName = self.waveDBFrame.get_waveform_selection()

        arr = self.data[dbName][waveName]
        self.sliderFrame.set_values(arr)

    def __launch_vibration(self, event):
        duration = self.playFrame.get_duration()
        scale = self.playFrame.get_scale()
        wave = self.sliderFrame.get_values()

        print(f'Duration {duration}')
        print(f'waveform {wave}')
        print(f'scale {scale}')

    def __save_atomic_wave(self, event):
        name = self.waveDBFrame.get_new_waveform_name()
        if len(name) == 0: return

        dbName = self.waveDBFrame.get_wave_database_selection()
        if name not in self.data[dbName]:
            arr = self.sliderFrame.get_values()
            self.data[dbName].update({name: arr})
            self.waveDBFrame.set_waveform_list(
                sorted(list(self.data[dbName].keys()))
            )

if __name__ == '__main__':
    root = Tk()
    f = AtomicWaveFrame(root)
    f.pack()
    root.mainloop()
