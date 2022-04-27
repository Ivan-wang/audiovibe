import numpy as np
from math import log, sqrt
import matplotlib.pyplot as plt
import librosa, sys
import librosa.display
from scipy.signal import argrelextrema
from scipy.stats import zscore
from sklearn.mixture import GaussianMixture
from scipy.ndimage import convolve1d
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import copy

# bn = 255

# bins = np.linspace(0., 1., bn, endpoint=True)
# mu_bins = [x*(log(1+bn*x)/log(1+bn)) for x in bins]
# sqrt_bins = [sqrt(x) for x in bins]
# plt.figure()
# plt.plot(bins, bins, "b-")
# plt.plot(bins, mu_bins, "r-")
# plt.plot(bins, sqrt_bins, "y-")
# plt.savefig("mu_law.png")
# print("hello")

def amplitude_envelope(signal, win_len, hop_len):
    return np.array([max(signal[i:i+win_len]) for i in range(0, signal.size, hop_len)])

def get_features(y, sr, slice_num):
    n_mels = 128
    n_mfcc = 13
    slice_num = int(slice_num)
    S = librosa.feature.melspectrogram(y, sr, n_mels=n_mels)
    mfcc = librosa.feature.mfcc(S=librosa.power_to_db(S), n_mfcc=n_mfcc)    # shape (dim, time)
    mfcc_padded = np.zeros((mfcc.shape[0], mfcc.shape[1]+2))
    mfcc_padded[:, :mfcc.shape[1]] = mfcc
    mfcc_delta = mfcc - mfcc_padded[:, 1:1+mfcc.shape[1]]
    mfcc_delta_delta = mfcc - mfcc_padded[:, 2:2+mfcc.shape[1]]
    # # moving average
    # ma_kernel = [1/slice_num] * slice_num
    # feature_vector = convolve1d(mfcc, weights=ma_kernel, axis=1, mode='nearest')
    # moving average without overlap
    mfcc_comb = np.zeros((mfcc.shape[0]*3, mfcc.shape[1]))
    mfcc_comb[:mfcc.shape[0], :] = mfcc
    mfcc_comb[mfcc.shape[0]:mfcc.shape[0]*2, :] = mfcc_delta
    mfcc_comb[mfcc.shape[0]*2:mfcc.shape[0]*3, :] = mfcc_delta_delta
    feature_vector = np.array([np.mean(mfcc[:, i:i+slice_num], axis=1) for i in range(0, mfcc.shape[1], slice_num)])
    return feature_vector.transpose()


def get_peaks(melspec, peak_movlen=5, peak_relativeth=4, peak_globalth=50):
    feat_dim, _ = melspec.shape
    melspec_mask = np.ones_like(melspec)    # mask of melspec
    melspec_db = librosa.power_to_db(melspec)    # convert to db scale

    # extract peaks along mels
    # exclude all-same time point
    melspec_var = np.var(melspec_db, axis=0)
    melspec_var_mask = np.ones_like(melspec_var)
    melspec_var_mask[melspec_var==0] = 0    # if variance is zeros, all the elements have the same value (no peak exists)
    melspec_var_mask_mat = np.tile(melspec_var_mask, (feat_dim, 1))
    melspec_mask = melspec_mask * melspec_var_mask_mat

    # move average
    ma_kernel = [1/peak_movlen] * peak_movlen
    melspec_ma = convolve1d(melspec_db, weights=ma_kernel, axis=0, mode='nearest')
    melspec_ma_diff = melspec_db - melspec_ma    # value over local average
    melspec_mask[melspec_ma_diff<peak_relativeth] = 0    # set mask based on local threshold

    # global threshold
    melspec_max = np.max(melspec_db, axis=0)    # max at each time
    global_th = melspec_max - peak_globalth    # threshold has determined difference from max amplitude at each time
    global_th_mat = np.tile(global_th, (feat_dim, 1))
    melspec_global_diff = melspec_db - global_th_mat    # value over threshold
    melspec_mask[melspec_global_diff<0] = 0    # set mask based on global threshold

    # local maxima
    melspec_local_maxima_ind = argrelextrema(melspec_db, np.greater, axis=0)
    melspec_local_maxima_ind = np.array(melspec_local_maxima_ind).transpose()
    melspec_mask_localmax = np.zeros_like(melspec_mask)
    melspec_mask_localmax[melspec_local_maxima_ind[:,0], melspec_local_maxima_ind[:,1]] = 1

    # combine to all masks
    melspec_mask = melspec_mask * melspec_mask_localmax

    # mask original mel-spec
    melspec_masked = melspec * melspec_mask

    return melspec_mask


