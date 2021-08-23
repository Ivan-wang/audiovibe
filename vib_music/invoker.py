import os
import glob
import pickle

class MotorInvoker(object):
    motor_t = {}
    iterator_t = {}
    vibration_mode = {}
    def __init__(self, basedir, audio, vib_mode, motors=[]):
        super(MotorInvoker, self).__init__()
        self.motors = self._init_motors(motors)

        audio = os.path.basename(audio).split('.')[0]
        vibrations = glob.glob(f'{basedir}/{audio}/*.pkl')
        vibrations = {os.path.basename(v).split('.')[0] : v for v in vibrations}
        with open(vibrations['meta'], 'rb') as f:
            self.meta = pickle.load(f)

        self.vib_iter = {'frame': self._build_vib_iter('frame', None, None)}
        for vib in self.meta['vibrations']:
            with open(vibrations[vib], 'rb') as f:
                self.vib_iter[vib] = self._build_vib_iter(vib, self.meta, pickle.load(f))

        self.total_frame = self.meta['len_sample'] // self.meta['len_hop']
        if self.meta['len_sample'] % self.meta['len_hop'] == 1:
            self.total_frame += 1
        
        self.vib_mode = vib_mode

    def _build_vib_iter(self, vib_t, audio_meta, vib_data, **kwargs):
        if vib_t in MotorInvoker.iterator_t:
            return MotorInvoker.iterator_t[vib_t](audio_meta, vib_data, **kwargs)
        else:
            for k in self.iterator_t.keys():
                if vib_t.startswith(k):
                    return MotorInvoker.iterator_t[k](audio_meta, vib_data, **kwargs)
            print(f'Available Iterators : {list(self.iterator_t.keys())}')
            raise KeyError(f'Cannot build iterator for {vib_t}')


    def _init_motors(self, motor_t):
        motors = []
        for (name, kwargs) in motor_t:
            if name in MotorInvoker.motor_t:
                motors.append(MotorInvoker.motor_t[name](**kwargs))
            else:
                print(f'Unrecongnized Motor Type {name}')

        return motors
    
    def _build_vibration_signals(self):
        bundle = {k: i.feature for k, i in self.vib_iter.items()}
        amp, freq = MotorInvoker.vibration_mode[self.vib_mode](bundle)

        self.vib_iter.update({
            'amp': self._build_vib_iter('amp', None, amp),
            'freq': self._build_vib_iter('freq', None, freq)
        })

    def on_start(self, runtime):
        # TODO: how to handle environment
        self._build_vibration_signals()
        for m in self.motors:
            m.on_start(runtime)

    def on_update(self):
        bundle = {k: next(i) for k, i in self.vib_iter.items()}
        for m in self.motors:
            m.on_running(bundle)

    def on_end(self):
        for m in self.motors:
            m.on_end()

    @classmethod
    def from_config(cls, config):
        return cls(config['datadir'], config['audio'],
            config['vib_mode'], config['motors'])

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
