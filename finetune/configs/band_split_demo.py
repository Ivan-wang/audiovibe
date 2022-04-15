# 3/7/22
# Fei Tao
# taofei@feathervibe.com

# vibration
vib__duty = 0.5    # vibration signal duty ratio, if larger than 1, it represents the number of "1"
vib__recep_field = 1    # receptive filed in computing spectrogram energy
vib__split_aud = None    # mel-frequency point for splitting band
# vib__vib_freq = [20,70,120,170,220,270,320,370,420,470]    # output vibration signal's frequency
# vib__vib_scale = [1,1,1,1,1,1,1,1,1,1]    # output vibration signal's scale
# vib__vib_freq = [20,100,240,340,470]    # output vibration signal's frequency
# vib__vib_scale = [1,1,1,1,1]    # output vibration signal's scale
vib__vib_freq = [100,240,470]    # output vibration signal's frequency
vib__vib_scale = [1,1,1]    # output vibration signal's scale
vib__vib_frame_len = 24    # vibration signal sample number for each output frame
vib__global_scale = 1.0    # the global scale for vibration tense
# dsp
len_window = 512    # acoustic feature window length
len_hop = 256    # acoustic feature hop length