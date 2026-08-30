"""Post-freeze analysis 2: unbiased evaluation on randomly-exposed videos.

KuaiRand's defining asset is log_random: impressions where the video was
chosen uniformly at random rather than by a recommender, which removes
selection bias from evaluation (the dataset authors designed it for
exactly this; see kuairand.com). We retired this file from TRAINING on
temporal-leakage grounds, and that stands. Using it for EVALUATION only is
legal and is the sound use: no model here is trained, tuned, or selected
on these rows.

What this measures: within-user ranking quality on ~898k test-window
impressions whose exposure carries no recommender bias. The standard-log
test set answers "can you rank what the old system chose to show"; this
set answers "can you rank videos drawn without favor" — closer to true
preference modeling.

Method: the frozen committee (shipped weights, bit-identical) scores the
random test-window rows. Features are built causally over the user's full
experienced stream (standard + random impressions, time-ordered; each row
sees strictly-prior events only, same rule as everywhere). The official
kit FM baseline is retrained on the standard training split (its normal
recipe, seed 0) and scored on the same rows. evaluate.py is the official
scorer, unmodified.

Run from code/:  python3 unbiased_eval.py     (~5 min)
"""
import csv, os, collections
import numpy as np
from evaluate import evaluate
from baseline import FM, run_fm
from data import load
from sequences import load_sequenced, encode_rows, BASE, SEQ, DATA


def load_random_rows():
    vid2author = {}
    with open(os.path.join(DATA, 'video_features_basic_pure.csv')) as fh:
        for r in csv.DictReader(fh):
            vid2author[r['video_id']] = r['author_id']
    rows = []
    with open(os.path.join(DATA, 'log_random_4_22_to_5_08_pure.csv')) as fh:
        for r in csv.DictReader(fh):
            rows.append({
                'date': int(r['date']), 't': int(r['time_ms']),
                'user_id': r['user_id'], 'video_id': r['video_id'],
                'author_id': vid2author.get(r['video_id'], 'UNK'),
                'tab': r['tab'], 'duration': float(r['duration_ms']),
                'y': 1 if r['long_view'] != '0' else 0,
                'is_random': True,
            })
    return rows


RICH = BASE + SEQ + ['hist30', 'tag_hist', 'gap']
TEST_START = 20220429

print("loading standard stream + random log ...")
splits = load_sequenced()
random_rows = load_random_rows()
print(f"random rows total {len(random_rows):,}; "
      f"test-window {sum(1 for x in random_rows if x['date'] >= TEST_START):,}")

# causal features over the user's full experienced stream
vid2tag = {}
with open(os.path.join(DATA, 'video_features_basic_pure.csv')) as fh:
    for r in csv.DictReader(fh):
        vid2tag[r['video_id']] = (r['tag'] or 'UNK').split(',')[0].strip() or 'UNK'

all_rows = [x for rws in splits.values() for x in rws] + random_rows
all_rows.sort(key=lambda x: (x['user_id'], x['date'], x['t']))
hist = {}
for x in all_rows:
    u = x['user_id']
    if u not in hist:
        hist[u] = {'last30': collections.deque(maxlen=30),
                   'tag': collections.Counter(), 'last_t': None,
                   'last10': collections.deque(maxlen=10), 'n': 0,
                   'prev1': None, 'auth': collections.Counter()}
    h = hist[u]
    x['prev1'] = 'none' if h['prev1'] is None else str(h['prev1'])
    x['hist10'] = 'none' if not h['last10'] else str(sum(h['last10']))
    n = h['n']
    x['hist_n'] = ('0' if n == 0 else '1-3' if n <= 3 else '4-10' if n <= 10
                   else '11-30' if n <= 30 else '31-100' if n <= 100 else '100+')
    a = h['auth'][x['author_id']]
    x['auth_hist'] = str(a) if a < 3 else '3+'
    x['hist30'] = ('none' if not h['last30']
                   else str(int(10 * sum(h['last30']) / len(h['last30']))))
    tg = vid2tag.get(x['video_id'], 'UNK')
    tc = h['tag'][tg]
    x['tag_hist'] = str(tc) if tc < 3 else '3+'
    if h['last_t'] is None:
        x['gap'] = 'none'
    else:
        d = (x['date'] - h['last_t'][0]) * 86400_000 + (x['t'] - h['last_t'][1])
        x['gap'] = ('<1m' if d < 60_000 else '<1h' if d < 3_600_000
                    else '<1d' if d < 86_400_000 else '1d+')
    # update after featurizing (own label never in own features)
    h['prev1'] = x['y']; h['last10'].append(x['y']); h['n'] += 1
    h['auth'][x['author_id']] += x['y']
    h['last30'].append(x['y'])
    h['tag'][tg] += x['y']
    h['last_t'] = (x['date'], x['t'])

rand_test = [x for x in random_rows if x['date'] >= TEST_START]

# encode with the SAME train-built vocab as the frozen weights
eval_splits = {'train': splits['train'], 'valid': splits['valid'],
               'test': rand_test}
enc, dim = encode_rows(eval_splits, RICH)
Xrt, yrt, urt = enc['test']

def _frozen_dir():
    for c in ('frozen_model', os.path.join('..', 'final_output', 'frozen_model')):
        if os.path.exists(os.path.join(c, 'fm_seed0.npz')):
            return c
    raise FileNotFoundError('frozen weights not found')

print("\nscoring the frozen committee on randomly-exposed test rows ...")
preds = []
frozen = _frozen_dir()
for seed in range(5):
    z = np.load(os.path.join(frozen, f'fm_seed{seed}.npz'))
    m = FM(dim, k=16, seed=seed)
    assert m.V.shape == z['V'].shape
    m.V, m.W, m.b = z['V'], z['W'], np.float32(z['b'])
    p = m.predict(Xrt)
    preds.append((p - p.mean()) / p.std())
ours = evaluate(urt, yrt, np.mean(preds, 0))

print("retraining the official kit baseline (seed 0) and scoring it on the same rows ...")
kit_splits = load('./KuaiRand-Pure/data')
kit_splits_eval = {'train': kit_splits['train'], 'valid': kit_splits['valid'],
                   'test': [(x['date'], x['user_id'], x['video_id'],
                             x['author_id'], x['tab'], x['duration'], x['y'])
                            for x in rand_test]}
base = run_fm(kit_splits_eval, seed=0, verbose=False)['test']

print("\n=== UNBIASED (RANDOM-EXPOSURE) TEST-WINDOW EVALUATION ===")
print(f"rows {len(rand_test):,} | users {ours['users']:,}")
print(f"{'model':<28} {'GAUC':>8} {'nDCG@5':>8} {'primary':>9}")
print(f"{'official FM baseline':<28} {base['GAUC']:>8.4f} {base['nDCG@5']:>8.4f} {base['primary']:>9.4f}")
print(f"{'frozen submission (ours)':<28} {ours['GAUC']:>8.4f} {ours['nDCG@5']:>8.4f} {ours['primary']:>9.4f}")
print(f"delta on unbiased exposure: {ours['primary'] - base['primary']:+.4f}")
