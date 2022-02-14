# 2/11/22
# Fei Tao
# taofei@feathervibe.com

import numpy as np
import math
import matplotlib.pyplot as plt


def periodic_rectangle_generator(mag, duty, freq, frame_num,
                                 frame_time=512/44100.0, frame_len=24):
    """
    pulse wave generator, given magnitude and frequency
    :param mag: a list of magnitude max and min, e.g. [75,25]; if mag is a number, min is set to 0 automatically
    :param duty: if <1, duty ratio in each vibration period; if >=1, number of 1s at the center of period
    :param freq: vibration frequency
    :param frame_num: total number of frames in output vibration sequence
    :param frame_time: duration of each frame in output vibration sequence
    :param frame_len: output vibration frame length
    :return:
    """
    assert isinstance(frame_num, int), "frame_num should be int"
    assert isinstance(frame_len, int), "frame_len should be int"
    assert duty>0, "duty must be postive"

    if not isinstance(mag, list):
        mag = [mag, 0]

    output_sr = frame_len / frame_time    # output sample rate (will be rounded later) (CAUTION float!)
    assert freq<output_sr/2, "frequency too high !"
    period_sample_num = output_sr / freq    # sample number in each period (CAUTION float!)
    # construct base sequence
    base_seq = np.ones((int(round(period_sample_num)),))
    if duty<1:
        period_load_num = period_sample_num * duty    # number of 1s in each period (CAUTION float!)
        period_empty_num = int(period_sample_num - round(period_load_num))
        assert period_empty_num>0 and period_load_num>0, "wrong duty ratio !"
        base_seq[:period_empty_num] = min(mag)/max(mag)    # set zeros according to duty ratio
    else:
        period_center = int(round(period_sample_num / 2))
        half_duty = int(round(duty / 2))
        center_left = period_center-half_duty
        base_seq[:center_left] = min(mag)/max(mag)
        base_seq[center_left+duty:] = min(mag)/max(mag)
    period_num = math.ceil((frame_num * frame_len) / round(period_sample_num))+1    # number of periods in total
    # construct periodic sequence
    total_seq = np.tile(base_seq, period_num)    # repeat periodically
    final_seq = total_seq[:int(frame_num*frame_len)]
    # scale output
    final_seq *= max(mag)
    # turn 1-D sequence to 2-D for output
    final_array = np.reshape(final_seq,(frame_num, frame_len)).astype(np.uint8)

    return final_array


def sine_wave_generator(mag, freq, frame_num,
                                 frame_time=512/44100.0, frame_len=24, zero_inserted_mode=1):
    """
    pulse wave generator, given magnitude and frequency
    :param mag: a list of magnitude max and min, e.g. [75,25]; if mag is a number, min is set to 0 automatically
    :param freq: vibration frequency
    :param frame_num: total number of frames in output vibration sequence
    :param frame_time: duration of each frame in output vibration sequence
    :param frame_len: output vibration frame length
    :return:
    """
    assert isinstance(frame_num, int), "frame_num should be int"
    assert isinstance(frame_len, int), "frame_len should be int"

    if not isinstance(mag, list):
        mag = [mag, 0]

    output_sr = frame_len / frame_time    # output sample rate (will be rounded later) (CAUTION float!)
    total_dura = int(math.ceil(frame_num * frame_time))    # total duration in seconds
    assert freq<output_sr/2, "frequency too high !"
    # construct sine wave
    time = np.arange(0, total_dura, 1 / output_sr)
    sinewave = np.sin(2 * np.pi * freq * time)
    final_seq = sinewave[:int(frame_num*frame_len)]
    # scale output
    final_seq *= max(mag)
    # offset waveform to make all number positive
    offset_seq = max(mag)*np.ones_like(final_seq)
    final_seq += offset_seq
    # insert zeros
    if zero_inserted_mode>0:
        final_seq[::(zero_inserted_mode+1)] = 0
    elif zero_inserted_mode<0:
        final_seq = final_seq
    else:
        final_seq = final_seq
    # # display waveform (TODO commented out when run)
    # plt.plot(final_seq)
    # plt.show()
    # turn 1-D sequence to 2-D for output
    final_array = np.reshape(final_seq,(frame_num, frame_len)).astype(np.uint8)

    return final_array