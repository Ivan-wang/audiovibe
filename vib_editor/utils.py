import sys
import numpy as np
from tkinter import Tk

from AtomicWaveFrame import AtomicWaveFrame

from vib_music import AudioStream, VibrationStream
from vib_music import AudioDriver, LogDriver
from vib_music import AudioProcess, VibrationProcess
from vib_music import AudioStreamHandler, StreamHandler

def launch_atomic_wave_frame() -> None:
    root = Tk()
    f = AtomicWaveFrame(root)
    f.pack()
    root.mainloop()

from VibModeFrame import VibModeFrame

def launch_vibration_mode_frame() -> None:
    root = Tk()
    f = VibModeFrame(root)
    f.pack()
    root.mainloop()

from VibPlayFrame import VibPlayFrame

def launch_vibration(process=[]) -> None:
    root = Tk()
    frame = VibPlayFrame(root, process)
    frame.pack()

    def on_closing():
        frame.backend.close_stream()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

class MonoFrameAudioStream(AudioStream):
    def __init__(self, num_frame:int, len_frame: int) -> None:
        super().__init__(np.zeros((len_frame,), dtype=np.uint16), len_frame)
        self.next_frame = 0
        self.num_frame = num_frame
    
    def init_stream(self) -> None:
        super().init_stream()
    
    def getnframes(self) -> int:
        return self.num_frame
    
    def readframe(self, n: int = 1):
        if self.next_frame == self.num_frame:
            return ''
        else:
            self.next_frame += 1
            return self.chunks.tostring()
    
    def tell(self) -> int:
        return self.next_frame
    
    def setpos(self, pos: int) -> None:
        self.next_frame = pos
    
    def rewind(self) -> None:
        self.next_frame = 0

    def close(self) -> None:
        pass
        
    def getframerate() -> int:
        return 44100
    
    def getnchannels() -> int:
        return 1
    
    def getsampwidth() -> int:
        return 2

def launch_vib_with_atomicwave(atomicwave:np.ndarray,
    duration:float, scale:int=1) -> None:
    FRAME_TIME = 0.0116
    atomicwave *= scale
    num_frame = int(duration / FRAME_TIME)

    audiodata = MonoFrameAudioStream(num_frame, 512)
    audiodriver = AudioDriver()
    audiohandler = AudioStreamHandler(audiodata, audiodriver)
    audioproc = AudioProcess(audiohandler)

    vibdata= np.stack([atomicwave] * num_frame, axis=0).astype(np.uint8)
    vibdata = VibrationStream(vibdata, 24)
    vibdriver = LogDriver()
    vibhandler = StreamHandler(vibdata, vibdriver)
    vibproc = VibrationProcess(vibhandler)

    launch_vibration([audioproc, vibproc]) 