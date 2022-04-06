import numpy as np
from utils import tune_rmse_parser
from utils import _main

from vib_music import AudioFeatureBundle
from vib_music import VibrationStream

@VibrationStream.vibration_mode(over_ride=False)
def audio_power(fb:AudioFeatureBundle) -> np.ndarray:
    rmse = fb.feature_data('rmse')

    rmse = (rmse-rmse.min()) / (rmse.max()-rmse.min())
    rmse  = rmse ** 2

    bins = np.linspace(0., 1., 150, endpoint=True)
    level = np.digitize(rmse, bins).astype(np.uint8)

    varr = 0
    for i in np.arange(0.1,0.9,0.01):
        if varr < np.var(np.power(rmse,i)):
            varr = np.var(np.power(rmse,i))
            ind = i

    rmse = np.power(rmse,ind)
    rmse = (rmse-rmse.min()) / (rmse.max()-rmse.min())
    bins = np.linspace(0., 1., 150, endpoint=True)
    level = np.digitize(rmse, bins).astype(np.uint8)
    level = level + 30

    level_zeros = np.zeros_like(level)
    level_seq = np.stack([level]*4+[level_zeros]*4, axis=-1)
    level_seq = np.concatenate([level_seq]*3, axis=-1)
    for i in range(0,level_seq.shape[0]):
        if (i < level_seq.shape[0] - 1):
            if (level[i] + 30 < level[i+1]):
                level_seq[i,0:8] = level_seq[i,0:8]*0.5
                level_seq[i,8:16] = level_seq[i,8:16]*0.7
            if (level[i] - 30 > level[i+1]):
                level_seq[i,8:16] = level_seq[i,8:16]*0.7
                level_seq[i,16:24] = level_seq[i,16:24]*0.5

    return level_seq.ravel()

def main():
    p = tune_rmse_parser()
    opt = p.parse_args()

    # replace 'rmse_mode' with 'audio_power' mode defined above
    opt = p.parse_args(args=['--vib-mode', 'audio_power'], namespace=opt)
    print(opt)

    feat_recipes = None
    if opt.task == 'run' or 'build':
        feat_recipes = {}
        feat_recipes['rmse'] = {'len_window': opt.len_window}

    _main(opt, feat_recipes)

main()