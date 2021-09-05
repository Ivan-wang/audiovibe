import yaml
from .features import LibrosaContext

def list_librosa_context():
    ks = list(LibrosaContext.stg_funcs.keys())
    meta_ks = list(LibrosaContext.stg_meta_funcs.keys())

    print(f'Available Librosa Strategies : {ks}')
    print(f'Available Librosa Meta Strategies : {meta_ks}')

from .invoker import MotorInvoker
def list_matplotlib_invoker():
    ks = list(MotorInvoker.motor_t)

    print(f'Available Board Motors: {ks}')

def get_feature(features, k=None, prefix=None):
    if k is not None and k in features:
        return features[k]

    for name in features:
        if name.startswith(prefix):
            return features[name]

    return None

if __name__ == '__main__':
    list_librosa_context()