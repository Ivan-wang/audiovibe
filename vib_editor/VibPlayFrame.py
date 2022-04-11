from tkinter import *
import tkinter.ttk as ttk

from .VibPlayBackend import VibPlayBackend

class VibPlayFrame(LabelFrame):
    def __init__(self, master=None, processes=[], **args):
        LabelFrame.__init__(self, master, text='Vib Play Frame', **args)

        self.nextFrame = IntVar(value=0)
        self.backend = VibPlayBackend(self.nextFrame, processes)
        self.btns = {}

        # status text
        statusFrame = LabelFrame(self, text='Status')
        self.statusLabel = Label(statusFrame, text='Loading...', width=60, height=5)

        # progress slider
        total_frame = 1
        if self.backend.has_audio_proc():
            total_frame = self.backend.total_frame
        sliderFrame = LabelFrame(self, text='Progress (Frame)')
        self.slider = Scale(sliderFrame, from_=0, to=total_frame, resolution=1, orient=HORIZONTAL,
            showvalue=NO, sliderlength=60, variable=self.nextFrame)
        nextFrameLabel = Label(sliderFrame, textvariable=self.nextFrame)
        totalFrameLabel = Label(sliderFrame, text='/ {}'.format(total_frame))
        self.nextFrame.set(0)
        
        # control panel
        btnFrame = Frame(self)
        for t in ['Start', 'Pulse', 'Resume', 'Stop']:
            self.btns.update({t:Button(btnFrame, text=t)})
        
        for t in ['Backward', 'Forward', 'VibUP', 'VibDOWN']:
            self.btns.update({t:Button(btnFrame, text=t)})
        
        # bind signals
        self.btns['Start'].bind('<Button-1>', lambda e: self.on_start())
        self.btns['Pulse'].bind('<Button-1>', lambda e: self.on_pulse())
        self.btns['Resume'].bind('<Button-1>', lambda e: self.on_resume())
        self.btns['Stop'].bind('<Button-1>', lambda e: self.backend.close_stream())
        self.btns['Forward'].bind('<Button-1>', lambda e: self.backend.forward_stream())
        self.btns['Backward'].bind('<Button-1>', lambda e: self.backend.backward_stream())
        self.btns['VibUP'].bind('<Button-1>', lambda e: self.backend.vib_up())
        self.btns['VibDOWN'].bind('<Button-1>', lambda e: self.backend.vib_down())
        self.slider.bind('<Button-1>', lambda e: self.backend.pulse_stream())
        self.slider.bind('<ButtonRelease-1>', lambda e: self.backend.seek_stream(self.nextFrame.get()))

        # pack widgets
        self.statusLabel.pack(side=TOP, fill=BOTH)
        statusFrame.pack(side=TOP, padx=5, fill=BOTH, expand=YES)

        self.slider.pack(side=LEFT, fill=BOTH, expand=YES)
        nextFrameLabel.pack(side=LEFT, fill=Y, pady=2)
        totalFrameLabel.pack(side=LEFT, fill=Y, pady=2)
        sliderFrame.pack(side=TOP, padx=5, fill=BOTH, expand=YES)

        for i, btn in enumerate(self.btns):
            self.btns[btn].grid(row=i//4, column=i%4, padx=5, pady=0, sticky=E+W)
        for i in range(0, 4):
            btnFrame.grid_columnconfigure(i, weight=1)
        for i in range(0, 2):
            btnFrame.grid_rowconfigure(i, weight=1)
        btnFrame.pack(side=TOP, fill=X, expand=YES)

        self._disable_all()
        if self.backend.has_audio_proc():
            self.statusLabel.configure(text='Audio Process Good But Not Start!!!')
            self.btns['Start'].configure(state='normal')
        else:
            self.statusLabel.configure(text='No Audio Process Attached!!!')

    def _disable_all(self):
        for btn in self.btns:
            self.btns[btn].configure(state='disable')
        self.slider.configure(state='disable')
    
    def _enable_all(self):
        for btn in self.btns:
            self.btns[btn].configure(state='normal')
        self.slider.configure(state='normal')

    def on_start(self):
        self._enable_all()
        self.btns['Start'].configure(state='disable')
        self.btns['Resume'].configure(state='disable')
        self.statusLabel.configure(text='Audio Playing...')
        self.backend.start_stream()
    
    def on_pulse(self):
        self.btns['Resume'].configure(state='normal')
        self.btns['Pulse'].configure(state='disable')
        self.statusLabel.configure(text='Audio Pulsed...')
        self.backend.pulse_stream()
    
    def on_resume(self):
        self.btns['Pulse'].configure(state='normal')
        self.btns['Resume'].configure(state='disable')
        self.statusLabel.configure(text='Audio Playing...')
        self.backend.resume_stream()
    
    def on_stop(self):
        self._disable_all()
        self.statusLabel.configure(text='Audio Stopped...')
        self.backend.close_stream()



# if __name__ == '__main__':
#     launch_vibration_GUI()