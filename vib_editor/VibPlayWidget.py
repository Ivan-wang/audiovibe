from tkinter import *
import tkinter.ttk as ttk

from .backend import BackendHalper

class VibPlayWidget(LabelFrame):
    def __init__(self, master=None, processes=[], **args):
        LabelFrame.__init__(self, master, text='Vib Play Frame', **args)

        self.nextFrame = IntVar(value=0)
        self.backend = BackendHalper(self.nextFrame, processes)
        self.btns = []

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
            self.btns.append(Button(btnFrame, text=t))
        
        for t in ['Backward', 'Forward', 'VibUP', 'VibDown']:
            self.btns.append(Button(btnFrame, text=t))
        
        # bind signals
        self.btns[0].bind('<Button-1>', lambda e: self.backend.start_stream())
        self.btns[1].bind('<Button-1>', lambda e: self.backend.pulse_stream())
        self.btns[2].bind('<Button-1>', lambda e: self.backend.resume_stream())
        self.btns[3].bind('<Button-1>', lambda e: self.backend.close_stream())
        self.btns[4].bind('<Button-1>', lambda e: self.backend.forward_stream())
        self.btns[5].bind('<Button-1>', lambda e: self.backend.backward_stream())
        self.btns[6].bind('<Button-1>', lambda e: self.backend.vib_up())
        self.btns[7].bind('<Button-1>', lambda e: self.backend.vib_down())
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
            btn.grid(row=i//4, column=i%4, padx=5, pady=0, sticky=E+W)
        for i in range(0, 4):
            btnFrame.grid_columnconfigure(i, weight=1)
        for i in range(0, 2):
            btnFrame.grid_rowconfigure(i, weight=1)
        btnFrame.pack(side=TOP, fill=X, expand=YES)

        if self.backend.has_audio_proc():
            self.statusLabel.configure(text='Audio Process Good But Not Start!!!')
        else:
            self.statusLabel.configure(text='No Audio Process Attached!!!')
            self._disable_all()

    def _disable_all(self):
        for btn in self.btns:
            btn.configure(state='disable')
        self.slider.configure(state='disable')
    
    def _enable_all(self):
        pass


def launch_vibration_GUI(process=[]) -> None:
    root = Tk()
    frame = VibPlayWidget(root, process)
    frame.pack()

    def on_closing():
        frame.backend.close_stream()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == '__main__':
    launch_vibration_GUI()