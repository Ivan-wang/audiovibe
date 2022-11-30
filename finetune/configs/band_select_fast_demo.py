# 4/22/22
# Fei Tao
# taofei@feathervibe.com

# global setting
vib_lead_aud = 0    # time shift, how many frames vibration will lead audio (vibration occurs early), range in [-10, 10]
# vibration
vib__duty = 0.5    # vibration signal duty ratio, if larger than 1, it represents the number of "1"
vib__vib_extremefreq = [30,200]    # extreme value of the vibration frequency (highest and lowest frequency)
vib__vib_bias = 80    # zero-feeling offset
vib__vib_maxbin = 255    # number of bins for digitizing vibration magnitude
vib__peak_limit = -1    # the limit of peaks selected for vibration generation (at most this many components will be included in final vibration at current time)
vib__vib_frame_len = 12    # vibration signal sample number for each output frame
vib__global_scale = 1.0    # the global scale for vibration tense
vib__streaming = True    # flag to use streaming inference
vib__audio_len = 0.1    # seconds of the audio window in streaming inference
vib__stream_nwin = 1    # number of streaming inferencing windows in mapping buffer. Mapping algo will be performed over it and the center window's result will be output.
# signal analysis
peak_globalth = 20    # global threshold for peak detection in dB (difference from the max value at current time)
peak_relativeth = 4    # local threshold for peak detection in dB (difference over the moving average at current time)
mel_peak_movlen = 5    # moving average length (in number of bins) along frequency axis
stft_peak_movlen = 19    # moving average length (in number of bins) along frequency axis
hprs_harmonic_filt_len = 0.1    # HPRS harmonic direction filter length (in sec)
hprs_percusive_filt_len = 400    # HPRS percusive direction filter length (in hz)
hprs_beta = 4.0    # HPRS harmonic and percusive threshold factor
# dsp
len_window = 128    # acoustic feature window length
len_hop = 128    # acoustic feature hop length