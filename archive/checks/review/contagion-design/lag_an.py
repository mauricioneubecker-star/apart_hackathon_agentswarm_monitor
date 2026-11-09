import sys; sys.path.insert(0, '.')
import numpy as np
from mhlib import mh_acc, summarize, fmt
z = np.load('data/lag_w3.npz'); A = z['A']; cols = list(z['cols'])
D = {c: A[:, i] for i, c in enumerate(cols)}; D['cfg'] = z['cfg']; D['run'] = z['run']
B = cols[4:]
dm = D['dm_any'] == 1
nonnever = np.zeros(len(A), bool)
for b in B[:-1]: nonnever |= D[b] == 1
only = {b: (D[b] == 1) & (np.sum([D[c] for c in B[:-1] if c != b], axis=0) == 0) for b in B[:-1]}
ref = dm & ~nonnever   # DMs only from never-violators
print('reference rows', int(ref.sum()), 'adopt', int(D['Y'][ref].sum()), f"rate {D['Y'][ref].mean():.4f}")
for b in B[:-1]:
    ex = only[b]
    m = ref | ex
    print(f"{b:16s} only-this-lag n={int(ex.sum()):6d} ad={int(D['Y'][ex].sum()):4d} crude={D['Y'][ex].mean():.4f} |", fmt(summarize(mh_acc(D, m, ex.astype(float)))))
print('--- any-bucket (not exclusive), vs rows without that bucket, within dm>0')
for b in B:
    print(f"{b:16s}", fmt(summarize(mh_acc(D, dm, D[b]))))
