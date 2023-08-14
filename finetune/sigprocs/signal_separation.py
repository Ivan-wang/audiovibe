# 3/3/22
# Fei Tao
# taofei@feathervibe.com
# separate audio sources

import librosa
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


def convert_l_sec_to_frames(L_h_sec, Fs=22050, N=1024, H=512):
    """Convert filter length parameter from seconds to frame indices

    Notebook: C8/C8S1_HPS.ipynb

    Args:
        L_h_sec (float): Filter length (in seconds)
        Fs (scalar): Sample rate (Default value = 22050)
        N (int): Window size (Default value = 1024)
        H (int): Hop size (Default value = 512)

    Returns:
        L_h (int): Filter length (in samples)
    """
    L_h = int(np.ceil(L_h_sec * Fs / H))
    return L_h


def convert_l_hertz_to_bins(L_p_Hz, Fs=22050, N=1024, H=512):
    """Convert filter length parameter from Hertz to frequency bins

    Notebook: C8/C8S1_HPS.ipynb

    Args:
        L_p_Hz (float): Filter length (in Hertz)
        Fs (scalar): Sample rate (Default value = 22050)
        N (int): Window size (Default value = 1024)
        H (int): Hop size (Default value = 512)

    Returns:
        L_p (int): Filter length (in frequency bins)
    """
    L_p = int(np.ceil(L_p_Hz * N / Fs))
    return L_p


def make_integer_odd(n):
    """Convert integer into odd integer

    Notebook: C8/C8S1_HPS.ipynb

    Args:
        n (int): Integer

    Returns:
        n (int): Odd integer
    """
    if n % 2 == 0:
        n += 1
    return n


def band_separate(feat, split_bin_nums=[20]):
    """
    split input melspec feature given split boundaries
    :param feat: (numpy array) (mel)spectrogram (dim, time)
    :param split_bin_nums: (list of integer) split boundary in bin number, must be ascending
    :return:
    """
    assert split_bin_nums==sorted(split_bin_nums), "split_bin_nums must be ascending"
    final_list = []
    prev_bound = 0
    for split_bound in split_bin_nums:
        temp_feat = feat[prev_bound:split_bound, :]
        final_list.append(temp_feat)
        prev_bound = split_bound
    temp_feat = feat[prev_bound:, :]
    final_list.append(temp_feat)

    return final_list


def hrps(power_spec, sr, len_harmonic_filt, len_percusive_filt, beta=2.0, len_window=512, len_hop=256,
         L_unit='physical'):
    """Harmonic-residual-percussive separation (HRPS) algorithm
    Args:
        power_spec (np.ndarray): power spectrogram
        sr (scalar): Sampling rate
        len_harmonic_filt (float): Horizontal median filter length given in seconds or frames
        len_percusive_filt (float): Percussive median filter length given in Hertz or bins
        beta (float): Separation factor (Default value = 2.0)
        len_window (int): Frame length
        len_hop (int): Hopsize
        L_unit (str): Adjusts unit, either 'pyhsical' or 'indices' (Default value = 'physical')
    Returns:
        power_spec_h (np.ndarray): Harmonic signal
        power_spec_p (np.ndarray): Percussive signal
        power_spec_r (np.ndarray): Residual signal
        M_h (np.ndarray): Harmonic mask
        M_p (np.ndarray): Percussive mask
        M_r (np.ndarray): Residual mask
    """
    assert L_unit in ['physical', 'indices']
    # median filtering
    if L_unit == 'physical':
        len_harmonic_filt = convert_l_sec_to_frames(L_h_sec=len_harmonic_filt, Fs=sr, N=len_window, H=len_hop)
        len_percusive_filt = convert_l_hertz_to_bins(L_p_Hz=len_percusive_filt, Fs=sr, N=len_window, H=len_hop)
    L_h = make_integer_odd(len_harmonic_filt)
    L_p = make_integer_odd(len_percusive_filt)
    # ### debug print ###
    # print(f"harmonic len {len_harmonic_filt}, percusive len {len_percusive_filt}")
    # ######
    Y_h = signal.medfilt(power_spec, [1, L_h])
    Y_p = signal.medfilt(power_spec, [L_p, 1])
    # masking
    M_h = np.int8(Y_h >= beta * Y_p)
    M_p = np.int8(Y_p > beta * Y_h)
    M_r = 1 - (M_h + M_p)
    power_spec_h = power_spec * M_h
    power_spec_p = power_spec * M_p
    power_spec_r = power_spec * M_r

    return power_spec_h, power_spec_p, power_spec_r, M_h, M_p, M_r