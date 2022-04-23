# 3/2/22
# Fei Tao
# taofei@feathervibe.com
# mapping approaches pool to map acoustic feature to vibration

from vib_music import FeatureManager
import numpy as np
from sigprocs.signal_separation import band_separate, hrps
from utils.wave_generator import periodic_rectangle_generator
import matplotlib.pyplot as plt
import librosa
import librosa.display
import sys, copy
from scipy.ndimage import convolve1d
from scipy.signal import argrelextrema
from math import log

bin_levels = 255

@FeatureManager.vibration_mode(over_ride=False)
def band_split(fm:FeatureManager, duty=0.5, recep_field=3, split_aud=None, vib_freq=[50,500], vib_scale=[1,1.5],
               vib_bias=50, vib_frame_len=24, **kwargs) -> np.ndarray:
    """
    split melspectrogram into bands, use specific vibration for each band, conbimed together in output
    :param fm: (FeatureManager) FM object
    :param duty: (float) duty ratio
    :param recep_field: (int) receptive field length of melspectrogram used in generating vibration
    :param split_aud: (list) list of split audio frequency, used to split bands. If None, use uniformly split
    :param vib_freq: (list) vibration frequency for corresponding band
    :param vib_scale: (list) scale number for corresponding band
    :param vib_bias: vibration offset for body feeling
    :param vib_frame_len: (int) sample number of vibration in each frame
    :param kwargs: other kwargs
    :return: 2d vibration sequence (frame_num, vib_frame_len)
    """
    assert len(vib_freq)==len(vib_scale), "lengths of vib_scale and vib_freq must match!"
    if split_aud:
        assert isinstance(split_aud, list), "split_aud should be a list"
        assert len(split_aud)+1==len(vib_scale), "length of split_aud should 1 more than length of vib_scale!"
    assert recep_field%2==1, "recep_field must be odd integer"
    recep_field = int(recep_field)
    feats = fm.feature_data('melspec')
    sr = fm.meta["sr"]
    len_hop = fm.meta["len_hop"]
    mel_freq = fm.feature_data('melspec', prop='mel_freq')
    feat_dim, feat_time = feats.shape
    global_scale = kwargs["global_scale"]
    assert global_scale>0 and global_scale<=1.0, "global scale must be in (0,1]"

    # ### debug ###
    # plt.figure()
    # S_dB = librosa.power_to_db(feats, ref=np.max)
    # S_dB = np.flip(S_dB, axis=0)
    # plt.imshow(S_dB, cmap='hot', interpolation='nearest', aspect='auto')
    # plt.colorbar()
    # plt.savefig("spec_kick_db.png")
    # f_min = np.min(feats, axis=1)
    # f_max = np.max(feats, axis=1)
    # min_mat = np.expand_dims(f_min, axis=1)
    # min_mat = np.tile(min_mat, (1, feats.shape[1]))    # tile to form a matrix (frame_num, frame_len)
    # max_mat = np.expand_dims(f_max, axis=1)
    # max_mat = np.tile(max_mat, (1, feats.shape[1]))    # tile to form a matrix (frame_num, frame_len)
    # feat_norm = (feats - min_mat) / (max_mat - min_mat)
    # plt.figure()
    # plt.imshow(np.flip(feat_norm, axis=0), cmap='hot', interpolation='nearest', aspect='auto')
    # plt.colorbar()
    # plt.savefig("spec_kick.png")
    # feat_fakedb = 10*np.log10((feats - min_mat) / (max_mat - min_mat))
    # plt.figure()
    # plt.imshow(np.flip(feat_fakedb, axis=0), cmap='hot', interpolation='nearest', aspect='auto')
    # plt.colorbar()
    # plt.savefig("spec_kick_fakedb.png")
    # sys.exit()
    # # fig, ax = plt.subplots()
    # # S_dB = librosa.power_to_db(feats, ref=np.max)
    # # img = librosa.display.specshow(S_dB, x_axis='time',y_axis='mel', sr=sr, fmax=sr//2, ax=ax)
    # # fig.colorbar(img, ax=ax, format='%+2.0f dB')
    # # ax.set(title='Mel-frequency spectrogram')
    # ######

    # split features
    split_bins = []
    split_hz = []
    if not split_aud:
        seg_num = len(vib_freq)
        split_step = int(round(mel_freq[-1] / seg_num))    # uniformly split in Hz
        for s in range(1, seg_num):
            split_ind = (np.abs(mel_freq-split_step*s)).argmin()    # find conrresponding split index in mel scale
            split_bins.append(split_ind)
            split_hz.append(mel_freq[split_ind])
    else:
        for s in split_aud:
            split_ind = (np.abs(mel_freq-s)).argmin()    # find conrresponding split index in mel scale
            split_bins.append(split_ind)
            split_hz.append(mel_freq[split_ind])
    print(f"split on bin {split_bins}; Herz {split_hz}")
    split_feats = band_separate(feats, split_bin_nums=split_bins)
    
    # import matplotlib.pyplot as plt
    # ### debug ###
    # disp_split_feats = np.zeros((len(split_feats), split_feats[0].shape[1]))
    # for sf_ind in range(len(split_feats)):
    #     curr_feats = split_feats[sf_ind]
    #     # compute current band power
    #     curr_band_power = np.sum(curr_feats,axis=0)
    #     # moving average
    #     average_weight = np.ones((recep_field))/recep_field
    #     comb_power = np.convolve(curr_band_power, average_weight, mode="same")
    #     # normalize current band
    #     max_power = np.max(comb_power)
    #     min_power = np.min(comb_power)
    #     # comb_power = comb_power ** 0.5    # subband square root
    #     comb_power = (comb_power - min_power) / (max_power - min_power)    # noramlize
    #     disp_split_feats[sf_ind, :] = comb_power
    # disp_split_feats = np.flip(disp_split_feats, axis=0)
    # plt.figure()
    # plt.imshow(disp_split_feats, cmap='hot', interpolation='nearest', aspect='auto')
    # plt.savefig("split_feats_10bands_kick.png")
    # sys.exit()
    # ######

    # generate vibration
    final_vibration = 0
    for sf_ind in range(len(split_feats)):
        curr_feats = split_feats[sf_ind]
        # compute current band power
        curr_band_power = np.sum(curr_feats,axis=0)
        # moving average
        average_weight = np.ones((recep_field))/recep_field
        comb_power = np.convolve(curr_band_power, average_weight, mode="same")
        # normalize current band
        max_power = np.max(comb_power)
        min_power = np.min(comb_power)
        # comb_power = comb_power ** 0.5    # subband square root
        comb_power = (comb_power - min_power) / (max_power - min_power)    # noramlize
        comb_power = comb_power * vib_scale[sf_ind]    # band scale
        digit_power = np.expand_dims(comb_power, axis=1)
        digit_power_matrix = np.tile(digit_power, (1, vib_frame_len))    # tile to form a matrix (frame_num, frame_len)
        # vibration signal
        vib_signal = periodic_rectangle_generator([1,0.], duty=duty, freq=vib_freq[sf_ind], frame_num=feat_time,
                                                  frame_time=len_hop/float(sr), frame_len=vib_frame_len)
        scaled_vib_signal = vib_signal * digit_power_matrix    # pointwise scale vibration given power
        if sf_ind == 0:
            final_vibration = scaled_vib_signal
            accumulate_scale = vib_scale[sf_ind]
        else:
            final_vibration += scaled_vib_signal    # accumulate vibration signals in bands
            accumulate_scale += vib_scale[sf_ind]

    assert not isinstance(final_vibration,int), "final_vibration is not assigned!"
    
    # final normalization
    final_vibration = final_vibration / accumulate_scale
    # final_vibration = final_vibration ** 0.5    # final signal square root
    final_max = np.max(final_vibration)
    final_min = np.min(final_vibration)
    final_vibration_norm = (final_vibration - final_min) / (final_max - final_min)
    bins = np.linspace(0., 1., 150, endpoint=True)    # TODO we should use a smarter way to set bin number
    final_vibration_bins = np.digitize(final_vibration_norm, bins)
    final_vibration_bins = final_vibration_bins.astype(np.uint8)
    # add offset
    final_vibration_bins += vib_bias
    final_vibration_bins[final_vibration_bins<=vib_bias+1] = 0

    # ### debug ###
    # debug_vibration = copy.deepcopy(final_vibration_bins)
    # debug_vibration.resize(final_vibration_bins.shape[0]*final_vibration_norm.shape[1])
    # # debug_vibration = debug_vibration.astype(int)
    # plt.figure()
    # plt.plot(debug_vibration)
    # plt.savefig("vib_signal.png")
    # # plt.show()
    # # debug_vibration_nozeros = debug_vibration[debug_vibration!=0]
    # # plt.hist(debug_vibration_nozeros, bins="auto")
    # # plt.savefig("histogram.png")
    # sys.exit()
    # ######
        
    return final_vibration_bins


