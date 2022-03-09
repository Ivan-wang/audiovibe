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


@FeatureManager.vibration_mode(over_ride=False)
def band_split(fm:FeatureManager, duty=0.5, recep_field=3, split_aud=None, vib_freq=[50,500], vib_scale=[1,1.5],
               vib_frame_len=24, **kwargs) -> np.ndarray:
    """
    split melspectrogram into bands, use specific vibration for each band, conbimed together in output
    :param fm: (FeatureManager) FM object
    :param duty: (float) duty ratio
    :param recep_field: (int) receptive field length of melspectrogram used in generating vibration
    :param split_aud: (list) list of split audio frequency, used to split bands. If none, use uniformly split
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
    frame_len = fm.feature_data('melspec',prop='len_window')
    mel_freq = fm.feature_data('melspec', prop='mel_freq')
    feat_dim, feat_time = feats.shape
    # ### debug ###
    # fig, ax = plt.subplots()
    # S_dB = librosa.power_to_db(feats, ref=np.max)
    # img = librosa.display.specshow(S_dB, x_axis='time',y_axis='mel', sr=sr, fmax=sr//2, ax=ax)
    # fig.colorbar(img, ax=ax, format='%+2.0f dB')
    # ax.set(title='Mel-frequency spectrogram')
    # ######

    # split features
    split_bins = []
    if not split_aud:
        seg_num = len(vib_freq)
        split_step = int(round(mel_freq[-1] / seg_num))    # uniformly split in Hz
        for s in range(1, seg_num):
            split_ind = (np.abs(mel_freq-split_step*s)).argmin()    # find conrresponding split index in mel scale
            split_bins.append(split_ind)
    else:
        for s in split_aud:
            split_ind = (np.abs(mel_freq-s)).argmin()    # find conrresponding split index in mel scale
            split_bins.append(split_ind)
    print(f"split on {split_bins}")
    split_feats = band_separate(feats, split_bin_nums=split_bins)

    # generate vibration
    final_vibration = 0
    for sf_ind in range(len(split_feats)):
        curr_feats = split_feats[sf_ind]
        # compute current band power
        curr_band_power = np.sum(curr_feats,axis=0)
        # construct receptive field (zero padding beginning and end)
        context_power = np.zeros((recep_field, len(curr_band_power)+recep_field-1))    # put redundant field
        for ci in range(recep_field):
            start_ind = int(recep_field//2-ci+1)
            context_power[ci, start_ind:start_ind+len(curr_band_power)] = curr_band_power
        context_power = context_power[:, recep_field//2:-(recep_field//2)]    # trim redundant field
        # max_power = max(context_power)
        # min_power = min(context_power)
        # combine receptive field
        max_power = np.max(curr_band_power)
        min_power = np.min(curr_band_power)
        comb_power = np.mean(context_power, axis=0)
        comb_power = (comb_power - min_power) / (max_power - min_power)    # noramlize
        comb_power = comb_power * vib_scale[sf_ind]    # band scale
        # digitize current band
        bins = np.linspace(0., 1., 255, endpoint=True)
        digit_power = np.expand_dims(np.digitize(comb_power, bins).astype(np.uint8), axis=1)
        digit_power_matrix = np.tile(digit_power, (1, vib_frame_len))    # tile to form a matrix (frame_num, frame_len)
        # vibration signal
        vib_signal = periodic_rectangle_generator([1,0.], duty=duty, freq=vib_freq[sf_ind], frame_num=feat_time,
                                                  frame_time=frame_len/float(sr), frame_len=vib_frame_len)
        scaled_vib_signal = vib_signal * digit_power_matrix    # pointwise scale vibration given power
        if sf_ind == 0:
            final_vibration = scaled_vib_signal
        else:
            final_vibration += scaled_vib_signal    # accumulate vibration signals in bands

    assert not isinstance(final_vibration,int), "final_vibration is not assigned!"
    return final_vibration


@FeatureManager.vibration_mode(over_ride=False)
def hrps_split(fm:FeatureManager, len_harmonic_filt=0.1, len_percusive_filt=10, beta=2.0, duty=0.5,
               vib_frame_len=24, **kwargs) -> np.ndarray:
    """
    split melspectrogram into bands, use specific vibration for each band, conbimed together in output
    :param fm:
    :return:
    """
    specs = fm.feature_data('stft')
    pitch = fm.feature_data('pitchpyin')
    sr = fm.meta["sr"]
    len_hop = fm.meta["len_hop"]
    len_window = fm.feature_data('stft',prop='len_window')
    power_spec = np.abs(specs)**2.0
    power_spec_h, power_spec_p, power_spec_r, M_h, M_p, M_r = hrps(power_spec, sr, len_harmonic_filt=len_harmonic_filt,
                                                                   len_percusive_filt=len_percusive_filt, beta=beta,
                                                                   len_window=len_window, len_hop=len_hop)
    ### debug plot ###
    print("plot...")
    plt.imshow(M_p, aspect="auto")
    plt.show()
    # generate vibration
    final_vibration = 0
    return final_vibration