import sys
import os
import pickle
import librosa
import numpy as np
from tkinter import IntVar
from multiprocessing import Queue, Process
from threading import Thread, Event
from typing import List, Tuple

sys.path.append('..')
from vib_music import PCF8591Driver
from vib_music import VibrationProcess
from vib_music import FeatureBuilder
from vib_music import AudioFeatureBundle
from vib_music import StreamHandler
from vib_music import VibrationStream
from vib_music import get_audio_process
from vib_music import AudioProcess, StreamProcess
from vib_music import StreamEvent, StreamEventType
from vib_music import AudioStreamEvent, AudioStreamEventType

FRAME_TIME = 0.0116
VIB_TUNE_MODE = 'vibration_tune_mode'

class SliderHelperThread(Thread):
    def __init__(self, variable:IntVar, msg_queue:Queue, end_event:Event):
        self.variable = variable
        self.msg_queue = msg_queue
        self.end_event = end_event
    
    def run(self) -> None:
        while not self.end_event.is_set():
            msg = self.msg_queue.get(block=True)
            self.variable.set(msg.what['pos'])

class BackendHalper(object):
    def __init__(self, slider_var:IntVar, processes:List[StreamProcess]=[]):
        super(self, BackendHalper).__init__()
        self.audio_proc = processes[0] if len(processes) > 0 else None
        self.vib_processes = processes[1:]
        self.sendQ, self.recvQ = self.audio_proc.event_queues()

        # prepare for GUI
        if self.audio_proc is not None:
            self.exit_event = Event()
            self.slider_thread = SliderHelperThread(slider_var, self.recvQ, self.exit_event)
            self.audio_proc.enable_frame_ack()
            self.audio_proc.enable_manual_exit()
        
    def has_audio_proc(self) -> bool:
        return self.audio_proc is not None

    def start_stream(self) -> None:
        if not self.has_audio_proc(): return
        for p in self.vib_processes:
            p.start()
        self.audio_proc.start()
        self.slider_thread.start()
        self.sendQ.put(StreamEvent(head=StreamEventType.STREAM_INIT))
        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_START))

    def close_stream(self) -> None:
        if not self.has_audio_proc(): return

        self.exit_event.set()
        self.sendQ.put(StreamEvent(head=StreamEventType.STREAM_CLOSE))

        self.slider_thread.join()
        self.audio_proc.join()
        for p in self.vib_processes:
            p.join()

    def pulse_stream(self) -> None:
        if not self.has_audio_proc(): return

        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_PULSE))

    def resume_stream(self) -> None:
        if not self.has_audio_proc(): return

        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_RESUME))

    def forward_stream(self) -> None:
        if not self.has_audio_proc(): return

        pos = self.audio_proc.stream_handler.tell()
        pos = min(self.audio_proc.stream_handler.num_frame(), pos+100)
        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.STREAM_SEEK, what={'pos': pos}))

    def backward_stream(self) -> None:
        if not self.has_audio_proc(): return

        pos = self.audio_proc.stream_handler.tell()
        pos = min(0, pos-100)
        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.STREAM_SEEK, what={'pos': pos}))
    
    def vib_up(self) -> None:
        pass

    def vib_down(self) -> None:
        pass

    def seek_stream(self, where:int) -> None:
        if not self.has_audio_proc(): return

        self.sendQ.put(AudioStreamEvent(head=AudioStreamEventType.STREAM_SEEK, what={'pos': where}))

def load_atomic_wave_database(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)

    return data


def save_atomic_wave_database(data, path):
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def launch_vib_with_atomicwave(atomicwave:np.ndarray,
    duration:float, scale:int=1) -> Tuple[Queue, Queue]:
    atomicwave *= scale
    MAGIC_NUM = 1.4
    num_frame = int(duration / FRAME_TIME * MAGIC_NUM)
    # print(f'estimated duration {FRAME_TIME * num_frame:.3f}')
    sequence = np.stack([atomicwave] * num_frame, axis=0).astype(np.uint8)
    return launch_vib_with_array(sequence)


def launch_vib_with_array(sequence:np.ndarray, len_frame:int):
    sdata = VibrationStream(sequence, len_frame)
    sdriver = PCF8591Driver()
    shandler = StreamHandler(sdata, sdriver)

    vib_proc = VibrationProcess(shandler)
    results, commands = Queue(), Queue()
    vib_proc.set_event_queues(commands, results)

    # FIXME: where to start the process
    return commands, results

from .VibTransformQueue import TransformQueue

def launch_vib_with_transforms(audio:str, fb:AudioFeatureBundle, 
    tQ:TransformQueue, atomic_wave:np.ndarray) -> List[Process, Process]:
    # update vibration mode
    @VibrationStream.vibration_mode(over_ride=True)
    def vib_editor_mode(fb:AudioFeatureBundle):
        rmse = fb.feature_data('rmse').copy()
        rmse = tQ.apply_all(rmse, curve=False)
        rmse = np.clip((rmse*255).round(), a_min=0, a_max=255)

        vib_seq = rmse.reshape((-1, 1))
        wave = atomic_wave.reshape((1, -1))

        vib_seq = (vib_seq * wave).round().astype(np.uint8)
        return vib_seq

    sdata = VibrationStream.from_feature_bundle(fb, 24, 'vib_editor_mode')
    sdriver = PCF8591Driver()
    shandler = StreamHandler(sdata, sdriver)
    vib_proc = VibrationProcess(shandler)

    audio_proc = get_audio_process(audio, 512)
    if audio_proc is None:
        print('initial audio process failed. exit...')
        return

    results, commands = Queue(), Queue()
    audio_proc.set_event_queues(commands, results)
    audio_proc.attach_vibration_proc(vib_proc)

    return [audio_proc, vib_proc]

def init_audio_features(audio:str, len_hop:int=512, use_cache:bool=False) -> AudioFeatureBundle:
    # build feature dirs if necessary
    DATA_DIR = '../data'
    os.makedirs(DATA_DIR, exist_ok=True)
    DATA_DIR = os.path.join(DATA_DIR, 'vib_editor')
    os.makedirs(DATA_DIR, exist_ok=True)

    feature_dir = os.path.basename(audio).split('.')[0]
    feature_dir = os.path.join(DATA_DIR, feature_dir)
    if not use_cache or not os.path.isdir(feature_dir):
        # extract and save features
        recipe = {
            'rmse': {
                'len_window': 2048
            },
            'melspec': {
                'len_window': 2048,
                'n_mels': 128,
                'fmax': None
            }
        }
        
        fbuilder = FeatureBuilder(audio, None, len_hop)
        fb = fbuilder.build_features(recipe)
        fb.save(feature_dir)
    else:
        fb = AudioFeatureBundle.from_folder(feature_dir)

    return fb


# TODO: reuse plot manager for drawing
def draw_rmse(audio, sr, hop_len, rmse, ax):
    ax.cla()

    librosa.display.waveplot(audio, sr=sr, ax=ax)
    times = librosa.times_like(rmse, sr=sr, hop_length=hop_len)
    ax.plot(times, rmse, 'r')
    ax.set_xlim(xmin=0, xmax=times[-1])

if __name__ == '__main__':
    waveform = np.array([0.01] * 8 + [0.99] * 4 + [0.01] * 8 + [0.99] * 4)
    scale = 75
    duration = 1.0
    launch_vib_with_atomicwave(waveform, duration, scale)
