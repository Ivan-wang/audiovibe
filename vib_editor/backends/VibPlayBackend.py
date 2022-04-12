from queue import Empty
import sys
import os
import pickle
import librosa
import numpy as np
from tkinter import IntVar
from multiprocessing import Queue, Process
from threading import Thread, Event
from typing import List, Tuple

from vib_music import StreamProcess
from vib_music import StreamEvent, StreamEventType
from vib_music import AudioStreamEvent, AudioStreamEventType

VIB_TUNE_MODE = 'vibration_tune_mode'

class SliderHelperThread(Thread):
    def __init__(self, variable:IntVar, msg_queue:Queue, end_event:Event):
        super(SliderHelperThread, self).__init__()
        self.variable = variable
        self.msg_queue = msg_queue
        self.end_event = end_event
    
    def run(self) -> None:
        while not self.end_event.is_set():
            try:
                msg = self.msg_queue.get(block=False)
            except Empty:
                pass
            else:
                if 'pos' in msg.what:
                    self.variable.set(msg.what['pos'])

class VibPlayBackend(object):
    def __init__(self, slider_var:IntVar, processes:List[StreamProcess]=[]):
        super(VibPlayBackend, self).__init__()
        self.audio_proc = processes[0] if len(processes) > 0 else None

        if self.audio_proc is None:
            return
        self.vib_processes = processes[1:]

        self.slider_var = slider_var 
        self.sendQ, self.recvQ = Queue(), Queue()
        self.audio_proc.set_event_queues(self.sendQ, self.recvQ)
        for p in self.vib_processes:
            self.audio_proc.attach_vibration_proc(p)

        # prepare for GUI
        self.exit_event = Event()
        self.slider_thread = SliderHelperThread(slider_var, self.recvQ, self.exit_event)
        self.audio_proc.enable_GUI_mode()

        self._init_stream()
        try:
            msg = self.recvQ.get(block=True)
        except:
            self.total_frame = 1
        else:
            self.total_frame = msg.what['num_frame']
        
        # NOTE: must start the slider after we get the num frame
        self.slider_thread.start()

        self.is_running = True
        
    def has_audio_proc(self) -> bool:
        return self.audio_proc is not None
    
    def _init_stream(self) -> None:
        if not self.has_audio_proc(): return
        for p in self.vib_processes:
            p.start()
        self.audio_proc.start()
        # NOTE: audio process uses auto init here
        # self.sendQ.put(StreamEvent(head=StreamEventType.STREAM_INIT))
    
    def start_stream(self) -> None:
        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_START))

    def close_stream(self) -> None:
        if not self.has_audio_proc(): return
        if not self.is_running: return

        self.sendQ.put(StreamEvent(head=StreamEventType.STREAM_CLOSE))

        self.audio_proc.join()
        print('audio process joined')
        for p in self.vib_processes:
            p.join()
        print('vibration process joined')
        self.exit_event.set()
        self.slider_thread.join()
        print('slider thread joined')
        self.is_running = False

    def pulse_stream(self) -> None:
        if not self.has_audio_proc(): return

        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_PULSE))

    def resume_stream(self) -> None:
        if not self.has_audio_proc(): return

        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_RESUME))

    def forward_stream(self) -> None:
        if not self.has_audio_proc(): return

        pos = self.slider_var.get()
        pos = min(self.total_frame, pos+100)
        self.slider_var.set(pos)
        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.STREAM_SEEK, what={'pos': pos}))

    def backward_stream(self) -> None:
        if not self.has_audio_proc(): return

        pos = self.slider_var.get()
        pos = max(0, pos-100)
        self.slider_var.set(pos)
        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.STREAM_SEEK, what={'pos': pos}))
    
    def vib_up(self) -> None:
        pass

    def vib_down(self) -> None:
        pass

    def seek_stream(self, where:int) -> None:
        if not self.has_audio_proc(): return

        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.STREAM_SEEK, what={'pos': where}))


# from .VibTransformQueue import TransformQueue

# def launch_vib_with_transforms(audio:str, fb:AudioFeatureBundle, 
#     tQ:TransformQueue, atomic_wave:np.ndarray) -> List[Process]:
#     # update vibration mode
#     @VibrationStream.vibration_mode(over_ride=True)
#     def vib_editor_mode(fb:AudioFeatureBundle):
#         rmse = fb.feature_data('rmse').copy()
#         rmse = tQ.apply_all(rmse, curve=False)
#         rmse = np.clip((rmse*255).round(), a_min=0, a_max=255)

#         vib_seq = rmse.reshape((-1, 1))
#         wave = atomic_wave.reshape((1, -1))

#         vib_seq = (vib_seq * wave).round().astype(np.uint8)
#         return vib_seq

#     sdata = VibrationStream.from_feature_bundle(fb, 24, 'vib_editor_mode')
#     sdriver = PCF8591Driver()
#     shandler = StreamHandler(sdata, sdriver)
#     vib_proc = VibrationProcess(shandler)

#     audio_proc = get_audio_process(audio, 512)
#     if audio_proc is None:
#         print('initial audio process failed. exit...')
#         return

#     results, commands = Queue(), Queue()
#     audio_proc.set_event_queues(commands, results)
#     audio_proc.attach_vibration_proc(vib_proc)

#     return [audio_proc, vib_proc]

# # TODO: reuse plot manager for drawing
# def draw_rmse(audio, sr, hop_len, rmse, ax):
#     ax.cla()

#     librosa.display.waveplot(audio, sr=sr, ax=ax)
#     times = librosa.times_like(rmse, sr=sr, hop_length=hop_len)
#     ax.plot(times, rmse, 'r')
#     ax.set_xlim(xmin=0, xmax=times[-1])

# if __name__ == '__main__':
#     waveform = np.array([0.01] * 8 + [0.99] * 4 + [0.01] * 8 + [0.99] * 4)
#     scale = 75
#     duration = 1.0
#     launch_vib_with_atomicwave(waveform, duration, scale)
