import sys
sys.path.append('../..')

import numpy as np
from vib_music import AdcDriver
from vib_music import BoardProcess
import time

FRAME_TIME = 0.0116

def launch_atomicwave_vibration(atomicwave, duration, scale=1):
    atomicwave *= scale
    MAGIC_NUM = 1.4
    num_frame = int(duration / FRAME_TIME * MAGIC_NUM)
    est_time = FRAME_TIME * num_frame 
    # print(f'estimated duration {FRAME_TIME * num_frame:.3f}')
    sequence = np.stack([atomicwave]*num_frame, axis=0).astype(np.uint8)
    start = time.time()
    launch_vibration(sequence)
    end = time.time()
    act_time = end-start
    print(f'Running time {end-start:.3f} seconds.')
    print(f'Playing Done')
    

def launch_vibration(sequence):
    driver = AdcDriver(sequence)

    if not driver.on_start():
        raise RuntimeError('Driver initializing failed.')

    vib_proc = BoardProcess(driver, None)
    vib_proc.start()
    vib_proc.join()

if __name__ == '__main__':
    waveform = np.array([0.01] * 8 + [0.99] * 4 + [0.01] * 8 + [0.99] * 4)
    scale = 75
    duration = 1.0
    launch_atomicwave_vibration(waveform, duration, scale)
