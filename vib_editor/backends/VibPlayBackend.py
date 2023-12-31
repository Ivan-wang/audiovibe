from queue import Empty
from tkinter import IntVar
from multiprocessing import Queue
from threading import Thread, Event
from typing import List

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
                msg = self.msg_queue.get(block=True, timeout=0.1)
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
