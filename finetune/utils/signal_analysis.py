# audio signal analyzers

from scipy.signal import argrelextrema
from scipy.stats import zscore
from sklearn.mixture import GaussianMixture
import librosa, copy
import numpy as np
from scipy.ndimage import convolve1d
import matplotlib.pyplot as plt


def find_bandwidth(bin_ind, spectral, bin_freqs, cut_off=0.5):
    """
    find the bandwidth given STFT bin number, spectral, and frequency of each bin
    """
    curr_magnitude = spectral[bin_ind]
    curr_threshold = cut_off * curr_magnitude    # get cut-off threshold
    curr_cands = np.where(spectral<=curr_threshold)[0]    # find all candidates which are lower than threshold
    curr_diff = curr_cands - bin_ind    # get distance between curr bin and all candidates
    # find where sign change in the diff list (indicating the lower and upper bound indexes for bandwidth)
    curr_sign_change = curr_diff[:-1] * curr_diff[1:]    # every point multiply its following point
    curr_sign_change_zero = np.where(curr_sign_change==0)[0]    # there should be no zero distance
    assert len(curr_sign_change_zero)==0, "zero occurs in sign change detection for BW determination"
    curr_sign_change = np.where(curr_sign_change<0)[0]    # find negative multiplication meaning sign changed
    curr_upper_index = len(curr_diff)-1
    curr_lower_index = 0
    curr_bw = -1
    if len(curr_sign_change)==0:    # if there no negative multiplication, we hit the either extreme candidate
        if curr_diff[0]>0: curr_upper_index = 0    # if first candidate is positive, our peak index is too low, we set the first candidate as upper bound
        elif curr_diff[-1]<0: curr_lower_index = len(curr_diff)-1    # if last candidate is negative, our peak index is too high, we set the last candidate as lower bound
        else:
            assert False, "wrong sign change detection"
    if curr_upper_index != len(curr_diff)-1:    # if upper index is set, we cannot have lower bound, so use half bandwidth to get full bandwidth
        curr_upper_bound = curr_cands[curr_upper_index]
        curr_bw = 2*(abs(bin_freqs[curr_upper_bound]-bin_freqs[bin_ind]))
    if curr_lower_index != 0:    # if lower index is set, we cannot have upper bound
        curr_lower_bound = curr_cands[curr_lower_index]
        curr_bw = 2*(abs(bin_freqs[curr_lower_bound]-bin_freqs[bin_ind]))
    if curr_bw ==-1:    # if full bandwidth is not set yet, we have normal upper and lower bounds
        curr_sign_change = curr_sign_change[0]
        curr_lower_bound = curr_cands[curr_sign_change]
        curr_upper_bound = curr_cands[curr_sign_change+1]
        curr_bw = abs(bin_freqs[curr_upper_bound]-bin_freqs[curr_lower_bound])
    return curr_bw


def remove_harmonics(peak_mask, spec, bin_freqs, mode='exhaust'):
    """
    remove harmonic peaks from the given peak masks and STFT
    """
    # frequency to bin number
    def freq2bin(freq, bin_freqs):
        diffs = np.abs(bin_freqs - freq)
        ind = np.argmin(diffs)
        return ind

    ori_mask = copy.deepcopy(peak_mask)    # store the original mask
    spec_masked = spec * peak_mask
    peak_dim, peak_time = peak_mask.shape
    for i in range(peak_time):
        if np.sum(peak_mask[:, i])==0: continue    # no peak at current time
        peak_search_range = peak_dim // 2 + 1
        search_peaks = spec_masked[:peak_search_range, i]
        search_index = np.linspace(0, peak_search_range-1, peak_search_range, dtype=int)
        search_peaks = np.stack((search_index, search_peaks), axis=1)
        search_peaks_queue = search_peaks[:, 1].argsort()    # sort ascend based on peak value
        search_peaks_queue = search_peaks_queue[::-1]    # reassign descending
        if mode=="exhaust":
            srh_len = len(search_peaks_queue)    # if exhaust, remove all harmonics
        else:
            srh_len = 1    # if not, only remove harmonics of the strongest peak
        # iterate from largets to smallest peaks
        main_peaks = []
        for si in range(0, srh_len):
            if search_peaks[search_peaks_queue[si], 1]==0: continue    # if no peak, skip
            if si in main_peaks: continue    # skip if this is a main peak
            main_peaks.append(si)    # we skip peak that have been processed avoiding remove strong peaks
            curr_peak_ind = int(search_peaks[search_peaks_queue[si],0])    # index of current peak
            curr_peak_freq = bin_freqs[curr_peak_ind]
            curr_peak_bw = find_bandwidth(curr_peak_ind, spec[:, i], bin_freqs)    # get band width
            harm_factor = 2
            # loop over all harmonics until the largest freqeuncy
            while curr_peak_freq*harm_factor < bin_freqs[-1]:
                curr_harm_freq = curr_peak_freq * harm_factor
                curr_harm_band = curr_peak_bw * harm_factor    # current harmonic's bandwidth
                curr_harm_start_freq = curr_harm_freq - curr_harm_band/2
                curr_harm_end_freq = curr_harm_freq + curr_harm_band/2
                curr_harm_start_ind = freq2bin(curr_harm_start_freq, bin_freqs)
                curr_harm_end_ind = freq2bin(curr_harm_end_freq, bin_freqs)
                peak_mask[curr_harm_start_ind:curr_harm_end_ind+1, i] = 0    # mask peaks in harmonic band
                harm_factor += 1    # go to next harmonic
    return peak_mask, ori_mask


