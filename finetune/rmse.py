import sys
import numpy as np
import argparse
from typing import Optional
sys.path.append('..')

from vib_music import LiveVibrationStream, get_audio_process
from vib_music import VibrationProcess, LiveStreamHandler
from vib_music import UARTDriver
from vib_editor import launch_vibration


class RMSEVibrationStream(LiveVibrationStream):
    def __init__(self, hoplen:int=1024, len_window:int=2048) -> None:
        super().__init__()
        self.len_window : int = len_window
        self.hoplen : int = hoplen
        self.remain : int = len_window - hoplen
        self.buffer : Optional[np.ndarray] = None
    
    def init_stream(self) -> None:
        self.buffer = np.zeros((self.len_window,))

    def readframe(self, what):
        buffer = np.reshape(what, (-1, self.hoplen))
        num_frame = buffer.shape[0]
        ret = np.zeros((num_frame, ))
        for i in range(num_frame):
            self.buffer[:self.remain] = self.buffer[self.hoplen:]
            self.buffer[self.remain:] = buffer[i]
            ret[i] = self.buffer.mean()

        ret_dict = {
            'CH': '1 0 Z Z',
            'volt': ret.mean(),
            'freq': 1000,
            'duty': 50
        } 
        return ret_dict
    
    def clear_buffer(self) -> None:
        self.init_stream()

def get_parser():
    p = argparse.ArgumentParser(conflict_handler='resolve')
    p.add_argument('--audio', type=str)
    p.add_argument('--len-hop', type=int, default=1024)
    p.add_argument('--len-window', type=int, default=2048)

    return p


def main():
    p = get_parser()
    opt = p.parse_args()
    print(opt)

    music_proc = get_audio_process(opt.audio, opt.len_hop)

    data = RMSEVibrationStream(opt.len_hop, opt.len_window)
    driver = UARTDriver()
    handler = LiveStreamHandler(data, driver)
    vib_proc = VibrationProcess(handler)

    launch_vibration(None, [music_proc, vib_proc])

main()