# CHANGE: all vib_music functions now have type hints.
# CHANGE: a python IDE can show the expected type when you call a function from vib_music
import numpy as np
from utils import tune_rmse_parser
from utils import _main

# CHANGE: FeatureManager is separated to AudioFeatureBundle and FeatureBuilder
# CHNAGE: AudioFeatureBundle is data class, use it to generate vib signals
# CHANGE: FeatureBuilder manages librosa extraction functions
from vib_music import AudioFeatureBundle
# CHANGE: VibrationStream manages the vibration data and drivers.
from vib_music import VibrationStream

# CHNAGE: register vibration function with VibrationStream.vibration_mode
# CHANGE: vibration function now need an AudioFeatureBundle instance
@VibrationStream.vibration_mode(over_ride=False)
def audio_power(fb:AudioFeatureBundle) -> np.ndarray:
    # AudioFeatureBundle has a similar interface with previous FeatureManager
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
    # CHANGE: all vibration return an 1-D array, please flatten the vibration sequence
    return level_seq.ravel()

def main():
    p = tune_rmse_parser()
    opt = p.parse_args()

    # CHANGE: vibration mode is a command line argument, see utils.py
    # CHANGE: here we fixed the vibration mode as "audio_power" (default "rmse")
    opt = p.parse_args(args=['--vib-mode', 'audio_power'], namespace=opt)
    print(opt)

    # CHANGE: librosa_config is replaced by a "feature recipes" dict
    # CHANGE: we need to build the "recipes" from the command line args here
    feat_recipes = None
    if opt.task == 'run' or 'build':
        feat_recipes = {}
        # put "len_window" into "rmse" recipes
        feat_recipes['rmse'] = {'len_window': opt.len_window}
        # for other recipes, use:
        # feat_recipes['other_feature_extraction_func'] = {
        #     'func_arg_0': opt.func_arg_0,
        #     'func_arg_1': opt.func_arg_1,
        #     ...
        # }

    # CHANGE: now main function only requires opt and feature recipes
    _main(opt, feat_recipes)

main()