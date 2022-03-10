# 3/8/22
# Fei Tao
# taofei@feathervibe.com


# vibration (start with vib__)
vib__pitch_recep_field=3
vib__duty=0.5
vib__len_harmonic_filt = 0.1    # in second
vib__len_percusive_filt= 1000    # in hz
vib__beta = 20.0
vib__vib_freq= {"per":20.0, "har":lambda x:0.1*x+20.0}    # vibration frequency for specified signal
# dsp
len_window = 512
pitch_len_window = 1024
len_hop=256