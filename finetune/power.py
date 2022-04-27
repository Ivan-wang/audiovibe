import numpy as np
from runutils import tune_rmse_parser
from runutils import tune_melspec_parser
from runutils import _main
import sys
from vib_music import FeatureManager
from vib_music.misc import init_vibration_extraction_config

@FeatureManager.vibration_mode(over_ride=False)
def audio_power(fm:FeatureManager, scale=150) -> np.ndarray:
    rmse = fm.feature_data('rmse')
    spec = fm.feature_data('melspec')

   # rmse = (rmse-rmse.min()) / (rmse.max()-rmse.min())
   # rmse  = rmse ** 2

   # bins = np.linspace(0., 1., scale, endpoint=True)
   # level = np.digitize(rmse, bins).astype(np.uint8)

    # mimic a square wave for each frame [x, x, x, x, 0, 0, 0, 0]
    # [x,x,x,x,0,0,0,0,x,x,x,x,0,0,0,0,x,x,x,x,0,0,0,0] - 300Hz

    # when using 2D sequence, do not use plot function
    # level_zeros = np.zeros_like(level)
    # level_seq = np.stack([level]*4+[level_zeros]*4, axis=-1)
    # level_seq = np.concatenate([level_seq]*3, axis=-1)

    # the following lines scan for the best power index
    varr = 0
    for i in np.arange(0.1,0.9,0.01):
        if varr < np.var(np.power(rmse,i)):
            varr = np.var(np.power(rmse,i))
            ind = i
    # the following line is power funtion
    rmse = np.power(rmse,ind)
    rmse = (rmse-rmse.min()) / (rmse.max()-rmse.min())
    bins = np.linspace(0., 1., 150, endpoint=True)
    level = np.digitize(rmse, bins).astype(np.uint8) 
    bias = 0
    level = level + bias

    # [x,x,x,x,0,0,0,0,x,x,x,x,0,0,0,0,x,x,x,x,0,0,0,0] - 300Hz

    # when using 2D sequence, do not use plot function
    level_zeros = np.zeros_like(level)
    level_seq = np.stack([level]*4+[level_zeros]*4, axis=-1)
    level_seq = np.concatenate([level_seq]*3, axis=-1)
     # the following lines tune the trend
    for i in range(0,level_seq.shape[0]):
        if (i < level_seq.shape[0] - 1):
            if (level[i] + bias < level[i+1]):
                level_seq[i,0:8] = level_seq[i,0:8]*1.1
                level_seq[i,8:16] = level_seq[i,8:16]*1.5
            if (level[i] - bias > level[i+1]):
                level_seq[i,8:16] = level_seq[i,8:16]*0.7
                level_seq[i,16:24] = level_seq[i,16:24]*0.5
            if (level[i] - bias < 0.01 ):
                level_seq[i,0:24] = 0
    return level_seq

def main():
    p = tune_rmse_parser(base_parser=tune_melspec_parser())
    opt = p.parse_args()
    print(opt)

    librosa_config = None
    plot_config = None
    if opt.task == 'run' or 'build':
        print('Buidling Feature Database...', end='')
        librosa_config = init_vibration_extraction_config()
        librosa_config['audio'] = opt.audio
        librosa_config['len_hop'] = 512
        librosa_config['stgs']['rmse'] = {
            'len_window': opt.len_window,
        }
        librosa_config['stgs']['melspec'] = {
            'len_window': opt.len_window,
            'n_mels': opt.n_mels,
            'fmax': opt.fmax if opt.fmax > 0 else None
        }

    if opt.plot:
        plot_config = {
            'plots': ['waveform', 'wavermse']
        }
    vib_kwargs_dict = {"scale":50}
    _main(opt, 'audio_power', 'adc', librosa_config, plot_config, vib_kwargs_dict)

# debug part
sys.argv = ["power.py", "--audio", "../audio/kick_22k.wav", "--task", "run"]
print("DEBUGDEBUGDEBUGDEBUG...")
###
main()
