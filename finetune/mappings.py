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

bin_levels = 255

@FeatureManager.vibration_mode(over_ride=False)
def band_split(fm:FeatureManager, duty=0.5, recep_field=3, split_aud=None, vib_freq=[50,500], vib_scale=[1,1.5],
               vib_frame_len=24, **kwargs) -> np.ndarray:
    """
    split melspectrogram into bands, use specific vibration for each band, conbimed together in output
    :param fm: (FeatureManager) FM object
    :param duty: (float) duty ratio
    :param recep_field: (int) receptive field length of melspectrogram used in generating vibration
    :param split_aud: (list) list of split audio frequency, used to split bands. If None, use uniformly split
    :param vib_freq: (list) vibration frequency for corresponding band
    :param vib_scale: (list) scale number for corresponding band
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
    vib_bias = 50
    assert global_scale>0 and global_scale<=1.0, "global scale must be in (0,1]"
    # ### debug ###
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