def remove_harmonics(peak_mask, spec, bin_freqs, band_tol=0.3, band_min=50, mode='exhaust'):
    ori_mask = copy.deepcopy(peak_mask)

    def freq2bin(freq, bin_freqs):
        diffs = np.abs(bin_freqs - freq)
        ind = np.argmin(diffs)
        return ind

    def find_bandwidth(bin_ind, spectral, bin_freqs, cut_off=0.5):
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
        for si in range(0, srh_len):
            if search_peaks[search_peaks_queue[si], 1]==0: continue    # if no peak, skip
            curr_peak_ind = int(search_peaks[search_peaks_queue[si],0])    # index of current peak
            curr_peak_freq = bin_freqs[curr_peak_ind]
            curr_peak_bw = find_bandwidth(curr_peak_ind, spec[:, i], bin_freqs)    # get band width
            harm_factor = 2
            # loop over all harmonics until the largest freqeuncy
            while curr_peak_freq*harm_factor < bin_freqs[-1]:
                curr_harm_freq = curr_peak_freq * harm_factor
                curr_harm_ind = freq2bin(curr_harm_freq, bin_freqs)
                # only proceed when current harmonic is not masked yet
                if peak_mask[curr_harm_ind, i]!=0:
                    # curr_harm_band = max(band_tol*curr_harm_freq, band_min)    # get band width
                    curr_harm_band = curr_peak_bw * harm_factor
                    curr_harm_start_freq = curr_harm_freq - curr_harm_band/2
                    curr_harm_end_freq = curr_harm_freq + curr_harm_band/2
                    curr_harm_start_ind = freq2bin(curr_harm_start_freq, bin_freqs)
                    curr_harm_end_ind = freq2bin(curr_harm_end_freq, bin_freqs)
                    peak_mask[curr_harm_start_ind:curr_harm_end_ind+1, i] = 0    # mask peaks in harmonic band
                harm_factor += 1    # go to next harmonic
    return peak_mask, ori_mask



y, sr = librosa.load("../audio/viol_22k.wav", mono=True)
# y = y[22050*28:22050*30]
hop_len = 256
win_len = 1024
y_stft = librosa.stft(y, n_fft=win_len, hop_length=hop_len)

