import os
import numpy as np
import pickle

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

import os

os.makedirs('../data', exist_ok=True)
with open('../data/atomic-wave.pkl', 'wb') as f:
    pickle.dump(db, f)