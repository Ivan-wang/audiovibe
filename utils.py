import librosa

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

from matplotlibMotor import MatplotlibMotor 
def list_matplotlib_invoker():
    ks = list(MatplotlibMotor.commands)

    print(f'Available Matplotlib Invoker Strategies : {ks}')

from boardInvoker import BoardInvoker
def list_matplotlib_invoker():
    ks = list(BoardInvoker.motor_t)

    print(f'Available Board Motors: {ks}')

def get_feature(features, k=None, prefix=None):
    if k is not None and k in features:
        return features[k]
    
    for name in features:
        if name.startswith(prefix):
            return features[name]

    return None 

def load_config(cfg):
    with open(cfg, 'r') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    
    ctx = LibrosaContext(audio=cfg['audio'], sr=cfg['sr'], stg=cfg['strategy'])
    venc = VibrationEncoder(stg=cfg['vibration_enc'])

    motors = [(k, v) for k, v in cfg['motors'].items()]
    invoker = BoardInvoker(motors=motors)

    return ctx, venc, invoker

if __name__ == '__main__':
    list_librosa_context()
    list_vibration_encoder()
    list_matplotlib_invoker()