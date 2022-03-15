import pickle
import os, glob
from typing import Any, List
from collections import UserDict

class AudioFeatureBundle(UserDict):
    def frame_len(self) -> int:
        return self.data['meta']['len_hop']
    
    def sample_rate(self) -> int:
        return self.data['meta']['sr']
    
    def sample_len(self) -> int:
        return self.data['meta']['len_sample']
    
    def feature_names(self) -> List[str]:
        return self.data['meta']['audfeats']

    def feature_data(self, name:str, prop:str='data') -> Any:
        return self.data[name][prop]
    
    def feature_dict(self, name:str) -> dict:
        return self.data[name]

    def save(self, dst:str) -> None:
        os.makedirs(dst, exist_ok=True)

        for k in self.keys():
            filename = os.path.join(dst, k+'.pkl')
            if not os.path.exists(filename):
                with open(filename, 'wb') as f:
                    pickle.dump(self.feature_dict, f)

    @classmethod
    def from_folder(cls, folder):
        vibrations = glob.glob(f"{folder}/*.pkl")
        vibrations = {os.path.basename(v).split(".")[0] : v for v in vibrations}

        fb = cls()
        with open(vibrations["meta"], "rb") as f:
            meta = pickle.load(f)
        fb.update({'meta': meta})

        for aud in meta["recipe"]:
            with open(vibrations[aud], "rb") as f:
                fb.update({aud: pickle.load(f)})

        return fb
