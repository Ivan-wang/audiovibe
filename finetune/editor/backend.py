import sys

sys.path.append('../..')
sys.path.append('..')

import os
import argparse
import time
import pickle
import librosa
import numpy as np
import multiprocessing

from vib_music import AdcDriver
from vib_music import BoardProcess
from vib_music import FeatureManager
from vib_music import FeatureExtractionManager
from vib_music.utils import get_audio_process
from vib_music.utils import get_board_process
from vib_music.utils import show_proc_bar
from vib_music.misc import init_vibration_extraction_config
from exp_utils import periodic_rectangle_generator, sine_wave_generator, rectangle_generator

AUDIO_SR = 44100
AUDIO_FRAME_LEN = 512
FRAME_TIME = AUDIO_FRAME_LEN / AUDIO_SR
FRAME_LEN = 24
VIB_TUNE_MODE = 'vibration_tune_mode'
MAGIC_NUM = 1.4


def load_atomic_wave_database(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)

    return data


def save_atomic_wave_database(data, path):
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def launch_atomicwave_vibration(atomicwave, duration, scale=1):
    atomicwave *= scale
    print('Atomic Wave:', atomicwave)
    MAGIC_NUM = 1.4
    num_frame = int(duration / FRAME_TIME * MAGIC_NUM)
    est_time = FRAME_TIME * num_frame
    # print(f'estimated duration {FRAME_TIME * num_frame:.3f}')
    sequence = np.stack([atomicwave] * num_frame, axis=0).astype(np.uint8)
    start = time.time()
    launch_vibration(sequence)
    end = time.time()
    act_time = end - start
    print(f'Running time {end - start:.3f} seconds.')
    print(f'Playing Done')


def exp_basic_launch_vibration(duration, freq, scale=[1,0], duty=0.5, wave_mode="periodic_rectangle", debug=0):
    """
    launch vibration for experiment
    :param duration: sequence duration
    :param freq: vibration frequency
    :param duty: if <1, duty ratio in each vibration period; if >=1, number of 1s at the center of period
    :param scale: a list of magnitude max and min, e.g. [75,25]; if mag is a number, min is set to 0 automatically (
    between 0 and 255)
    :param wave_mode: (str) if "periodic_rectangle", use periodic_rectangle generator; if "rectangle", use
    :param debug: (int) if 0, no debug; if 1, no vibration
    :return:
    """
    num_frame = int(duration / FRAME_TIME * MAGIC_NUM)
    est_time = FRAME_TIME * num_frame
    output_sr = FRAME_LEN / FRAME_TIME
    if wave_mode=="periodic_rectangle":
        sequence = periodic_rectangle_generator(scale, duty, freq, num_frame,
                                     frame_time=FRAME_TIME, frame_len=FRAME_LEN)
    elif wave_mode=="rectangle":
        sequence = rectangle_generator(scale, duty, num_frame,
                                     frame_time=FRAME_TIME, frame_len=FRAME_LEN)
    # sequence = sine_wave_generator(scale, freq, num_frame,
    #                              frame_time=FRAME_TIME, frame_len=24, zero_inserted_mode=1)
    else:
        print("wrong wave mode")
        sys.exit()
    # print(f'estimated duration {FRAME_TIME * num_frame:.3f}')
    end = 0
    start = 0
    if debug==0:
        start = time.time()
        launch_vibration(sequence)
        end = time.time()
    print(f'Running parameters:')
    print(f'output sample rate: {output_sr}')
    print(f'frequency: {freq} Hz')
    print(f'magnitude: {scale}')
    print(f'duty: {duty}')
    print(f'duration: {end - start:.3f} seconds.')
    print(f'seq max: {np.max(sequence):.2f}')
    print(f'seq min: {np.min(sequence):.2f}')
    print(f'Playing Done')


