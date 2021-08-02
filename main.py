from librosaContext import LibrosaContext
from vibrationEncoder import VibrationEncoder
from config import PLP_FRAME, FRAME_LEN
# from matplotlibInvoker import MatplotlibInvoker

import multiprocessing
import wave
import pyaudio
# Producer
class AudioProcess(multiprocessing.Process):
    def __init__(self, filename, io_queue=None):
        super(AudioProcess, self).__init__()
        self.filename = filename
        # NOTE: do not create auido object here!
        # self.audio = pyaudio.PyAudio()
        # self.sr = librosa.get_samplerate(filename)
    
    def run(self):
        print('init feature proc...')
        # IMPORTANT: initialize the audio within one process
        # Don't share it across different processes
        audio = pyaudio.PyAudio()
        wf = wave.open(self.filename, 'rb')
        print('loaded wav file...')
        stream = audio.open(
            format=audio.get_format_from_width(wf.getsampwidth()),
            channels = wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        
        print('loading...')
        while True:
            data = wf.readframes(1024)
            if len(data) > 0:
                stream.write(data)
            else:
                break
        
        print('feature proc exit...')
        stream.stop_stream()
        stream.close()

# class AudioIOProcess(multiprocessing.Process):
#     def __init__(self, audio, sr, io_queue):
#         super(AudioIOProcess, self).__init__()

#         self.audio = audio
#         self.sr = sr
#         self.io_queue = io_queue
    
#     def run(self):
#         # TODO: use blocking calls to load chunk
#         step = FRAME_LEN - HOP_LEN
#         end = self.audio.shape[0] - step
#         for start in range(0, end, step):
#             # print(data[start:start+DEFAULT_FRAME_LEN].shape)
#             self.io_queue.put(self.audio[start:start+FRAME_LEN])
#         self.io_queue.put(None)
#         return

class LibrosaContextProcess(multiprocessing.Process):
    def __init__(self, io_queue, vib_queue, ctx=None, enc=None):
        super().__init__()
        self.io_queue = io_queue
        self.vib_queue = vib_queue 
        self.ctx = ctx
        self.enc = enc
    
    def run(self):
        # collecte frame from IO Q, extract features, put features to features Q
        print('Librosa Context Process Started..')
        while True:
            if not self.io_queue.empty():
                chunk = self.io_queue.get()
                if chunk is None:
                    break
                else:
                    self.ctx.sound = chunk
                    features = self.ctx.audio_features()
                    vibertion = self.enc.fit(features)
                    self.vib_queue.put(vibertion)
        self.vib_queue.put(None)
        return

class BroadProcess(multiprocessing.Process):
    def __init__(self, vib_queue, invoker=None):
        super().__init__()
        self.vib_queue = vib_queue
        self.invoker = invoker
    
    def run(self):
        print('Feature Consumer Process Started..')
        self.invoker.on_start()

        while True:
            if not self.vib_queue.empty():
                vib = self.vib_queue.get()
                if vib is None:
                    print('Exiting Consumer Process...')
                    break
                else:
                    self.invoker.dispatch(vib)
        return

# from utils import load_audio
# from librosaContext import FRAME_LEN
# from librosaContext import HOP_LEN

# from config import load_config
import subprocess
def main():
    feat_proc = FeatureProcess('audio/YellowRiverSliced.wav')

    # subprocess.Popen(['omxplayer', 'audio/YellowRiverSliced.wav'])
    feat_proc.start()
    feat_proc.join()
    # data, sr = load_audio()
    # data = data[:FRAME_LEN*10]
    # print(data.shape)

    # ctx, venc, invoker = load_config('configs/demo.yaml')

    # io_queue = multiprocessing.Queue()
    # vib_queue = multiprocessing.Queue()

    # audio_proc = AudioIOProcess(data, sr, io_queue)
    # # TODO: merge librosa and board procs
    # librosa_proc = LibrosaContextProcess(io_queue, vib_queue, ctx, venc)
    # board_proc = BroadProcess(vib_queue=vib_queue, invoker=invoker)

    # librosa_proc.start()
    # board_proc.start()

    # audio_proc.start()

    # audio_proc.join()

    # librosa_proc.join()
    # board_proc.join()

# call main function
main()