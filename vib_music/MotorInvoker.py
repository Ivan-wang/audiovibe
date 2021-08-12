import os
import glob
import pickle

class MotorInvoker(object):
    motor_t = {}
    iterator_t = {}
    def __init__(self, basedir, audio, motors=[]):
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

    def _build_vib_iter(self, vib_t, audio_meta, vib_data):
        if vib_t not in MotorInvoker.iterator_t:
            print(list(self.iterator_t.keys()))
            raise KeyError(f'Cannot build iterator for {vib_t}')

        return MotorInvoker.iterator_t[vib_t](audio_meta, vib_data)

    def _init_motors(self, motor_t):
        motors = []
        for (name, kwargs) in motor_t:
            if name in MotorInvoker.motor_t:
                motors.append(MotorInvoker.motor_t[name](**kwargs))
            else:
                print(f'Unrecongnized Motor Type {name}')

        return motors

    def on_start(self, runtime):
        # TODO: how to handle environment
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
        return cls(config['datadir'], config['audio'], config['motors'])

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