def exp_masking_launch_vibration(duration, freq, scale=1, duty=0.5, second_freq=10, second_scale=1, second_duty=1):
    """
    launch vibration for experiment
    :param duration: sequence duration
    :param freq: vibration frequency
    :param second_freq: (float) vibration frequency of second audio for masking
    :param scale: (list or float) a list of magnitude max and min, e.g. [75,25]; if mag is a number, min is set to 0
    automatically (between 0 and 255)
    :param second_scale: (list or float) a list of magnitude max and min of second audio for masking
    :param duty: if <1, duty ratio in each vibration period; if >=1, number of 1s at the center of period
    :param second_duty: (float or int) duty of second audio for masking
    :return:
    """
    num_frame = int(duration / FRAME_TIME * MAGIC_NUM)
    sequence_1 = periodic_rectangle_generator(scale, duty, freq, num_frame,
                                 frame_time=FRAME_TIME, frame_len=FRAME_LEN)
    sequence_2 = periodic_rectangle_generator(second_scale, second_duty, second_freq, num_frame,
                                 frame_time=FRAME_TIME, frame_len=FRAME_LEN)
    # sequence_3 = periodic_rectangle_generator(scale, duty, freq/4, num_frame,
    #                              frame_time=FRAME_TIME, frame_len=24)
    sequence = sequence_1 +sequence_2
    # print(f'estimated duration {FRAME_TIME * num_frame:.3f}')
    start = time.time()
    launch_vibration(sequence)
    end = time.time()
    act_time = end - start
    print(f'Running parameters:')
    print(f'frequency: {freq} Hz')
    print(f'magnitude: {scale}')
    print(f'duty: {duty}')
    print(f'second frequency: {second_freq} Hz')
    print(f'second magnitude: {second_scale}')
    print(f'second duty: {second_duty}')
    print(f'duration: {end - start:.3f} seconds.')
    print(f'seq max: {np.max(sequence):.2f}')
    print(f'seq min: {np.min(sequence):.2f}')
    print(f'Playing Done')

def launch_vibration(sequence):
    driver = AdcDriver(sequence)

    if not driver.on_start():
        raise RuntimeError('Driver initializing failed.')

    vib_proc = BoardProcess(driver, None)
    vib_proc.start()
    vib_proc.join()


def launch_vib_mode(audio, fm, transforms, atomic_wave):
    # update vibration mode
    @FeatureManager.vibration_mode(over_ride=True)
    def vibration_tune_mode(featManager:FeatureManager):
        rmse = featManager.feature_data('rmse').copy()
        rmse = transforms.apply_all(rmse, curve=False)

        vib_seq = rmse.reshape((-1, 1))
        wave = atomic_wave.reshape((1, -1))

        vib_seq = vib_seq * wave
        return vib_seq
    # vib_seq = fm.vibration_sequence(cached=False)
    # print(vib_seq[:10])

    driver = AdcDriver(fm.vibration_sequence(cached=False))

    audio_sem = multiprocessing.Semaphore()
    vib_sem = multiprocessing.Semaphore()

    frame_len = fm.frame_len()
    audio_proc = get_audio_process(audio, frame_len, audio_sem, vib_sem)
    if audio_proc is None:
        print('initial audio process failed. exit...')
        return

    board_proc = get_board_process(driver, audio_sem)
    if board_proc is None:
        print('initial board process failed. exit...')
        return

    # show prograss bar here
    sample_len = fm.sample_len()
    num_frame = (sample_len + frame_len - 1) // frame_len

    board_proc.start()
    audio_proc.start()

    show_proc_bar(num_frame, vib_sem)

    board_proc.join()
    audio_proc.join()


