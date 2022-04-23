# 4/22/22
# Fei Tao
# taofei@feathervibe.com

# vibration
vib__duty = 0.5    # vibration signal duty ratio, if larger than 1, it represents the number of "1"
vib__peak_globalth = 50    # global threshold for peak detection in dB (difference from the max value at current time)
vib__peak_relativeth = 4    # local threshold for peak detection in dB (difference over the moving average at current time)
vib__peak_movlen = 5    # moving average length (in number of bins) along frequency axis
vib__extremefreq = [50,500]    # extreme value of the vibration frequency (highest and lowest frequency)
vib__vib_bias = 80    # zero-feeling offset
vib__vib_maxbin = 255    # number of bins for digitizing vibration magnitude
vib__peak_libmit = 5    # the limit of peaks selected for vibration generation (at most this many components will be included in final vibration at current time)
vib__vib_frame_len = 24    # vibration signal sample number for each output frame
# dsp
len_window = 512    # acoustic feature window length
len_hop = 256    # acoustic feature hop length