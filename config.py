import yaml

from librosaContext import LibrosaContext
def list_librosa_context():
    ks = list(LibrosaContext.stg_funcs.keys())
    meta_ks = list(LibrosaContext.stg_meta_funcs.keys())

    print(f'Available Librosa Strategies : {ks}')
    print(f'Available Librosa Meta Strategies : {meta_ks}')

from vibrationEncoder import VibrationEncoder
def list_vibration_encoder():
    ks = list(VibrationEncoder.enc_funcs)

    print(f'Available Vibration Encoder Strategies : {ks}')

from matplotlibInvoker import MatplotlibInvoker
def list_matplotlib_invoker():
    ks = list(MatplotlibInvoker.commands)

    print(f'Available Matplotlib Invoker Strategies : {ks}')

from boardInvoker import BoardInvoker
def list_matplotlib_invoker():
    ks = list(BoardInvoker.motor_t)

    print(f'Available Board Motors: {ks}')

from pprint import pprint
from collections import OrderedDict
def demo_config(save=None):
    config = OrderedDict()
    config['version'] = 0.1

    # audio
    config['audio'] = None
    config['sr'] = 48000

    # librosa context config
    strategy = [
        'rmse_1024_512',
        'pitchyin_2048_512_0.8'
    ]
    config['strategy'] = strategy

    # vibration encoder
    vibration_enc = [
        'rmse_enc'
    ]
    config['vibration_enc'] = vibration_enc

    # board invoker
    motors = {
        # motor, [features,...]
        'console': ['rmse']
    }
    config['motors'] = motors

    pprint(config)

    if save is not None:
        with open(save, 'w') as f:
            yaml.dump(dict(config), f)

def load_config(cfg):
    with open(cfg, 'r') as f:
        cfg = yaml.load(f)
    
    ctx = LibrosaContext(audio=cfg['audio'], sr=cfg['sr'], stg=cfg['strategy'])
    venc = VibrationEncoder(stg=cfg['vibration_enc'])
    bid = BoardInvoker(motors=cfg['motors'])

    return ctx, venc, bid

if __name__ == '__main__':
    list_librosa_context()
    list_vibration_encoder()
    list_matplotlib_invoker()
    demo_config('configs/demo.yaml')