def load_audio(audio_path, use_cache=False):
    # load audio data
    audio, _ = librosa.load(audio_path, sr=None)

    # extract or load features
    DATA_DIR = './features'
    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)

    feature_folder = os.path.basename(audio_path).split('.')[0]
    feature_folder = os.path.join(DATA_DIR, feature_folder)
    if not use_cache or not os.path.isdir(feature_folder):
        # extract and save features
        librosa_config = init_vibration_extraction_config()
        librosa_config['audio'] = audio_path
        librosa_config['len_hop'] = 512  # hardcoded: HOP_LEN = 512

        librosa_config['stgs']['rmse'] = {
            'len_window': 2048,  # harded coded: WIN_LEN = 2048
        }
        librosa_config['stgs']['melspec'] = {
            'len_window': 2048,  # hard coded: WIN_LEN = 2048
            'n_mels': 128,  # hard coded: N_MELS = 128
            'fmax': None  # hard coded: F_MAX = NONE
        }

        ctx = FeatureExtractionManager.from_config(librosa_config)
        ctx.save_features(root=DATA_DIR)

    fm = FeatureManager.from_folder(feature_folder, mode='vibration_tune_mode')

    return audio, fm


# TODO: reuse plot manager for drawing
def draw_rmse(audio, sr, hop_len, rmse, ax):
    ax.cla()

    librosa.display.waveplot(audio, sr=sr, ax=ax)
    times = librosa.times_like(rmse, sr=sr, hop_length=hop_len)
    ax.plot(times, rmse, 'r')
    ax.set_xlim(xmin=0, xmax=times[-1])


from collections import namedtuple

Transform = namedtuple('Transform', ('name', 'params'))


class TransformQueue(object):
    def __init__(self):
        self.transforms = []
        self.transform_func = {
            'linear': lambda data, slope, bias: self.__linear_transform(data, slope, bias),
            'power': lambda data, power: self.__power_transform(data, power),
            'norm-std': lambda data, mean, std: self.__norm_transform(data, mean, std),
            'log': lambda data, shift: self.__log_transform(data, shift),
            'norm-min-max': lambda data, min_val, max_val: self.__norm_min_max_transform(data, min_val, max_val)
        }

    def get_transform(self, idx):
        if idx < len(self.transforms):
            return self.transforms[idx]
        else:
            return None

    def append(self, trans):
        self.transforms.append(trans)

    def delete(self, pos=-1):
        self.transforms.remove(self.transforms[pos])

    def move_up(self, pos=-1):
        if pos == 0:
            return
        self.transforms[pos], self.transforms[pos - 1] = self.transforms[pos - 1], self.transforms[pos]

    def move_down(self, pos=-1):
        if pos == -1 or pos == len(self.transforms) - 1:
            return

        self.transforms[pos], self.transforms[pos + 1] = self.transforms[pos + 1], self.transforms[pos]

    def update(self, params, pos):
        self.transforms[pos] = Transform(self.transforms[pos].name, params)

    def transform_list(self):
        return self.transforms

    def apply_transform(self, data, t, curve=True):
        if curve and t.name == 'norm':
            return data
        else:
            return self.transform_func[t.name](data, *t.params)

    def apply_all(self, data, curve=True):
        for t in self.transforms:
            data = self.apply_transform(data, t, curve)
        return data

    def save_transforms(self, name):
        with open(name, 'wb') as f:
            pickle.dump(self.transforms, f)

    def load_transforms(self, name):
        with open(name, 'rb') as f:
            self.transforms = pickle.load(f)

    def __len__(self):
        return len(self.transforms)

    def __linear_transform(self, data, slope, bias):
        out = data * slope + bias
        out = np.clip(out, 0, 1)
        return out

    def __power_transform(self, data, power):
        out = np.power(data, power)
        out = np.clip(out, 0, 1)
        return out

    def __norm_transform(self, data, mean, std):
        out = mean + (data - data.mean()) / data.std() * std
        out = np.clip(out, 0, 1)
        return out

    def __log_transform(self, data, gamma):
        out = np.log(1 + data) * gamma
        out = np.clip(out, 0, 1)
        return out
    # 
    def __norm_min_max_transform(self, data, min_val, max_val):
        if (min_val >= max_val):
            print('Min value is greater than max value')
            return data
        out = (data-data.min()) / (data.max()-data.min())
        out = out * (max_val-min_val) + min_val

        return out


