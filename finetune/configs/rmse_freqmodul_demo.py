# 4/22/22
# Fei Tao
# taofei@feathervibe.com

# global setting
vib_lead_aud = 0    # time shift, how many frames vibration will lead audio (vibration occurs early), range in [-10, 10]
# vibration
vib__duty = 0.5    # vibration signal duty ratio, if larger than 1, it represents the number of "1"
vib__vib_extremefreq = [30,400]    # extreme value of the vibration frequency (highest and lowest frequency)
vib__vib_bias = 80    # zero-feeling offset
vib__vib_maxbin = 255    # number of bins for digitizing vibration magnitude
vib__carrier_freq = 100    # the carrier freqeuncy
vib__vib_frame_len = 24    # vibration signal sample number for each output frame
vib__global_scale = 1.0    # the global scale for vibration tense
# dsp
len_window = 1024    # acoustic feature window length
len_hop = 256    # acoustic feature hop length