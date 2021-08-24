import os
import glob
import pickle
import math
import numpy as np

def _process_invoker_config(config):
    print(config)
    basedir = config['datadir']
    audio = config['audio']

    # check audio
    if not os.path.exists(audio):
        return None

    # load vibrations
    audio = os.path.basename(audio).split('.')[0]
    vibrations = glob.glob(f'{basedir}/{audio}/*.pkl')
    vibrations = {os.path.basename(v).split('.')[0] : v for v in vibrations}
    print(vibrations)

    try:
        with open(vibrations['meta'], 'rb') as f:
            meta = pickle.load(f)
    except:
        print('cannot load audio meta information')
        return None
    
    vib_iter = {}
    try:
        for vib in meta['vibrations']:
            with open(vibrations[vib], 'rb') as f:
                vib_iter[vib] = MotorInvoker._build_vib_iter(
                    vib, meta, pickle.load(f))
    except:
        print('cannot initialize vibration iterator')
        return None
    
    # build motors
    motors = config['motors']
    try:
        motors = MotorInvoker._build_motors(motors)
    except:
        print('cannot initialize motors')
        return None

    # build vibration signals
    num_frame = int(math.ceil(meta['len_sample'] / meta['len_hop']))
    vib_mode = config['vib_mode']
    try:
        vib_iter = MotorInvoker._build_vibration_signals(num_frame, vib_mode, vib_iter)
    except:
        print('build vibration signals failed')
        return None

    return {'num_frame': num_frame, 'vib_iterators': vib_iter, 'motors': motors}

class MotorInvoker(object):
    motor_t = {}
    iterator_t = {}
    vibration_mode = {}
    def __init__(self, num_frame, vib_iterators, motors):
        self.num_frame = num_frame
        self.vib_iterators = vib_iterators
        self.motors = motors

        self.vib_iterators.update({
            'frame': MotorInvoker._build_vib_iter('frame', None, None)
        })

    def on_start(self, runtime):
        for m in self.motors:
            m.on_start(runtime)

    def on_update(self):
        bundle = {k: next(i) for k, i in self.vib_iterators.items()}
        for m in self.motors:
            m.on_running(bundle)

    def on_end(self):
        for m in self.motors:
            m.on_end()

    @classmethod
    def _build_vib_iter(cls, vib_t, audio_meta, vib_data):
        if vib_t in cls.iterator_t:
            return cls.iterator_t[vib_t](audio_meta, vib_data)
        else:
            for k in cls.iterator_t.keys():
                if vib_t.startswith(k):
                    return cls.iterator_t[k](audio_meta, vib_data)
            print(f'Available Iterators : {list(cls.iterator_t.keys())}')
            raise KeyError(f'Cannot build iterator for {vib_t}')

    @classmethod
    def _build_motors(cls, motor_t):
        motors = []
        for (name, kwargs) in motor_t:
            if name in cls.motor_t:
                motors.append(cls.motor_t[name](**kwargs))
            else:
                print(f'Unrecongnized Motor Type {name}')

        return motors

    @classmethod
    def _build_vibration_signals(cls, num_frame, vib_mode, vib_iterators):
        bundle = {k: i.feature for k, i in vib_iterators.items()}
        amp, freq = cls.vibration_mode[vib_mode](bundle)
        if len(amp) != num_frame:
            amp = np.concatenate([amp, np.zeros((num_frame,), dtype=np.uint8)])
            amp = amp[:num_frame]

        if len(freq) != num_frame:
            freq = np.concatenate([freq, np.zeros((num_frame,), dtype=np.uint8)])
            freq = freq[:num_frame]

        vib_iterators.update({
            'amp': cls._build_vib_iter('amp', None, amp),
            'freq': cls._build_vib_iter('freq', None, freq)
        })
        return vib_iterators

    @classmethod
    def from_config(cls, config):
        # TODO: Check Configures
        kwargs = _process_invoker_config(config)
        if kwargs is None:
            return None
        return cls(**kwargs)

    @classmethod
    def register_motor(cls, motor_cls):
        alias = getattr(motor_cls, 'alias', None)
        if alias is not None:
            cls.motor_t[alias] = motor_cls
        return motor_cls

    @classmethod
    def register_vib_iterator(cls, vib_iter_cls):
        alias = getattr(vib_iter_cls, 'alias', None)
        if alias is not None:
            cls.iterator_t[alias] = vib_iter_cls
        return vib_iter_cls

    @classmethod
    def register_vibration_mode(cls, mode_func):
        if mode_func.__name__ in cls.vibration_mode:
            raise KeyError('Cannot register duplicated vibration mode {mode_func.__name__}')
        cls.vibration_mode.update({
            mode_func.__name__: mode_func
        })
        return mode_func
