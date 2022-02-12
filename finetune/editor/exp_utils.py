# 2/11/22
# Fei Tao
# taofei@feathervibe.com

import numpy as np
import math


def periodic_rectangle_generator(mag, duty_ratio, freq, frame_num,
                                 frame_time=512/44100.0, frame_len=24):
    """
    pulse wave generator, given magnitude and frequency
    :param mag: magnitude
    :param duty_ratio: duty ratio for each vibration period
    :param freq: vibration frequency
    :param frame_num: total number of frames in output vibration sequence
    :param frame_time: duration of each frame in output vibration sequence
    :param frame_len: output vibration frame length
    :return:
    """
    assert isinstance(frame_num, int), "frame_num should be int"
    assert isinstance(frame_len, int), "frame_len should be int"
    output_sr = frame_len / frame_time    # output sample rate (will be rounded later) (CAUTION float!)
    assert freq<output_sr/2, "frequency too high !"
    period_sample_num = output_sr / freq    # sample number in each period (CAUTION float!)
    period_load_num = period_sample_num * duty_ratio    # number of 1s in each period (CAUTION float!)
    period_empty_num = int(period_sample_num - round(period_load_num))
    assert period_empty_num>0 and period_load_num>0, "wrong duty ratio !"
    period_num = math.ceil((frame_num * frame_len) / round(period_sample_num))+1    # number of periods in total
    # construct periodic sequence
    base_seq = np.ones((int(round(period_sample_num)),))
    base_seq[:period_empty_num] = 0    # set zeros according to duty ratio
    total_seq = np.tile(base_seq, period_num)    # repeat periodically
    final_seq = total_seq[:int(frame_num*frame_len)]
    # scale output
    final_seq *= mag
    # turn 1-D sequence to 2-D for output
    final_array = np.reshape(final_seq,(frame_num, frame_len)).astype(np.uint8)

    return final_array