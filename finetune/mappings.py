# 3/2/22
# Fei Tao
# taofei@feathervibe.com
# mapping approaches pool to map acoustic feature to vibration

from vib_music import FeatureManager
import numpy as np
from utils.signal_separation import band_separate, hrps
from utils.wave_generator import periodic_rectangle_generator
from utils.signal_analysis import remove_harmonics, extract_peaks
from utils.ml_basic import extract_clustern
from utils.global_paras import PEAK_LIMIT
import matplotlib.pyplot as plt
import librosa
import librosa.display
import sys, copy, time
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
    # fig, ax = plt.subplots()
    # S_dB = librosa.power_to_db(feats, ref=np.max)
    # img = librosa.display.specshow(S_dB, x_axis='time',y_axis='mel', sr=sr, fmax=sr//2, ax=ax)
    # fig.colorbar(img, ax=ax, format='%+2.0f dB')
    # ax.set(title='Mel-frequency spectrogram')
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
def band_select(fm:FeatureManager, duty=0.5, vib_extremefreq = [50,500], vib_bias=80, vib_maxbin=255, 
                peak_limit=-1, vib_frame_len=24, **kwargs) -> np.ndarray:
    """
    select frequency band at each time point for mapping to vibration, where vibration frequency is determined by 
    scaling the corresponding audio frequency
    :return: 2d vibration sequence (frame_num, vib_frame_len)
    """
    melspec = fm.feature_data('melspec')
    stft = fm.feature_data('stft')
    linspec = np.abs(stft)**2.0    # power linear spectrogram
    sr = fm.meta["sr"]
    len_hop = fm.meta["len_hop"]
    mel_freq = fm.feature_data('melspec', prop='mel_freq')
    stft_freq = fm.feature_data('stft', prop='stft_freq')
    stft_len_window = fm.feature_data('stft', prop='len_window')
    feat_dim, feat_time = melspec.shape
    global_scale = kwargs.get("global_scale", 1.0)
    hprs_harmonic_filt_len = kwargs.get("hprs_harmonic_filt_len", 0.1)
    hprs_percusive_filt_len = kwargs.get("hprs_percusive_filt_len", 400)
    hprs_beta = kwargs.get("hprs_beta", 4.0)
    peak_globalth = kwargs.get("peak_globalth", 20)
    peak_relativeth = kwargs.get("peak_relativeth", 4)
    stft_peak_movlen = int(kwargs.get("stft_peak_movlen", 400//np.abs(stft_freq[2]-stft_freq[1])))
    mel_peak_movlen = int(kwargs.get("mel_peak_movlen", stft_peak_movlen//4))
    assert mel_peak_movlen>1 and stft_peak_movlen>1, "peak moving average filter must have length larger than 1"
    if stft_peak_movlen%2==0: stft_peak_movlen += 1
    if mel_peak_movlen%2==0: mel_peak_movlen += 1
    assert global_scale>0 and global_scale<=1.0, "global scale must be in (0,1]"


    # get relationship between vib-freq and audio-freq
    # we assume they have linear relationship: aud_freq = a * vib_freq + b
    # TODO we need more sophisticated way to model the relationship
    a = float((min(mel_freq)-max(mel_freq))) / (min(vib_extremefreq)-max(vib_extremefreq))
    b = max(mel_freq) - a * max(vib_extremefreq)


    # harmonic-percusive-residual separation
    start_t = time.time()
    power_spec_h, power_spec_p, power_spec_r, M_h, M_p, M_r = hrps(linspec, sr, len_harmonic_filt=hprs_harmonic_filt_len,
                                                                   len_percusive_filt=hprs_percusive_filt_len, beta=hprs_beta,
                                                                   len_window=stft_len_window, len_hop=len_hop)
    print("hrps elapses %f" % (time.time()-start_t))

    # ### debug plot ###
    # D = librosa.amplitude_to_db(power_spec, ref=np.max)
    # D_h = librosa.amplitude_to_db(power_spec_h, ref=np.max)
    # D_h_mask = librosa.amplitude_to_db(M_h, ref=np.max)
    # D_p = librosa.amplitude_to_db(power_spec_p, ref=np.max)
    # D_mel = librosa.amplitude_to_db(melspec, ref=np.max )
    # plt.figure()
    # librosa.display.specshow(D, x_axis='frames', y_axis='linear')
    # plt.colorbar()
    # plt.savefig("../plots/spec_original.png")
    # plt.close()
    # plt.figure()
    # librosa.display.specshow(D_h, x_axis='frames', y_axis='linear')
    # plt.colorbar()
    # plt.savefig("../plots/spec_harmonics.png")
    # plt.close()
    # plt.figure()
    # librosa.display.specshow(D_p, x_axis='frames', y_axis='linear')
    # plt.colorbar()
    # plt.savefig("../plots/spec_percussion.png")
    # plt.close()
    # plt.figure()
    # librosa.display.specshow(D_mel, x_axis='frames', y_axis='mel')
    # plt.colorbar()
    # plt.savefig("../plots/spec_mel.png")
    # plt.close()
    # ######

    # stft_mask = extract_peaks(linspec, peak_movlen=19, peak_relativeth=peak_relativeth, peak_globalth=peak_globalth)
    start_t = time.time()
    melspec_mask = extract_peaks(melspec, peak_movlen=mel_peak_movlen, peak_relativeth=peak_relativeth, peak_globalth=peak_globalth)
    print("melspec peak extraction elapses %f" % (time.time()-start_t))
    start_t = time.time()
    harm_peaks = extract_peaks(power_spec_h, peak_movlen=stft_peak_movlen, peak_relativeth=peak_relativeth, peak_globalth=peak_globalth)
    print("linspec peak extraction elapses %f" % (time.time()-start_t))
    # melspec_mask_no_harms, melspec_mask = remove_harmonics(melspec_mask, melspec, mel_freq)
    # stft_mask_no_harms, stft_mask = remove_harmonics(stft_mask, linspec, stft_freq)
    spec_mask = melspec_mask

    # ### debug ###
    # spec_db = librosa.power_to_db(spec_mask, ref=np.max)
    # harm_db = librosa.power_to_db(harm_peaks, ref=np.max)
    # np.save("../plots/masks_spec.npy", spec_db, allow_pickle=True)
    # np.save("../plots/masks_harm.npy", harm_db, allow_pickle=True)
    # # plt.figure()
    # # librosa.display.specshow(spec_db, x_axis='frames', y_axis='mel')
    # # plt.savefig("../plots/masks_spec.png")
    # # plt.close()
    # # plt.figure()
    # # librosa.display.specshow(harm_db, x_axis='frames', y_axis='linear')
    # # plt.savefig("../plots/masks_harm.png")
    # # plt.close()
    # # sys.exit()
    # ######

    # get top peaks
    spec_masked = melspec * spec_mask
    remove_t = 0    # harmonic removal timer
    if peak_limit<=0:
        # automatically determin peak limit
        # TODO more sophisticated way to determin peak limits
        peak_mask = np.zeros_like(spec_mask)
        power_spec_sum = np.sum(linspec, axis=0)
        power_spec_h_sum = np.sum(power_spec_h, axis=0)
        power_spec_p_sum = np.sum(power_spec_p, axis=0)
        power_spec_r_sum = np.sum(power_spec_r, axis=0)
        h_ratio = power_spec_h_sum / power_spec_sum
        p_ratio = power_spec_p_sum / power_spec_sum
        r_ratio = power_spec_r_sum / power_spec_sum
        for ti in range(feat_time):
            if p_ratio[ti]>=2*r_ratio[ti] and p_ratio[ti]>2*h_ratio[ti]:
                curr_peak_limit = 3
            elif r_ratio[ti]>2*h_ratio[ti]  and r_ratio[ti]>2*p_ratio[ti]:
                curr_peak_limit = 2
            elif h_ratio[ti]>2*p_ratio[ti] and h_ratio[ti]>2*r_ratio[ti]:
                curr_spec_mask = np.expand_dims(harm_peaks[:, ti], axis=1)
                curr_spec = np.expand_dims(linspec[:, ti], axis=1)
                start_t = time.time()
                spec_mask_no_harms, curr_spec_mask = remove_harmonics(curr_spec_mask, curr_spec, stft_freq)
                remove_t = max(time.time() - start_t, remove_t)
                # ### debug ###
                # plt.figure()
                # plt.plot(curr_spec_mask)
                # plt.savefig("../plots/curr_spec_mask_"+str(ti)+".png")
                # plt.close()
                # plt.figure()
                # plt.plot(spec_mask_no_harms)
                # plt.savefig("../plots/curr_spec_no_harms_"+str(ti)+".png")
                # plt.close()
                # ######
                curr_peak_limit = int(min(PEAK_LIMIT, np.sum(spec_mask_no_harms)+1))
            else:
                curr_peak_limit = PEAK_LIMIT
            peak_inds = spec_masked[:,ti].argsort()[::-1][:curr_peak_limit]
            peak_mask[peak_inds, ti] = 1
    else:
        # given pre-set peak_limit
        spec_masked = librosa.power_to_db(spec_masked)
        peak_inds = np.argpartition(spec_masked, -peak_limit, axis=0)[-peak_limit:, :]    # top peaks inds at each time point
        peak_mask = np.zeros_like(spec_mask)
        np.put_along_axis(peak_mask, peak_inds, 1, axis=0)    # set 1 to peak mask where top peaks are seleted
    # incorporate peak's mask
    spec_masked = spec_masked * peak_mask
    
    print("harmonic removal at most elapses %f" % (remove_t))

    # ### debug ###
    # plt.figure()
    # spec_db = librosa.power_to_db(spec_masked, ref=np.max)
    # librosa.display.specshow(spec_db, x_axis='frames', y_axis='mel')
    # plt.colorbar()
    # plt.savefig("../plots/spec_masked_final.png")
    # plt.close()
    # # sys.exit()
    # ######

    # variance based strategy for peak limit determination
    #     temp_linspec_masked = linspec * stft_mask_no_harms
    #     masked_std = np.var(temp_linspec_masked, axis=1)
    #     masked_std_sum = np.sum(masked_std)
    #     masks_queue = masked_std.argsort()
    #     masks_queue = masks_queue[::-1]
    #     accumulate_std = 0
    #     for m in range(PEAK_LIMIT):
    #         accumulate_std += masked_std[masks_queue[m]]
    #         std_proportion = accumulate_std / masked_std_sum
    #         print("%d proportion %f" % (m, std_proportion))
    #         if std_proportion>=0.75:
    #             peak_limit = m+1
    #             break
    #     if peak_limit<=0: peak_limit = PEAK_LIMIT
    # print(peak_limit)

    # clustering based strategy for peak limit determination
    # start_time = time.time()
    # if isinstance(peak_limit, list) or peak_limit<=0:
    #     if isinstance(peak_limit, list): class_n = peak_limit
    #     else: class_n = [1,PEAK_LIMIT]
    #     peak_limit_temp = np.zeros((feat_time), dtype=int)
    #     for ft in range(feat_time):
    #         curr_peaks = melspec_mask[:, ft]
    #         if np.sum(curr_peaks)<=1:
    #             peak_limit_temp[ft] = np.sum(curr_peaks)
    #             continue
    #         curr_class_n = [int(min(class_n)), int(min(np.sum(curr_peaks), max(class_n)))]    # up to the minimum between sum of peaks and pre-set {peak_limit}
    #         input_feat = np.expand_dims(melspec[:,ft],axis=1)
    #         peak_limit_temp[ft] = extract_clustern(input_feat, class_n=curr_class_n)
    #         # set peak limit as the largest peak limit over all time
    #         if peak_limit_temp[ft]>peak_limit: peak_limit = peak_limit_temp[ft]
    #         if peak_limit==max(class_n): break
    #     print("peak limit is %d" % (peak_limit))
    #     peak_limit += 1    # to add more variations, we add 1 more peak for auxilary
    # print("elapse %f secs" % (time.time()-start_time))

    # generate vibration
    final_vibration = 0
    for f in range(feat_dim):    # per mel bin
        # get vib freq: vib_freq = (aud_freq - b) / a
        curr_aud_freq = mel_freq[f]
        curr_vib_freq = round((curr_aud_freq-b)/a)    # we round it for wave generation
        curr_vib_wav = periodic_rectangle_generator([1,0.], duty=duty, freq=curr_vib_freq, frame_num=feat_time,
                                                  frame_time=len_hop/float(sr), frame_len=vib_frame_len)
        # get vib magnitude
        curr_melspec = spec_masked[f, :]
        curr_vib_mag = np.expand_dims(curr_melspec, axis=1)
        curr_vib_mag = np.tile(curr_vib_mag, (1, vib_frame_len))    # tile to form a matrix (frame_num, frame_len)
        # generate curr vib
        curr_vib = curr_vib_wav * curr_vib_mag
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
    global_min = np.min(spec_masked[np.nonzero(spec_masked)])    # find global minimum except 0
    threshold_val = (PEAK_LIMIT//2) * global_min    # we set zeroing condition: if less than half of {peak_limit} bins have {global_min} values
    threshold_val_norm = (threshold_val - final_min) / (final_max - final_min)
    threshold_val_bin = np.digitize(threshold_val_norm, mu_bins)
    final_vibration_bins[final_vibration_bins<=vib_bias+threshold_val_bin] = 0    # set zeros below threshold
        
    return final_vibration_bins


@FeatureManager.vibration_mode(over_ride=False)
def rmse_freqmodul(fm:FeatureManager, duty=0.5, vib_extremefreq = [50,500], vib_bias=80, vib_maxbin=255, 
                carrier_freq=100, vib_frame_len=24, **kwargs) -> np.ndarray:
    """
    use frequency modulation to map the wave rms to vibration
    :return: 2d vibration sequence (frame_num, vib_frame_len)
    """
    rmse = fm.feature_data('rmse')
    sr = fm.meta["sr"]
    len_hop = fm.meta["len_hop"]
    feat_time = len(rmse)
    global_scale = kwargs.get("global_scale", 1.0)
    assert global_scale>0 and global_scale<=1.0, "global scale must be in (0,1]"
    # rmse_anchor = (max(rmse)+min(rmse))/2.0    # compute the anchor point for rmse
    rmse_anchor = np.mean(rmse)    # compute the anchor point for rmse
    freq_deviation = np.max(np.abs(np.array(vib_extremefreq)-carrier_freq))
    rmse_max = max(rmse)
    rmse_min = min(rmse)
    
    # generate vibration
    final_vibration = np.zeros((feat_time, vib_frame_len))
    for t in range(feat_time):    # per mel bin
        # TODO decide freq-determination strategy
        # # linear freq modulation
        # curr_relative_rmse = rmse[t] - rmse_anchor
        # # get vib freq: vib_freq = carrier_freq + freq_deviation / rmse_max * curr_relative_rmse
        # curr_vib_freq = carrier_freq + freq_deviation / rmse_max * curr_relative_rmse
        # # cut vib freq to extreme freq
        # curr_vib_freq = max(curr_vib_freq, min(vib_extremefreq))
        # curr_vib_freq = min(curr_vib_freq, max(vib_extremefreq))
        # # segmental freq modulation
        if rmse[t] > rmse_anchor:
            pos_vib_factor = (max(vib_extremefreq)-carrier_freq)/(rmse_max-rmse_anchor) 
            curr_vib_freq = carrier_freq + pos_vib_factor * rmse[t]
        elif rmse[t] < rmse_anchor:
            neg_vib_factor = (min(vib_extremefreq)-carrier_freq) / log(rmse_min/rmse_anchor)
            curr_vib_freq = carrier_freq + neg_vib_factor * log(rmse[t]/rmse_anchor)
        else:
            curr_vib_freq = carrier_freq
        curr_vib_wav = periodic_rectangle_generator([1,0.], duty=duty, freq=curr_vib_freq, frame_num=1,
                                                  frame_time=len_hop/float(sr), frame_len=vib_frame_len)
        final_vibration[t, :] = curr_vib_wav[0]

    assert not np.sum(final_vibration)==0, "final_vibration is not assigned!"
    
    # post-process
    final_max = np.max(final_vibration)
    final_min = np.min(final_vibration)
    bin_num = vib_maxbin    # determine how many bins needed
    bins = np.linspace(0., 1., bin_num, endpoint=True)    # linear bins for digitizing
    # mu_bins = [x*(log(1+bin_num*x)/log(1+bin_num)) for x in bins]    # mu-law bins
    # final normalization
    final_vibration_norm = (final_vibration - final_min) / (final_max - final_min)
    # digitize
    final_vibration_bins = np.digitize(final_vibration_norm, bins)
    final_vibration_bins = final_vibration_bins.astype(np.uint8)
        
    return final_vibration_bins


@FeatureManager.vibration_mode(over_ride=False)
def band_select_fast(fm:FeatureManager, duty=0.5, vib_extremefreq = [50,500], vib_bias=80, vib_maxbin=255, 
                peak_limit=-1, vib_frame_len=24, **kwargs) -> np.ndarray:
    """
    select frequency band at each time point for mapping to vibration, where vibration frequency is determined by 
    scaling the corresponding audio frequency
    :return: 2d vibration sequence (frame_num, vib_frame_len)
    """
    start_t = time.time()
    stft = fm.feature_data('stft')
    linspec = np.abs(stft)**2.0    # power linear spectrogram
    sr = fm.meta["sr"]
    len_hop = fm.meta["len_hop"]
    stft_freq = fm.feature_data('stft', prop='stft_freq')
    
    # select bins lower than 8k hz
    num_8k_bins = np.sum(stft_freq<=8000)
    # num_8k_bins = np.sum(stft_freq<=8000000)
    linspec = linspec[:num_8k_bins,:]
    stft_freq = stft_freq[:num_8k_bins]
    stft_len_window = fm.feature_data('stft', prop='len_window')

    feat_dim, feat_time = linspec.shape
    global_scale = kwargs.get("global_scale", 0.01)
    hprs_harmonic_filt_len = kwargs.get("hprs_harmonic_filt_len", 0.1)
    hprs_percusive_filt_len = kwargs.get("hprs_percusive_filt_len", 400 * stft_len_window / 512)    # TODO this is determined by experience
    hprs_beta = kwargs.get("hprs_beta", 4.0)
    peak_globalth = kwargs.get("peak_globalth", 20)
    peak_relativeth = kwargs.get("peak_relativeth", 4)
    stft_peak_movlen = int(kwargs.get("stft_peak_movlen", 400//np.abs(stft_freq[2]-stft_freq[1])))    # TODO this is determined by experience
    # mel_peak_movlen = int(kwargs.get("mel_peak_movlen", stft_peak_movlen//4))
    # assert mel_peak_movlen>1 and stft_peak_movlen>1, "peak moving average filter must have length larger than 1"
    # if stft_peak_movlen%2==0: stft_peak_movlen += 1
    # if mel_peak_movlen%2==0: mel_peak_movlen += 1
    assert global_scale>0 and global_scale<=1.0, "global scale must be in (0,1]"


    # get relationship between vib-freq and audio-freq
    # we assume they have linear relationship: aud_freq = a * vib_freq + b
    # TODO we need more sophisticated way to model the relationship
    a = float((min(stft_freq)-max(stft_freq))) / (min(vib_extremefreq)-max(vib_extremefreq))
    b = max(stft_freq) - a * max(vib_extremefreq)


    # harmonic-percusive-residual separation
    # start_t = time.time()
    power_spec_h, power_spec_p, power_spec_r, M_h, M_p, M_r = hrps(linspec, sr, len_harmonic_filt=hprs_harmonic_filt_len,
                                                                   len_percusive_filt=hprs_percusive_filt_len, beta=hprs_beta,
                                                                   len_window=stft_len_window, len_hop=len_hop)
    # print("hrps elapses %f" % (time.time()-start_t))

    # ### debug plot ###
    # D = librosa.amplitude_to_db(linspec, ref=np.max)
    # D_h = librosa.amplitude_to_db(power_spec_h, ref=np.max)
    # D_p = librosa.amplitude_to_db(power_spec_p, ref=np.max)
    # plt.figure()
    # librosa.display.specshow(D, x_axis='frames', y_axis='linear')
    # plt.colorbar()
    # plt.savefig("../plots/spec_original_var_linspec.png")
    # plt.close()
    # plt.figure()
    # librosa.display.specshow(D_h, x_axis='frames', y_axis='linear')
    # plt.colorbar()
    # plt.savefig("../plots/spec_harmonics_var_D_h.png")
    # plt.close()
    # plt.figure()
    # librosa.display.specshow(D_p, x_axis='frames', y_axis='linear')
    # plt.colorbar()
    # plt.savefig("../plots/spec_percussion_var_D_p.png")
    # plt.close()
    # ######

    # stft_mask = extract_peaks(linspec, peak_movlen=19, peak_relativeth=peak_relativeth, peak_globalth=peak_globalth)
    # start_t = time.time()
    # melspec_mask = extract_peaks(melspec, peak_movlen=mel_peak_movlen, peak_relativeth=peak_relativeth, peak_globalth=peak_globalth)
    # print("melspec peak extraction elapses %f" % (time.time()-start_t))
    # start_t = time.time()
    harm_peaks = extract_peaks(power_spec_h, peak_movlen=stft_peak_movlen, peak_relativeth=peak_relativeth, peak_globalth=peak_globalth)
    # print("linspec peak extraction elapses %f" % (time.time()-start_t))
    # melspec_mask_no_harms, melspec_mask = remove_harmonics(melspec_mask, melspec, mel_freq)
    # stft_mask_no_harms, stft_mask = remove_harmonics(stft_mask, linspec, stft_freq)
    spec_mask = harm_peaks

    # ### debug ###
    # spec_db = librosa.power_to_db(spec_mask, ref=np.max)
    # harm_db = librosa.power_to_db(harm_peaks, ref=np.max)
    # # np.save("../plots/masks_spec_var_spec_mask.npy", spec_db, allow_pickle=True)
    # # np.save("../plots/masks_harm_var_harm_peaks.npy", harm_db, allow_pickle=True)
    # plt.figure()
    # librosa.display.specshow(spec_db, x_axis='frames', y_axis='mel')
    # plt.savefig("../plots/masks_spec_var_spec_mask.png")
    # plt.close()
    # plt.figure()
    # librosa.display.specshow(harm_db, x_axis='frames', y_axis='linear')
    # plt.savefig("../plots/masks_harm_var_harm_peaks.png")
    # plt.close()
    # # sys.exit()
    # ######

    # get top peaks
    spec_masked = linspec * harm_peaks
    # remove_t = 0    # harmonic removal timer
    if peak_limit<=0:
        # automatically determin peak limit
        # np.save("spec.npy", linspec)
        # np.save("harm_peaks.npy", harm_peaks)
        # np.save("spec_masked.npy", spec_masked)
        # np.save("spec_h.npy", power_spec_h)
        # np.save("spec_p.npy", power_spec_p)
        # np.save("spec_r.npy", power_spec_r)
        # np.save("stft_freq.npy", stft_freq)

        # TODO more sophisticated way to determin peak limits
        peak_mask = np.zeros_like(spec_mask)
        power_spec_sum = np.sum(linspec, axis=0)
        power_spec_h_sum = np.sum(power_spec_h, axis=0)
        power_spec_p_sum = np.sum(power_spec_p, axis=0)
        power_spec_r_sum = np.sum(power_spec_r, axis=0)
        h_ratio = power_spec_h_sum / power_spec_sum
        p_ratio = power_spec_p_sum / power_spec_sum
        r_ratio = power_spec_r_sum / power_spec_sum
        for ti in range(feat_time):
            if p_ratio[ti]>=2*r_ratio[ti] and p_ratio[ti]>2*h_ratio[ti]:
                curr_peak_limit = 3
            elif r_ratio[ti]>2*h_ratio[ti]  and r_ratio[ti]>2*p_ratio[ti]:
                curr_peak_limit = 2
            elif h_ratio[ti]>2*p_ratio[ti] and h_ratio[ti]>2*r_ratio[ti]:
                curr_spec_mask = np.expand_dims(harm_peaks[:, ti], axis=1)
                curr_spec = np.expand_dims(linspec[:, ti], axis=1)
                # start_t = time.time()
                spec_mask_no_harms, curr_spec_mask = remove_harmonics(curr_spec_mask, curr_spec, stft_freq)
                # remove_t = max(time.time() - start_t, remove_t)
                # ### debug ###
                # plt.figure()
                # plt.plot(curr_spec_mask)
                # plt.savefig("../plots/curr_spec_mask_"+str(ti)+".png")
                # plt.close()
                # plt.figure()
                # plt.plot(spec_mask_no_harms)
                # plt.savefig("../plots/curr_spec_no_harms_"+str(ti)+".png")
                # plt.close()
                # ######
                curr_peak_limit = int(min(PEAK_LIMIT, np.sum(spec_mask_no_harms)+1))
            else:
                curr_peak_limit = PEAK_LIMIT
            peak_inds = spec_masked[:,ti].argsort()[::-1][:curr_peak_limit]
            peak_mask[peak_inds, ti] = 1
    else:
        # given pre-set peak_limit
        spec_masked = librosa.power_to_db(spec_masked)
        peak_inds = np.argpartition(spec_masked, -peak_limit, axis=0)[-peak_limit:, :]    # top peaks inds at each time point
        peak_mask = np.zeros_like(spec_mask)
        np.put_along_axis(peak_mask, peak_inds, 1, axis=0)    # set 1 to peak mask where top peaks are seleted
    # incorporate peak's mask
    spec_masked = spec_masked * peak_mask
    # sys.exit()
    # print("harmonic removal at most elapses %f" % (remove_t))

    # ### debug ###
    # plt.figure()
    # spec_db = librosa.power_to_db(spec_masked, ref=np.max)
    # librosa.display.specshow(spec_db, x_axis='frames', y_axis='mel')
    # plt.colorbar()
    # plt.savefig("../plots/spec_masked_final_var_spec_masked.png")
    # plt.close()
    # sys.exit()
    # ######

    # generate vibration
    final_vibration = 0
    for f in range(feat_dim):    # per mel bin
        # get vib freq: vib_freq = (aud_freq - b) / a
        curr_aud_freq = stft_freq[f]
        curr_vib_freq = round((curr_aud_freq-b)/a)    # we round it for wave generation
        curr_vib_wav = periodic_rectangle_generator([1,0.], duty=duty, freq=curr_vib_freq, frame_num=feat_time,
                                                  frame_time=len_hop/float(sr), frame_len=vib_frame_len)
        # get vib magnitude
        curr_melspec = spec_masked[f, :]
        curr_vib_mag = np.expand_dims(curr_melspec, axis=1)
        curr_vib_mag = np.tile(curr_vib_mag, (1, vib_frame_len))    # tile to form a matrix (frame_num, frame_len)
        # generate curr vib
        curr_vib = curr_vib_wav * curr_vib_mag
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
    global_min = np.min(spec_masked[np.nonzero(spec_masked)])    # find global minimum except 0
    threshold_val = (PEAK_LIMIT//2) * global_min    # we set zeroing condition: if less than half of {peak_limit} bins have {global_min} values
    threshold_val_norm = (threshold_val - final_min) / (final_max - final_min)
    threshold_val_bin = np.digitize(threshold_val_norm, mu_bins)
    final_vibration_bins[final_vibration_bins<=vib_bias+threshold_val_bin] = 0    # set zeros below threshold
    
    print("mapping elapses: %f" % (time.time()-start_t))
    
    return final_vibration_bins
