from boardInvoker import Motor
from pprint import pprint
from tqdm import tqdm

from config import HOP_LEN

class ConsoleMotor(Motor):
    alias = 'console'
    def __init__(self, show_none=True, show_frame=True):
        super().__init__()
        self.show_none = show_none
        self.show_frame = show_frame

    def on_start(self, meta):
        total_frame = meta['len_sample'] // HOP_LEN
        if meta['len_sample'] % HOP_LEN != 0:
            total_frame += 1
        self.bar = tqdm(desc='[Console Motor]', unit=' frame', total=total_frame)

    def on_running(self, vibrations):
        vib_str = self._build_vibration_str(vibrations)
        if len(vib_str) > 0:
            tqdm.write(vib_str)
        self.bar.update()

    def on_end(self):
        self.bar.close()
    
    def _build_vibration_str(self, vibrations):
        vibs = []
        for k in vibrations:
            if k == 'frame':
                continue
            if self.show_none or vibrations[k] is not None:
                vibs.append('{} : {}'.format(k, vibrations[k]))
        if self.show_frame and len(vibs) > 0:
            vibs.append('{} : {}'.format('frame', vibrations['frame']))
        vib_str = ' | '.join(vibs)
        return vib_str

if __name__ == '__main__':
    from boardInvoker import BoardInvoker
    print(BoardInvoker.motor_t)
    audioname = 'YellowRiverInstrument'
    motors = [('console', {'show_frame': True, 'show_none': False})]
    bid = BoardInvoker(audioname, motors=motors)
    bid.on_start()
    for _ in range(10):
        bid.on_update()

