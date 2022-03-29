import wave
from typing import Optional, List
from multiprocessing import Process

from .streams import WaveAudioStream
from .drivers import AudioDriver
from .streamhandler import StreamHandler, AudioStreamHandler
from .processes import AudioProcess

def get_audio_process(audio:str, len_frame:int) -> Optional[AudioProcess]:
    try:
        wf = wave.open(audio, 'rb')
        audioHandler = AudioStreamHandler(WaveAudioStream(wf, len_frame), AudioDriver())
    except:
        print('cannot create audio handler')
        return None
    else:
        return AudioProcess(audioHandler)

from .core import AudioFeatureBundle
from .streams import VibrationStream
from .processes import VibrationProcess
from .drivers import PCF8591Driver

def get_vib_process(features:str, len_frame:int, mode:str):
    try:
        fb = AudioFeatureBundle.from_folder(features)
        vibStream = VibrationStream.from_feature_bundle(fb, len_frame, mode)
        vibHandler = StreamHandler(vibStream, PCF8591Driver())
    except:
        print('cannot create vibration handler')
        return None
    else:
        return VibrationProcess(vibHandler)

from multiprocessing import Queue

def launch_vibration(audio:str, len_audio_frame:int,
    feature_dir:str, len_vib_frame:int, mode:str) -> List[Process]:
    audio_proc = get_audio_process(audio, len_audio_frame)
    if audio_proc is None:
        print('initial audio process failed. exit...')
        return

    vib_proc = get_vib_process(feature_dir, len_vib_frame, mode)
    if vib_proc is None:
        print('initial board process failed. exit...')
        return

    results, commands = Queue(), Queue()
    audio_proc.set_event_queues(commands, results)
    audio_proc.attach_vibration_proc(vib_proc)

    return [audio_proc, vib_proc]

# from .plot import PlotManager
# def launch_plotting(audio, feature_dir, mode, plots):
#     fm = FeatureManager.from_folder(feature_dir, mode)
#     if fm is None:
#         print('cannot create feature manager')
#         return
#     ctx = PlotManager(audio, fm, plots)
#     ctx.save_plots()
