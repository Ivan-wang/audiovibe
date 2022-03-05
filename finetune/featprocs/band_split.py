# 3/3/22
# Fei Tao
# taofei@feathervibe.com
# split spectrum into bands

import librosa
import numpy as np


def vanilla_split(feat, split_bin_nums=[20]):
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