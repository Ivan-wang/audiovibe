import yaml

from pprint import pprint
from collections import OrderedDict
FRAME_LEN = 4096
HOP_LEN = 1024
PLP_FRAME = 300

def demo_config(save=None):
    config = OrderedDict() # use OrderedDict for easy reading
    config['version'] = 0.1

    # audio
    config['audio'] = None
    config['sr'] = None

    # librosa context config
    strategy = {
        'rmse': {'frame': FRAME_LEN, 'hop': HOP_LEN},
        'pitchyin': {'frame': FRAME_LEN, 'hop': HOP_LEN, 'thres': 0.8},
        'beatplp': {'hop': HOP_LEN, 'num_frame': PLP_FRAME}
    }
    
    config['strategy'] = strategy

    # vibration encoder
    vibration_enc = [
        'rmse_level'
    ]
    config['vibration_enc'] = vibration_enc

    # board invoker
    motors = {
        # motor, [features,...]
        'console': ['rmse', 'pitchyin']
    }
    config['motors'] = motors

    pprint(config)

    if save is not None:
        with open(save, 'w') as f:
            yaml.dump(dict(config), f, sort_keys=False)
        
    return config

if __name__ == '__main__':
    demo_config('configs/demo.yaml')