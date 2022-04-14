import sys
import numpy as np
from tkinter import Tk, Toplevel

sys.path.append('..')

# from AtomicWaveFrame import AtomicWaveFrame


# def launch_atomic_wave_frame() -> None:
#     root = Tk()
#     f = AtomicWaveFrame(root)
#     f.pack()
#     root.mainloop()

# from VibModeFrame import VibModeFrame

# def launch_vibration_mode_frame() -> None:
#     root = Tk()
#     f = VibModeFrame(root)
#     f.pack()
#     root.mainloop()

from VibPlayFrame import VibPlayFrame

def launch_vibration(master=None, process=[]) -> None:
    if master is None:
        root = Tk()
    else:
        print('init Vib Play in TopLevel')
        root = Toplevel(master)
    frame = VibPlayFrame(root, process)
    frame.pack()

    def on_closing():
        frame.backend.close_stream()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    if master is None:
        root.mainloop()

from backends import MonoFrameAudioStream

from vib_music import AudioFeatureBundle
from vib_music import VibrationStream
from vib_music import AudioDriver, LogDriver
from vib_music import AudioProcess, VibrationProcess
from vib_music import AudioStreamHandler, StreamHandler

def launch_vib_with_atomicwave(master, atomicwave:np.ndarray,
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

    launch_vibration(master=master, process=[audioproc, vibproc]) 

from backends import TransformQueue
from vib_music import get_audio_process
from multiprocessing import Queue
def launch_vib_with_rmse_transforms(master, audio:str, fb:AudioFeatureBundle,
    transforms:TransformQueue, atomicwave:np.ndarray) -> None:
    # update vibration mode
    @VibrationStream.vibration_mode(over_ride=True)
    def rmse_transform_mode(fb:AudioFeatureBundle):
        rmse = fb.feature_data('rmse').copy()
        rmse = transforms.apply_all(rmse, curve=False)
        rmse = np.clip((rmse*255).round(), a_min=0, a_max=255)

        vib_seq = rmse.reshape((-1, 1))
        wave = atomicwave.reshape((1, -1))

        vib_seq = (vib_seq * wave).round().astype(np.uint8)
        return vib_seq

    sdata = VibrationStream.from_feature_bundle(fb, 24, 'rmse_transform_mode')
    # sdriver = PCF8591Driver()
    sdriver = LogDriver()
    shandler = StreamHandler(sdata, sdriver)
    vib_proc = VibrationProcess(shandler)

    audio_proc = get_audio_process(audio, 512)
    if audio_proc is None:
        print('initial audio process failed. exit...')
        return

    results, commands = Queue(), Queue()
    audio_proc.set_event_queues(commands, results)
    audio_proc.attach_vibration_proc(vib_proc)

    launch_vibration(master=master, process=[audio_proc, vib_proc])

if __name__ == '__main__':
    from multiprocessing import Queue
    
    from vib_music import AudioFeatureBundle
    from vib_music import VibrationStream
    from vib_music import LogDriver
    from vib_music import StreamHandler
    from vib_music import VibrationProcess
    from vib_music import get_audio_process

    fb = AudioFeatureBundle.from_folder('../data/test_beat_short_1')
    sdata = VibrationStream.from_feature_bundle(fb, 24, 'rmse_mode')
    sdriver = LogDriver()
    shandler = StreamHandler(sdata, sdriver)
    vib_proc = VibrationProcess(shandler)

    audio = '../audio/test_beat_short_1.wav'
    len_hop = 512
    music_proc = get_audio_process(audio, len_hop)

    results, commands = Queue(), Queue()
    music_proc.set_event_queues(commands, results)
    music_proc.attach_vibration_proc(vib_proc)

    launch_vibration(process=[music_proc, vib_proc])