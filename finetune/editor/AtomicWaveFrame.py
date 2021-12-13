from tkinter import *
import tkinter.ttk as ttk

import numpy as np 

class SliderFrame(Frame):
    def __init__(self, root=None, **args):
        # args.setdefault('height', 400)
        # args.setdefault('width', 800)
        Frame.__init__(self, root, **args)

        self.sliders = []
        self.labels = []
        self.spins = []
        self.vars = []

        self.sliderPanel = Frame(self, height=400, width=800)

        for i in range(24):
            self.vars.append(DoubleVar())
            self.sliders.append(Scale(self.sliderPanel, from_=1., to=0., digits=3, resolution=0.01,
                orient=VERTICAL, showvalue=False, sliderlength=30, variable=self.vars[-1]))
            self.labels.append(Label(self.sliderPanel, textvariable=self.vars[-1]))
        
        for i, (s, l) in enumerate(zip(self.sliders, self.labels)):
            # s.grid(row=0, column=i, padx=10, pady=10)
            s.grid(row=0, column=i)
            l.grid(row=1, column=i)
        
        self.btn = Button(self, text='Save', relief=RAISED)

        self.sliderPanel.pack()
        self.sliderPanel.pack_propagate(0)
        ttk.Separator(self, orient=HORIZONTAL).pack(side=BOTTOM, fill=X, expand=YES)
        self.btn.pack(side=TOP)

    def get_values(self):
        return np.array([v.get() for v in self.vars])
    
    def set_values(self, values):
        for v, val in zip(self.vars, values[:24]):
            v.set(val)
        
class DataBaseFrame(Frame):
    def __init__(self, root=None, **args):
        Frame.__init__(self, root, **args)

        self.dbVar = StringVar()
        self.dbNames = ['sample db']
        self.waveVar = StringVar()
        self.waveNames = ['a', 'b', 'c', 'd']

        self.dbOptions = OptionMenu(self, 'DataBase', *self.dbNames)
        self.waveList = Listbox(self, listvariable=self.waveVar, selectmode=SINGLE)

        self.dbOptions.pack(side=BOTTOM)
        self.waveList.pack(side=BOTTOM)
        
class AtomicWaveFrame(Frame):
    def __init__(self, root=None):
        Frame.__init__(self, root, height=600, width=800)

        self.sliderFrame = SliderFrame(self, height=400)
        self.sliderFrame.pack()


        x = np.round(np.abs(np.random.randn(24)), 2)
        self.sliderFrame.set_values(x)


if __name__ == '__main__':
    root = Tk()
    f = SliderFrame(root)
    f.pack()
    root.mainloop()
