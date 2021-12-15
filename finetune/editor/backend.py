import sys
sys.path.append('../..')

import numpy as np
from vib_music import AdcDriver
from vib_music import BoardProcess

FRAME_TIME = 0.0116

def launch_atomicwave_vibration(atomicwave, duration, scale=1):
    atomicwave *= scale
    num_frame = duration / FRAME_TIME
    sequence = np.concatenate([atomicwave]*num_frame, dtype=np.uint8)
    launch_vibration(sequence)

def launch_vibration(sequence):
    driver = AdcDriver(sequence)

    if not driver.on_start():
        raise RuntimeError('Driver initializing failed.')

    vib_proc = BoardProcess(driver, None)
    vib_proc.start()
    vib_proc.join()

if __name__ == '__main__':
    waveform = np.array([0.01] * 8 + [0.99] * 4 + [0.01] * 8 + [0.99] * 4),
    scale = 100
    duration = 2.0
    launch_atomicwave_vibration(waveform, duration, scale)