if __name__ == '__main__':
    # scale = [200, 0]
    # duration = 10.0
    # freq = 1
    # duty = [[1,1.2], [4.2, 9.0]]
    # exp_basic_launch_vibration(duration, freq, scale, duty, wave_mode="rectangle")
    # time.sleep(5.0)
    # scale = [200, 0]
    # duration = 1.0
    # freq = 1
    # duty = 1500
    # exp_basic_launch_vibration(duration, freq, scale, duty)
    # exp_masking_launch_vibration(duration, freq, scale, duty)

    # sys.argv = ["backend.py", "--scale", "80:0", "--freq", "100", "--duty", "1", "--duration", "2.0",
    #             "--second-scale", "80:0", "--second-freq", "80", "--second-duty", "3",
    #             "--mode", "complex_rectangle"]
    # sys.argv = ["backend.py", "--scale", "80:0", "--freq", "20", "--duty", "30", "--duration", "2.0",
    #             "--mode", "periodic_rectangle"]

    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", help="max and min magnitude, delimitered by ':'")
    parser.add_argument("--freq", type=float, help="frequency for periodic signal")
    parser.add_argument("--duty", help="duty information of signal. Within list, delimitered by ':'; Between list, "
                                       "delimitered by ';'. E.G 1:1.2;2.0:3.0 => [[1,1.2],[2.0,3.0]")
    parser.add_argument("--second-scale", default="100:0", help="scale for second audio, if mode is 'complex_rectangle'")
    parser.add_argument("--second-freq", default="50", type=float, help="frequency for second audio, if mode is "
                                                                        "'complex_rectangle'")
    parser.add_argument("--second-duty", default="0.5", help="duty for second audio, if mode is 'complex_rectangle'")
    parser.add_argument("--duration", help="signal duration")
    parser.add_argument("--mode", default="periodic_rectangle", help="experiment mode")
    args = parser.parse_args()
    scale = args.scale
    freq = args.freq
    duty = args.duty
    dura = args.duration
    mode = args.mode
    second_freq = args.second_freq
    second_duty = args.second_duty
    second_scale = args.second_scale

    # process arguments
    # scale
    def process_scale(scale):
        scale = scale.split(":")
        if isinstance(scale, list):
            if len(scale)>1:
                scale = [float(scale[0]), float(scale[1])]
            else:
                scale = float(scale[0])
        else:
            scale = float(scale)
        return scale
    scale = process_scale(scale)
    second_scale = process_scale(second_scale)
    # frequence
    freq = float(freq)
    second_freq = float(second_freq)
    # duration
    dura = float(dura)
    # duty
    def process_duty(duty):
        if ";" in duty:
            raw_duty = duty.split(";")
            duty = []
            for s in raw_duty:
                tmp = s.split(":")
                duty.append([float(tmp[0]), float(tmp[1])])
        else:
            duty = float(duty)
        return duty
    duty = process_duty(duty)
    second_duty = process_duty(second_duty)
    # print args
    print(f'--scale: {scale}')
    print(f'--freq: {freq}')
    print(f'--duty: {duty}')
    print(f'--second-scale: {second_scale}')
    print(f'--second-freq: {second_freq}')
    print(f'--second-duty: {second_duty}')
    print(f'--duration: {dura}')
    print(f'--mode: {mode}')

    # run experiment
    if mode == "periodic_rectangle":
        exp_basic_launch_vibration(dura, freq, scale, duty, wave_mode="periodic_rectangle")
    elif mode == "rectangle":
        exp_basic_launch_vibration(dura, freq, scale, duty, wave_mode="rectangle")
    elif mode == "complex_rectangle":
        exp_masking_launch_vibration(dura, freq, scale, duty,
                                     second_freq=second_freq, second_scale=second_scale, second_duty=second_duty)
