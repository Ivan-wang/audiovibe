# 3/2/22
# Fei Tao
# taofei@feathervibe.com
# mapping approaches pool to map acoustic feature to vibration

from vib_music import FeatureManager
import numpy as np
from featprocs.band_split import vanilla_split
from utils.wave_generator import periodic_rectangle_generator


@FeatureManager.vibration_mode(over_ride=False)
def bandSplit(fm:FeatureManager, duty=0.5, recep_field=3, vib_freq=[50,500], vib_scale=[1,1.5]) -> np.ndarray:
    """
    split melspectrogram into bands, use specific vibration for each band, conbimed together in output
    :param fm:
    :return:
    """
    assert len(vib_freq)==len(vib_scale), "lengths of vib_scale and vib_freq must match!"
    assert recep_field%2==1, "recep_field must be odd integer"
    recep_field = int(recep_field)
    feats = fm.feature_data('melspec')
    sr = fm.meta["sr"]
    frame_len = fm.feature_data('len_window')
    n_mels = fm.feature_data('n_mels')
    feat_dim, feat_time = feats.shape

    # split features
    seg_num = len(vib_freq)
    split_bins = []
    split_step = int(round(n_mels[-1] / seg_num))    # uniformly split in Hz
    for s in range(1, seg_num):
        split_ind = (np.abs(n_mels-split_step*s)).argmin()    # find conrresponding split index in mel scale
        split_bins.append(split_ind)
    split_feats = vanilla_split(feats, split_bin_nums=split_bins)

    # generate vibration
    final_vibration = 0
    for sf_ind in range(len(split_feats)):
        curr_feats = split_feats[sf_ind]
        # compute current band power
        curr_band_power = np.sum(curr_feats,axis=0)
        # construct receptive field (zero padding beginning and end)
        context_power = np.zeros((recep_field, len(curr_band_power)+recep_field-1))    # put redundant field
        for ci in range(recep_field):
            start_ind = recep_field/2-ci+1
            context_power[ci, start_ind:start_ind+len(curr_band_power)] = curr_band_power
        context_power = context_power[:, recep_field/2:-(recep_field/2+1)]    # trim redundant field
        max_power = max(context_power)
        min_power = min(context_power)
        # combine receptive field
        comb_power = np.mean(context_power, axis=0)
        comb_power = (comb_power - max_power) / (max_power - min_power)    # noramlize
        comb_power = comb_power * vib_scale[sf_ind]    # band scale
        # digitize current band
        bins = np.linspace(0., 1., 255, endpoint=True)
        digit_power = np.expand_dims(np.digitize(comb_power, bins).astype(np.uint8), axis=1)
        digit_power_matrix = np.tile(digit_power, (1, frame_len))    # tile to form a matrix (frame_num, frame_len)
        # vibration signal
        vib_signal = periodic_rectangle_generator([1,0.], duty=duty, freq=vib_freq[sf_ind], frame_num=feat_time,
                                                  frame_time=frame_len/float(sr), frame_len=frame_len)
        scaled_vib_signal = vib_signal * digit_power_matrix    # pointwise scale vibration given power
        if sf_ind == 0:
            final_vibration = scaled_vib_signal
        else:
            final_vibration += scaled_vib_signal    # accumulate vibration signals in bands

    assert final_vibration!=0, "final_vibration is not assigned!"
    return final_vibration