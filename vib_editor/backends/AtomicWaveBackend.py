import sys
import pickle
import numpy as np
from typing import List, Optional
from collections import UserDict

sys.path.append('..')
from vib_music import AudioStream

class AtomicWaveDatabase(UserDict):
    def save(self, to:str) -> None:
        with open(to, 'wb') as f:
            pickle.dump(self.data)

    def load(self, _from:str) -> None:
        with open(_from, 'rb') as f:
            db = pickle.load(f)
        self.data.update(db)

    def init_db(self) -> None:
        db = {'uniform': {}, 'linear': {}, 'quadratic': {}}

        base0 = np.zeros((24, ))
        base1 = np.ones((24, )) * 0.99
        
        c4_3 = base1.copy()
        c4_3[0::6] = 0.01
        c4_3[1::6] = 0.01
        c4_3[2::6] = 0.01
        
        c4_4 = base1.copy()
        c4_4[0::6] = 0.01
        c4_4[1::6] = 0.01
        
        c4_5 = base1.copy()
        c4_5[0::6] = 0.01
        
        c6_2 = base1.copy()
        c6_2[0::4] = 0.01
        c6_2[1::4] = 0.01
        
        db['uniform'].update({
            'u2-4': np.array([0.01]*8+[0.99]*4+[0.01]*8+[0.99]*4),
            'u2-6': np.array([0.01]*6+[0.99]*6+[0.01]*6+[0.99]*6),
            'u2-8': np.array([0.01]*4+[0.99]*8+[0.01]*4+[0.99]*8),
            'u4-3': c4_3, 'u4-4': c4_4, 'u4-5': c4_5, 'u6-2': c6_2
        })
        
        l1_12 = np.linspace(0.01, 0.99, num=13, endpoint=True)[1:]
        l1_12 = np.stack([l1_12, np.zeros_like(l1_12)+0.01], axis=-1)
        l1_12 = l1_12.reshape((-1,))
        
        l2_8 = np.linspace(0.01, 0.99, num=7, endpoint=True)[1:]
        l2_8 = np.stack([l2_8, np.zeros_like(l2_8)+0.01], axis=-1)
        l2_8 = np.concatenate([l2_8.reshape((-1,))]*2)
        
        db['linear'].update({
            'l1_12_a': np.round(l1_12, 2), 'l1_12_d': np.round(l1_12[::-1].copy(), 2),
            'l2_8_a': np.round(l2_8, 2), 'l2_8_d': np.round(l2_8[::-1].copy(), 2),
            'l2_8_s': np.round(np.concatenate([l2_8[:12], l2_8[11:-1][::-1]]), 2),
            'l2_8_si': np.round(np.concatenate([l2_8[11:-1][::-1], l2_8[:12]]), 2),
        })
        
        q1_12 = np.linspace(0., 0.99, num=13, endpoint=True)[1:] ** 2
        q1_12 = np.stack([q1_12, np.zeros_like(q1_12)], axis=-1)
        q1_12 = q1_12.reshape((-1,))
        
        q2_8 = np.linspace(0, 0.99, num=7)[1:] ** 2
        q2_8 = np.stack([q2_8, np.zeros_like(q2_8)+0.01], axis=-1)
        q2_8 = np.concatenate([q2_8.reshape((-1,)), q2_8.reshape((-1,))])
        
        db['quadratic'].update({
            'q1_12_a': np.round(q1_12, 2), 'q2_12_d': np.round(q1_12[::-1].copy(), 2),
            'q2_8_a': np.round(q2_8, 2), 'q2_8_d': np.round(l2_8[::-1].copy(), 2),
            'q2_8_s': np.round(np.concatenate([q2_8[:12], q2_8[11:-1][::-1]]), 2),
            'q2_8_si': np.round(np.concatenate([q2_8[11:-1][::-1], q2_8[:12]]), 2),
        
        })

        self.data.update(db)

class AtomicWaveBackend(object):
    def __init__(self, database:Optional[str]=None):
        super(AtomicWaveBackend, self).__init__()
        
        self.database = AtomicWaveDatabase()
        if database is not None:
            self.database.load(database)
        else:
            self.database.init_db()
    
    def list_atomic_family_name(self) -> List[str]:
        return sorted(list(self.database.keys()))

    def list_atomic_wave_names(self, family:str) -> List[str]:
        return sorted(list(self.database[family].keys()))

    def get_atomic_wave(self, family:str, wave:str) -> np.ndarray:
        return self.database[family][wave]

    def contains_family(self, family:str) -> bool:
        return family in self.database    
    
    def add_family(self, family:str) -> None:
        self.database.setdefault(family, {})
    
    def add_atomic_wave(self, family:str, wave_name:str, wave_data:np.ndarray) -> None:
        self.add_family(family)
        self.database[family].update({wave_name:wave_data})

    def save_database(self, to:str) -> None:
        self.database.save(to)

class MonoFrameAudioStream(AudioStream):
    def __init__(self, num_frame:int, len_frame: int) -> None:
        super().__init__(np.zeros((len_frame,), dtype=np.uint16), len_frame)
        self.next_frame = 0
        self.num_frame = num_frame
    
    def init_stream(self) -> None:
        super().init_stream()
    
    def getnframes(self) -> int:
        return self.num_frame
    
    def readframe(self, n: int = 1):
        if self.next_frame == self.num_frame:
            return ''
        else:
            self.next_frame += 1
            return self.chunks.tostring()
    
    def tell(self) -> int:
        return self.next_frame
    
    def setpos(self, pos: int) -> None:
        self.next_frame = pos
    
    def rewind(self) -> None:
        self.next_frame = 0

    def close(self) -> None:
        pass
        
    def getframerate(self) -> int:
        return 44100
    
    def getnchannels(self) -> int:
        return 1
    
    def getsampwidth(self) -> int:
        return 2

