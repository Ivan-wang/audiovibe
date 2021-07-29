from librosaContext import LibrosaContext
from vibrationEncoder import VibrationEncoder
from matplotlibInvoker import MatplotlibInvoker

import multiprocessing
# Producer
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

from utils import load_audio
from librosaContext import DEFAULT_FRAME_LEN
from librosaContext import DEFAULT_HOP_LEN

from config import load_config
def main():
    data, sr = load_audio()
    data = data[:DEFAULT_FRAME_LEN*10]

    ctx, venc, invoker = load_config('configs/demo.yaml')

    io_queue = multiprocessing.Queue()
    vib_queue = multiprocessing.Queue()

    librosa_proc = LibrosaContextProcess(io_queue=io_queue, vib_queue=vib_queue,
        ctx=ctx, enc=venc)
    board_proc = BroadProcess(vib_queue=vib_queue, invoker=invoker)

    librosa_proc.start()
    board_proc.start()

    for start in range(0, DEFAULT_FRAME_LEN*9, DEFAULT_FRAME_LEN):
        # print(data[start:start+DEFAULT_FRAME_LEN].shape)
        io_queue.put(data[start:start+DEFAULT_FRAME_LEN])

    io_queue.put(None)

    librosa_proc.join()
    board_proc.join()

# call main function
main()