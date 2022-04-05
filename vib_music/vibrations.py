import numpy as np

from .core import AudioFeatureBundle
from .streams import VibrationStream

@VibrationStream.vibration_mode(over_ride=False)
def rmse_mode(fb:AudioFeatureBundle) -> np.ndarray:
    rmse = fb.feature_data('rmse')

    rmse = (rmse-rmse.min()) / (rmse.max()-rmse.min())
    rmse = rmse ** 2

    # digitize features
    bins = np.linspace(0., 1., 150, endpoint=True)
    voltage = np.digitize(rmse, bins).astype(np.uint8)

    vibrations = np.stack([voltage]*4 + [np.zeros_like(voltage)]*4, axis=-1)
    vibrations = np.concatenate([vibrations]*3, axis=-1)
    vibrations = vibrations.reshape((-1,))

    print(f'vibration shape {vibrations.shape}')

    return vibrations