def extract_peaks(spec, peak_movlen=5, peak_relativeth=4, peak_globalth=50):
    """
    extract peaks from spectrogram (linear or mel-scale)
    """
    feat_dim, _ = spec.shape
    spec_mask = np.ones_like(spec)    # mask of spec
    spec_db = librosa.power_to_db(spec)    # convert to db scale

    # extract peaks along mels
    # exclude all-same time point
    spec_var = np.var(spec_db, axis=0)
    spec_var_mask = np.ones_like(spec_var)
    spec_var_mask[spec_var==0] = 0    # if variance is zeros, all the elements have the same value (no peak exists)
    spec_var_mask_mat = np.tile(spec_var_mask, (feat_dim, 1))
    spec_mask = spec_mask * spec_var_mask_mat

    # move average
    ma_kernel = [1/peak_movlen] * peak_movlen
    spec_ma = convolve1d(spec_db, weights=ma_kernel, axis=0, mode='nearest')
    spec_ma_diff = spec_db - spec_ma    # value over local average
    spec_mask[spec_ma_diff<peak_relativeth] = 0    # set mask based on local threshold

    # ### debug ###
    # plt.figure()
    # fig, ax = plt.subplots()
    # img = librosa.display.specshow(spec_mask, ax=ax)
    # plt.savefig("../plots/move_mask.png")
    # plt.close()
    # plt.figure()
    # fig, ax = plt.subplots(nrows=2)
    # ax[0].plot(np.linspace(0, len(spec_mask[:,0])-1, len(spec_mask[:,0])), spec[:,9])
    # ax[1].plot(np.linspace(0, len(spec_mask[:,0])-1, len(spec_mask[:,0])), spec_mask[:,9])
    # plt.savefig("../plots/spec_peaks_move.png")
    # plt.close()
    # ######

    # global threshold
    spec_max = np.max(spec_db, axis=0)    # max at each time
    global_th = spec_max - peak_globalth    # threshold has determined difference from max amplitude at each time
    global_th_mat = np.tile(global_th, (feat_dim, 1))
    spec_global_diff = spec_db - global_th_mat    # value over threshold
    spec_mask[spec_global_diff<0] = 0    # set mask based on global threshold

    # ### debug ###
    # plt.figure()
    # fig, ax = plt.subplots()
    # img = librosa.display.specshow(spec_mask, ax=ax)
    # plt.savefig("../plots/global_mask.png")
    # plt.close()
    # plt.figure()
    # fig, ax = plt.subplots(nrows=2)
    # ax[0].plot(np.linspace(0, len(spec_mask[:,0])-1, len(spec_mask[:,0])), spec[:,9])
    # ax[1].plot(np.linspace(0, len(spec_mask[:,0])-1, len(spec_mask[:,0])), spec_mask[:,9])
    # plt.savefig("../plots/spec_peaks_global.png")
    # plt.close()
    # ######

    # local maxima
    spec_local_maxima_ind = argrelextrema(spec_db, np.greater, axis=0)
    spec_local_maxima_ind = np.array(spec_local_maxima_ind).transpose()
    spec_mask_localmax = np.zeros_like(spec_mask)
    spec_mask_localmax[spec_local_maxima_ind[:,0], spec_local_maxima_ind[:,1]] = 1

    # combine to all masks
    spec_mask = spec_mask * spec_mask_localmax

    # ### debug ###
    # plt.figure()
    # fig, ax = plt.subplots()
    # img = librosa.display.specshow(spec_mask, ax=ax)
    # plt.savefig("../plots/maxima_mask.png")
    # plt.close()
    # plt.figure()
    # fig, ax = plt.subplots(nrows=2)
    # ax[0].plot(np.linspace(0, len(spec_mask[:,0])-1, len(spec_mask[:,0])), spec[:,9])
    # ax[1].plot(np.linspace(0, len(spec_mask[:,0])-1, len(spec_mask[:,0])), spec_mask[:,9])
    # plt.savefig("../plots/spec_peaks_maxima.png")
    # plt.close()
    # ######

    return spec_mask