@FeatureManager.vibration_mode(over_ride=False)
def hrps_split(fm:FeatureManager, len_harmonic_filt=0.1, len_percusive_filt=10, beta=2.0, duty=0.5,
               pitch_recep_field=3, vib_frame_len=24, vib_freq= {"per":10.0, "har":lambda x:0.25*x+10.0},
               **kwargs) -> np.ndarray:
    """
    split melspectrogram into bands, use specific vibration for each band, conbimed together in output
    :param fm:
    :return:
    """
    assert pitch_recep_field%2 == 1, "pitch_recep_field must be odd number!"
    specs = fm.feature_data('stft')
    pitch = fm.feature_data('pitchpyin')
    specs_dim,specs_time = specs.shape
    assert specs_time == len(pitch), "length of pitch and specs must match!"
    sr = fm.meta["sr"]
    len_hop = fm.meta["len_hop"]
    stft_frame_len = fm.feature_data('stft',prop='len_window')
    global_scale = kwargs["global_scale"]
    assert global_scale>0 and global_scale<=1.0, "global scale must be in (0,1]"

    # HRPS
    power_spec = np.abs(specs)**2.0
    power_spec_h, power_spec_p, power_spec_r, M_h, M_p, M_r = hrps(power_spec, sr, len_harmonic_filt=len_harmonic_filt,
                                                                   len_percusive_filt=len_percusive_filt, beta=beta,
                                                                   len_window=stft_frame_len, len_hop=len_hop)
    bins = np.linspace(0., 1., 255, endpoint=True)

    # process power for percussion
    total_power_p = np.sum(power_spec_p, axis=0)
    global_power_p = np.sum(total_power_p)
    max_power_p = np.max(total_power_p)
    min_power_p = np.min(total_power_p)
    total_power_p = (total_power_p - min_power_p) / (max_power_p - min_power_p)    # noramlize
    digit_power_p = np.expand_dims(np.digitize(total_power_p, bins).astype(np.uint8), axis=1) - 1
    digit_power_matrix_p = np.tile(digit_power_p, (1, vib_frame_len))    # tile to form a matrix (frame_num, frame_len)

    # generate wave for percussion
    vib_signal_p = periodic_rectangle_generator([1,0.], duty=duty, freq=vib_freq["per"], frame_num=specs_time,
                                              frame_time=len_hop/float(sr), frame_len=vib_frame_len)
    scaled_vib_signal_p = vib_signal_p * digit_power_matrix_p

    # process power for pitch
    total_power_h = np.sum(power_spec_h, axis=0)    # we use power of harmonic part for now TODO improve it !!!
    global_power_h = np.sum(total_power_h)
    max_power_h = np.max(total_power_h)
    min_power_h = np.min(total_power_h)
    total_power_h = (total_power_h - min_power_h) / (max_power_h - min_power_h)    # noramlize
    digit_power_h = np.expand_dims(np.digitize(total_power_h, bins).astype(np.uint8), axis=1) - 1
    digit_power_matrix_h = np.tile(digit_power_h, (1, vib_frame_len))    # tile to form a matrix (frame_num, frame_len)

    # generate wave based on pitch
    pitch = np.nan_to_num(pitch)    # fill nan
    ori_pitch_len = len(pitch)
    vib_signal_h = np.zeros_like(scaled_vib_signal_p)    # harmonic part vibration signal buffer
    pitch = np.pad(pitch, (pitch_recep_field//2, pitch_recep_field//2), constant_values=(0,0))    # pad original pitch
    lambda_proto = lambda:0
    for pi in range(pitch_recep_field//2, ori_pitch_len):
        if isinstance(vib_freq["har"],(int, float)):
            curr_vib_freq = int(vib_freq["har"])
        elif isinstance(vib_freq["har"],type(lambda_proto)) and vib_freq["har"].__name__==lambda_proto.__name__:
            curr_vib_freq = vib_freq["har"](np.mean(pitch[pi-(pitch_recep_field//2):pi+pitch_recep_field//2+1]))
        else:
            raise ValueError('vib_freq["har"] is neither number nor function!')
        # generate 1 frame for current receptive field
        vib_signal_p = periodic_rectangle_generator([1, 0.], duty=duty, freq=curr_vib_freq, frame_num=1,
                                                    frame_time=len_hop / float(sr), frame_len=vib_frame_len)
        vib_signal_h[pi-(pitch_recep_field//2),:] = vib_signal_p[0,:]
    scaled_vib_signal_h = vib_signal_h * digit_power_matrix_h

    # fianl combination
    # part_scale = (global_power_p/global_power_h)    # scale factor for percussive part
    part_scale = 1
    final_vibration = scaled_vib_signal_h + scaled_vib_signal_p * part_scale
    
    # final normalization
    final_max = np.max(final_vibration)
    final_min = np.min(final_vibration)
    final_vibration_norm = (final_vibration - final_min) / (final_max - final_min)
    final_vibration_norm = np.round(bin_levels*final_vibration_norm*global_scale)
    final_vibration_norm = final_vibration_norm.astype(np.uint8)

    # ### debug plot ###
    # print("plot...")
    # D = librosa.amplitude_to_db(np.abs(specs), ref=np.max)
    # fig, ax = plt.subplots()
    # img = librosa.display.specshow(D, x_axis='time', y_axis='log', ax=ax)
    # ax.set(title='pYIN fundamental frequency estimation')
    # fig.colorbar(img, ax=ax, format="%+2.f dB")
    # times = librosa.times_like(pitch[pitch_recep_field//2:-(pitch_recep_field//2)])
    # ax.plot(times, total_power_h*2000, label='f0', color='cyan', linewidth=1)
    # ax.legend(loc='upper right')
    # plt.show()
    # ######

    return final_vibration_norm


@FeatureManager.vibration_mode(over_ride=False)
def band_select(fm:FeatureManager, duty=0.5, peak_globalth = 50, peak_relativeth = 4, peak_movlen = 5, vib_extremefreq = [50,500],
               vib_bias=80, vib_maxbin=255, peak_limit=5, vib_frame_len=24, **kwargs) -> np.ndarray:
    """
    select frequency band at each time point for mapping to vibration, where vibration frequency is determined by 
    scaling the corresponding audio frequency
    :return: 2d vibration sequence (frame_num, vib_frame_len)
    """
    melspec = fm.feature_data('melspec')
    sr = fm.meta["sr"]
    len_hop = fm.meta["len_hop"]
    mel_freq = fm.feature_data('melspec', prop='mel_freq')
    feat_dim, feat_time = melspec.shape
    global_scale = kwargs["global_scale"]
    assert peak_movlen%2==1, "moving average length should be odd"
    assert global_scale>0 and global_scale<=1.0, "global scale must be in (0,1]"
    melspec_mask = np.ones_like(melspec)    # mask of melspec
    melspec_db = librosa.power_to_db(melspec)    # convert to db scale

    # get relationship between vib-freq and audio-freq
    # we assume they have linear relationship: aud_freq = a * vib_freq + b
    # TODO we need more sophisticated way to model the relationship
    a = float((min(mel_freq)-max(mel_freq))) / (min(vib_extremefreq)-max(vib_extremefreq))
    b = max(mel_freq) - a * max(vib_extremefreq)

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

    # ### debug ###
    # melspec_masked_display = melspec * melspec_mask
    # plt.figure()
    # plt.imshow(np.flip(melspec_masked_display, axis=0), cmap='hot', interpolation='nearest', aspect='auto')
    # plt.colorbar()
    # plt.savefig("plots/melspec_masked.png")
    # melspec_db_masked = librosa.power_to_db(melspec_masked_display)
    # plt.figure()
    # plt.imshow(np.flip(melspec_db_masked, axis=0), cmap='hot', interpolation='nearest', aspect='auto')
    # plt.colorbar()
    # plt.savefig("plots/melspec_db_masked.png")
    # ######

    # only get top peaks
    temp_melspec_masked = melspec * melspec_mask
    temp_melspec_masked = librosa.power_to_db(temp_melspec_masked)
    peak_inds = np.argpartition(temp_melspec_masked, -peak_limit, axis=0)[-peak_limit:, :]    # top peaks inds at each time point
    peak_mask = np.zeros_like(melspec_mask)
    np.put_along_axis(peak_mask, peak_inds, 1, axis=0)    # set 1 to peak mask where top peaks are seleted
    melspec_mask = melspec_mask * peak_mask    # mask other peaks in the mask previously selected

    # mask original mel-spec
    melspec_masked = melspec * melspec_mask

    # ### debug ###
    # melspec_peak_num = np.sum(melspec_mask, axis=0)
    # plt.figure()
    # plt.imshow(np.flip(peak_mask, axis=0), cmap='hot', interpolation='nearest', aspect='auto')
    # plt.savefig("plots/melspec_peak_mask.png")
    # plt.figure()
    # plt.plot(np.linspace(1, len(melspec_peak_num), len(melspec_peak_num)), melspec_peak_num, ".")
    # plt.savefig("plots/melspec_peak_num.png")
    # plt.figure()
    # plt.imshow(np.flip(melspec_mask, axis=0), cmap='hot', interpolation='nearest', aspect='auto')
    # plt.savefig("plots/melspec_final_mask.png")
    # melspec_masked_display = melspec * melspec_mask
    # melspec_masked_display = librosa.power_to_db(melspec_masked_display)
    # plt.imshow(np.flip(melspec_masked_display, axis=0), cmap='hot', interpolation='nearest', aspect='auto')
    # plt.savefig("plots/melspec_final_mask_db.png")
    # sys.exit()
    # ######
    
    # generate vibration
    final_vibration = 0
    for f in range(feat_dim):    # per mel bin
        # get vib freq: vib_freq = (aud_freq - b) / a
        curr_aud_freq = mel_freq[f]
        curr_vib_freq = round((curr_aud_freq-b)/a)    # we round it for wave generation
        curr_vib_wav = periodic_rectangle_generator([1,0.], duty=duty, freq=curr_vib_freq, frame_num=feat_time,
                                                  frame_time=len_hop/float(sr), frame_len=vib_frame_len)
        
        # get vib magnitude
        curr_melspec = melspec_masked[f, :]
        curr_vib_mag = np.expand_dims(curr_melspec, axis=1)
        curr_vib_mag = np.tile(curr_vib_mag, (1, vib_frame_len))    # tile to form a matrix (frame_num, frame_len)

        # generate curr vib
        curr_vib = curr_vib_wav * curr_vib_mag
        # ### debug ###
        # total_len = curr_vib.shape[0]*curr_vib.shape[1]
        # plt.figure()
        # plt.plot(np.linspace(0, total_len-1, total_len), np.resize(curr_vib, (total_len,)))
        # plt.savefig("plots/vib_"+str(curr_aud_freq)+".png")
        # plt.close()
        # ######
        # accumulate
        if f == 0:
            final_vibration = curr_vib
        else:
            final_vibration += curr_vib

    assert not isinstance(final_vibration,int), "final_vibration is not assigned!"
    
    # post-process
    final_vibration = final_vibration / feat_dim    # average accumulated signal
    final_max = np.max(final_vibration)
    final_min = np.min(final_vibration)
    bin_num = vib_maxbin-vib_bias
    bins = np.linspace(0., 1., bin_num, endpoint=True)    # linear bins for digitizing
    mu_bins = [x*(log(1+bin_num*x)/log(1+bin_num)) for x in bins]    # mu-law bins
    # final normalization
    final_vibration_norm = (final_vibration - final_min) / (final_max - final_min)
    # digitize
    final_vibration_bins = np.digitize(final_vibration_norm, mu_bins)
    final_vibration_bins = final_vibration_bins.astype(np.uint8)
    # add offset
    final_vibration_bins += vib_bias
    # set zeros (we have to do this for body feeling)
    # TODO we need more sophisticated way to set zeros
    global_min = np.min(melspec_masked)
    threshold_val = (peak_limit-1) * global_min    # we set zeroing condition: if less than {peak_limit}-1 bins have {global_min} values
    threshold_val_norm = (threshold_val - final_min) / (final_max - final_min)
    threshold_val_bin = np.digitize(threshold_val_norm, mu_bins)
    final_vibration_bins[final_vibration_bins<=vib_bias+threshold_val_bin] = 0    # we set 

    # ### debug ###
    # debug_vibration = copy.deepcopy(final_vibration_bins)
    # debug_vibration.resize(final_vibration_bins.shape[0]*final_vibration_norm.shape[1])
    # # debug_vibration = debug_vibration.astype(int)
    # plt.figure()
    # plt.plot(debug_vibration)
    # plt.savefig("plots/band_select_vib_signal.png")
    # # plt.show()
    # # debug_vibration_nozeros = debug_vibration[debug_vibration!=0]
    # # plt.hist(debug_vibration_nozeros, bins="auto")
    # # plt.savefig("histogram.png")
    # sys.exit()
    # ######
        
    return final_vibration_bins