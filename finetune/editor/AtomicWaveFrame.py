from tkinter import *
import tkinter.ttk as ttk

import numpy as np
import pickle

from numpy.core.arrayprint import DatetimeFormat

def load_database():
    with open('atomic-wave.pkl', 'rb') as f:
        data = pickle.load(f)
    
    return data 

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

class WaveDBFrame(LabelFrame):
    def __init__(self, master=None, database={}, **args):
        LabelFrame.__init__(self, master=master, text='Atomic Wave Database', **args)
        
        self.database = database

        self.newDBName = StringVar()
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

        self.dbOptions.bind('<Double-1>', self.__on_database_selected)
        # self.waveOptions.bind('<Double-1>', self.__on_waveform_selected)

        self.dbOptions.pack(expand=YES)
        self.waveOptions.pack(expand=YES)

        self.dBframe.pack(side=LEFT, fill=X, padx=(0, 10))
        ttk.Separator(self.selFrame, orient=VERTICAL).pack(side=LEFT, fill=Y, expand=YES)
        self.waveFrame.pack(side=LEFT, fill=X, padx=(10, 0))

        self.newDB.pack(side=LEFT)
        self.newDBName.pack(side=LEFT)

        self.selFrame.pack(side=TOP, fill=X, expand=YES, padx=5)
        self.btnFrame.pack(side=TOP, fill=X, expand=YES, padx=5, pady=(5, 0))
    
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
   
    def __on_database_selected(self, event):
        dbName = self.get_wave_database_selection()
        waves = sorted(list(self.database[dbName].keys()))
        self.set_waveform_list(waves)
    
    def __add_wave_database(self):
        name = self.newDBName.get()
        print(name)
        if name not in self.database:
            self.database.setdefault(name, {})
            self.set_wave_database_list(
                sorted(list(self.database.keys()))
            )
        #TODO: save new name here...

class SliderFrame(Frame):
    def __init__(self, root=None, **args):
        # args.setdefault('height', 400)
        # args.setdefault('width', 800)
        Frame.__init__(self, root, **args)

        self.sliderPanel = SliderPanel(self, height=400, width=800)
       
        self.sliderPanel.pack()
        self.sliderPanel.pack_propagate(0) # keep the panel size
        ttk.Separator(self, orient=HORIZONTAL).pack(side=BOTTOM, fill=X, expand=YES)
    
    def set_values(self, values):
        self.sliderPanel.set_values(values)
    
    def get_values(self):
        return self.sliderPanel.get_values()

class WavePlayFrame(LabelFrame):
    def __init__(self, master=None, **args):
        LabelFrame.__init__(self, master=master, text='Atomic Wave Playing', **args)

        self.wave_len = DoubleVar()

        self.radioFrame = LabelFrame(self, text='Wave Length (in Time)')
        self.wave_len_options = []
        for t in [0.5, 1., 2., 5.]:
            self.wave_len_options.append(
                Radiobutton(self.radioFrame, text=f'{t} Sec.', variable=self.wave_len,
                value=t)
            )
            self.wave_len_options[-1].pack(anchor=W)
        self.buttonFrame = Frame(self)
        self.scaleSpinbox = Spinbox(self.buttonFrame, from_=1, to=255, increment=1)
        self.playButton = Button(self.buttonFrame, text='Play')

        self.playButton.pack(side=RIGHT)

        self.radioFrame.pack(side=TOP, padx=5)
        self.buttonFrame.pack(side=TOP)

    def get_duration(self):
        return self.wave_len.get()
       
class AtomicWaveFrame(Frame):
    def __init__(self, root=None):
        Frame.__init__(self, root, height=600, width=800)

        self.data = load_database()

        self.sliderFrame = SliderFrame(self, height=400)
        self.controlFrame = Frame(self)
        self.waveDBFrame = WaveDBFrame(self.controlFrame, database=self.data, height=200)
        self.playFrame = WavePlayFrame(self.controlFrame)

        self.waveDBFrame.set_wave_database_list(
            sorted(list(self.data.keys()))
        )

        self.waveDBFrame.waveOptions.bind('<Double-1>', self.__update_sliders)
        self.playFrame.playButton.bind('<Button-1>', self.__launch_vibration)

        self.waveDBFrame.pack(side=LEFT, padx=10)
        self.playFrame.pack(side=RIGHT, fill=Y, expand=NO)

        self.sliderFrame.pack(side=TOP, pady=(0, 10), padx=10)
        self.controlFrame.pack(side=TOP, fill=Y, pady=(0, 10))

    def __update_sliders(self, event):
        dbName = self.waveDBFrame.get_wave_database_selection()
        waveName = self.waveDBFrame.get_waveform_selection()

        arr = self.data[dbName][waveName]
        self.sliderFrame.set_values(arr)

    def __launch_vibration(self, event):
        duration = self.playFrame.get_duration()
        wave = self.sliderFrame.get_values()
        print(f'Duration {duration}')
        print(f'waveform {wave}')

if __name__ == '__main__':
    root = Tk()
    f = AtomicWaveFrame(root)
    f.pack()
    root.mainloop()
