from librosaContext import LibrosaContext
from matplotlibInvoker import MatplotlibInvoker

import multiprocessing
# Producer
class LibrosaContextProcess(multiprocessing.Process):
    def __init__(self, io_queue, feat_queue, ctx=None):
        super().__init__()
        self.io_queue = io_queue
        self.feat_queue = feat_queue
        self.ctx = ctx
    
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
                    self.feat_queue.put(features)
        self.feat_queue.put(None)
        return

class FeatureConsumerProcess(multiprocessing.Process):
    def __init__(self, feat_queue, consumer=None):
        super().__init__()
        self.feat_queue = feat_queue
        self.consumer = consumer
    
    def run(self):
        print('Feature Consumer Process Started..')
        while True:
            if not self.feat_queue.empty():
                features = self.feat_queue.get()
                if features is None:
                    print('Exiting Consumer Process...')
                    break
                else:
                    print(f'consumer proc feature size {len(features)}')
        return

from utils import load_audio
from librosaContext import DEFAULT_FRAME_LEN
from librosaContext import DEFAULT_HOP_LEN
def main():
    data, sr = load_audio()
    data = data[:DEFAULT_FRAME_LEN*10]

    ctx = LibrosaContext(sr=48000)
    ctx.strategy = [
        'rmse_1024_512',
        'pitchyin_2048_512_0.8']
    features = ctx.audio_features()

    ioQueue = multiprocessing.Queue()
    featQueue = multiprocessing.Queue()

    librosaProc = LibrosaContextProcess(io_queue=ioQueue, feat_queue=featQueue,
        ctx=ctx)
    featProc = FeatureConsumerProcess(feat_queue=featQueue)

    librosaProc.start()
    featProc.start()

    for start in range(0, DEFAULT_FRAME_LEN*9, DEFAULT_FRAME_LEN):
        # print(data[start:start+DEFAULT_FRAME_LEN].shape)
        ioQueue.put(data[start:start+DEFAULT_FRAME_LEN])

    ioQueue.put(None)

    librosaProc.join()
    featProc.join()

    # mi = MatplotlibInvoker(save_dir='plots')
    # mi.execture(features)

# call main function
main()