bin_freqs = librosa.fft_frequencies(sr=sr, n_fft=win_len)
bin_freq_diff = bin_freqs[2]-bin_freqs[1]
peak_movlen = int(400 // bin_freq_diff)
if peak_movlen %2 ==0: peak_movlen+= 1

spec = np.abs(y_stft)
peak_mask = get_peaks(spec, peak_movlen=peak_movlen)
peak_mask_no_harm, peak_mask_with_harm = remove_harmonics(peak_mask, spec, bin_freqs)
mask_diff = np.abs(peak_mask_no_harm - peak_mask_with_harm)
print(np.sum(mask_diff))

### debug ###
melspec_masked_display = peak_mask_with_harm
melspec_db_masked = librosa.power_to_db(melspec_masked_display, ref=np.max)
melspec_masked_no_harm_display = peak_mask_no_harm
melspec_no_harm_db_masked = librosa.power_to_db(melspec_masked_no_harm_display, ref=np.max)
plt.figure()
fig, ax = plt.subplots(nrows=2, sharex=True)
img = librosa.display.specshow(melspec_db_masked, x_axis='time', ax=ax[0])
ax[0].set(title='With Harmonics')
img = librosa.display.specshow(melspec_no_harm_db_masked, x_axis='time', ax=ax[1])
ax[1].set(title='Without Harmonics')
plt.savefig("debug_mask.png")
sys.exit()
######

# f0, voiced_flag, voiced_probs = librosa.pyin(y, frame_length=win_len, hop_length=hop_len,
#                                             fmin=librosa.note_to_hz('C2'),
#                                             fmax=librosa.note_to_hz('C7'))
# times = librosa.times_like(f0)
# D = librosa.amplitude_to_db(np.abs(y_stft), ref=np.max)
# fig, ax = plt.subplots()
# img = librosa.display.specshow(D, x_axis='time', y_axis='log', ax=ax)
# ax.set(title='pYIN fundamental frequency estimation')
# fig.colorbar(img, ax=ax, format="%+2.f dB")
# ax.plot(times, f0, label='f0', color='cyan', linewidth=3)
# ax.plot(times, f0*2, label='f0', color='cyan', linewidth=3)
# ax.plot(times, f0*3, label='f0', color='cyan', linewidth=3)
# ax.plot(times, f0*4, label='f0', color='cyan', linewidth=3)
# ax.plot(times, f0*5, label='f0', color='cyan', linewidth=3)
# ax.plot(times, f0*6, label='f0', color='cyan', linewidth=3)
# ax.plot(times, f0*7, label='f0', color='cyan', linewidth=3)
# ax.legend(loc='upper right')
# plt.savefig("debug.png")

# feats = get_features(y, sr, (0.1*sr)//hop_len)

# epsilon = 1e-8
# pitches, magnitudes = librosa.piptrack(y=y, sr=sr, win_length=win_len, hop_length=hop_len)
# plt.figure()
# plt.imshow(magnitudes, cmap='hot', interpolation='nearest', aspect='auto')
# plt.savefig('debug.png')
# pitches_sum = np.sum(magnitudes, axis=0)
# pitches_max = np.max(magnitudes, axis=0)
# pitch_ratios = []
# for i in range(magnitudes.shape[1]):
#     if pitches_sum[i] >0:
#         pitch_ratios.append(pitches_max[i]/(pitches_sum[i]-pitches_max[i]+epsilon))
# D = np.abs(y_stft)
# spec_flux = np.sum(np.abs(D[:,:-1] - D[:, 1:]), axis=0)
# print(np.mean(pitch_ratios), np.mean(spec_flux))



# S, phase = librosa.magphase(y_stft)
# D = np.abs(y_stft)

# onset_strength = librosa.onset.onset_strength(S=D)
# onset_frames = librosa.onset.onset_detect(onset_envelope=onset_strength, units="frames", 
#                                     hop_length=hop_len, backtrack=False)
# spec_centroid = librosa.feature.spectral_centroid(S=S)[0]
# amp_envelope = amplitude_envelope(y, win_len=win_len, hop_len=hop_len)
# assert abs(len(amp_envelope)-len(spec_centroid))<2, "feature length mismatch"
# if len(amp_envelope)<len(spec_centroid):    # if amp_envelope is shorter, pad zeros
#     amp_envelope_temp = np.zeros_like(spec_centroid)
#     amp_envelope_temp[:len(amp_envelope)] = amp_envelope
# elif len(amp_envelope)>len(spec_centroid):    # if amp_envelope is longer, only get the beginning part
#     amp_envelope = amp_envelope[:len(spec_centroid)]

# # times = librosa.times_like(spec_centroid)
# # plt.figure(figsize=(20,10))
# # fig, ax = plt.subplots()
# # librosa.display.specshow(librosa.amplitude_to_db(S, ref=np.max),
# #                          y_axis='log', x_axis='time', ax=ax)
# # ax.plot(times, spec_centroid.T, label='Spectral centroid', color='w')
# # plt.savefig("debug_spec_cent.png")
# # plt.close()
# # plt.figure(figsize=(20,10))
# # fig, ax = plt.subplots()
# # librosa.display.specshow(librosa.amplitude_to_db(S, ref=np.max),
# #                          y_axis='log', x_axis='time', ax=ax)
# # ax.plot(times, amp_envelope.T, label='amplitude envelope', color='w')
# # plt.savefig("debug_amp_envelope.png")
# # sys.exit()

# onset_strength_min_frames = argrelextrema(onset_strength, np.less)[0]
# feat = np.zeros((2, len(onset_frames)))
# for i in range(len(onset_frames)):
#     # find onset area, 
#     # defined as the range between the onset_strength minimas before and after onset peak
#     onset_frame_diffs = onset_frames[i] - onset_strength_min_frames
#     temp_onset_frame_diffs = np.ones((onset_frame_diffs.size+1))
#     temp_onset_frame_diffs[1:] = onset_frame_diffs    # append 1 before the diff list
#     onset_frame_diffs = temp_onset_frame_diffs
#     onset_frame_sign = np.array(onset_frame_diffs[:-1]) * np.array(onset_frame_diffs[1:])
#     onset_ind = np.where(onset_frame_sign<0)[0]    # at this point, the diff changes signs, indicating peak occurs
#     assert len(onset_ind)==1, "multiple onset ranges found"
#     onset_start_ind = onset_ind[0] - 1    # adjust index, because we append 1 element at the beginning previously
#     if onset_start_ind<0:
#         onset_start_frame = 0
#     else:
#         onset_start_frame = onset_strength_min_frames[onset_start_ind]    # diff sign changed point is the minima before onset peak
#     onset_end_frame = onset_strength_min_frames[onset_start_ind+1]    # the ind after the diff sign changed point is the minima after onset peak
#     # amplitude envelope analysis
#     curr_amp_envelope = amp_envelope[onset_start_frame:onset_end_frame+1]
#     curr_amp_envelope_slopes = curr_amp_envelope[1:] - curr_amp_envelope[:-1]
#     feat[0,i] = np.mean(curr_amp_envelope_slopes)
#     # feat[1,i] = np.var(curr_amp_envelope_slopes)
#     # spectral centroid analysis
#     curr_spec_centroid = spec_centroid[onset_start_frame:onset_end_frame+1]
#     # feat[2,i] = np.mean(curr_amp_envelope_slopes)
#     feat[1,i] = np.std(curr_spec_centroid)
# print(np.std(feat[0, :]), np.std(feat[1, :]))
# sys.exit()

# feat_norm = zscore(feats, axis=1).transpose()
# scaler = StandardScaler()
# feat_norm = scaler.fit_transform(feats.transpose())
# pca = PCA(n_components=13)
# pca.fit(feats)
# pca_var = pca.explained_variance_
# print(pca_var[0]/np.sum(pca_var))
# ss = []
# cluster_num = range(2, 7)
# for i in cluster_num:
#     gmm = GaussianMixture(n_components=i, random_state=0).fit(feat_norm)
#     x_label = GaussianMixture(n_components=i, random_state=0).fit_predict(feat_norm)
#     curr_ss = gmm.bic(feat_norm)
#     # curr_ss = silhouette_score(feat_norm, x_label, random_state=0)
#     ss.append(curr_ss)

# print(cluster_num[np.argmax(ss)]-1)