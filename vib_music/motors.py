from .invoker import MotorInvoker

from tqdm import tqdm
from abc import abstractmethod

class Motor(object):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def on_start(self, runtime):
        pass

    @abstractmethod
    def on_running(self, vibrations):
        pass

    @abstractmethod
    def on_end(self):
        pass

def _build_vibration_str(bundle, show_none=True, show_frame=True):
    vibs = []
    for k in bundle:
        if k == 'frame':
            continue
        if bundle[k] is not None:
            vibs.append('{} : {}'.format(k, bundle[k]))
        elif show_none:
            vibs.append('{} : {}'.format(k, bundle[k]))
        else:
            pass

    if show_frame and len(vibs) > 0:
        vibs.append('{} : {}'.format('frame', bundle['frame']))
    vib_str = ' | '.join(vibs)
    return vib_str

@MotorInvoker.register_motor
class ConsoleMotor(Motor):
    alias = 'console'
    def __init__(self, show_none=True, show_frame=True):
        super().__init__()
        self.handler = lambda bundle: _build_vibration_str(bundle, show_none, show_frame)

    def on_start(self, runtime):
        total_frame = runtime.invoker.num_frame
        self.bar = tqdm(desc='[Console Motor]', unit=' frame', total=total_frame)

    def on_running(self, bundle):
        vib_str = self.handler(bundle)
        if len(vib_str) != 0:
            if len(vib_str) > 80:
                tqdm.write(vib_str)
            else:
                self.bar.set_postfix(bundle, refresh=True)
        self.bar.update()

    def on_end(self):
        self.bar.close()

    def _build_vibration_str(self, vibrations):
        vibs = []
        for k in vibrations:
            if k == 'frame':
                continue
            if vibrations[k] is not None:
                vibs.append('{} : {}'.format(k, vibrations[k]))
            elif self.show_none:
                vibs.append('{} : {}'.format(k, vibrations[k]))
            else:
                pass

        if self.show_frame and len(vibs) > 0:
            vibs.append('{} : {}'.format('frame', vibrations['frame']))
        vib_str = ' | '.join(vibs)
        return vib_str

@MotorInvoker.register_motor
class BoardMotor(Motor):
    alias = 'board'
    def __init__(self):
        self.vib_queue = None

    def on_start(self, runtime):
        self.vib_queue = runtime.vib_queue

    def on_running(self, bundle):
        amp, freq = bundle['amp'], bundle['freq']

        if amp is not None:
            self.vib_queue.put((amp, freq, False))
        else:
            self.vib_queue.put((0, 0, True))

    def on_end(self):
        self.vib_queue.put((0, 0, True))
