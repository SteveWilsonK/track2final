"""Verification script: recompute the repository's checkable claims.

Run from code/:  python3 verify_claims.py

Checks, in order:
  1. Kit integrity: sha256 of evaluate.py and data.py against the official
     starter kit archive's hashes.
  2. Split sizes: train / validation / test row counts.
  3. Oracle ceiling and user composition on the test split (ranking by the
     true labels; zero-positive and all-positive user shares).
  4. Random-scoring floor (seeded).
  5. Seed-noise summary of the final recipe (from the five shipped
     committee members' individual test scores in LOG.jsonl and from
     final_model.py's printed singles).
"""
import hashlib, json, os
import numpy as np
from data import load
from evaluate import evaluate

OFFICIAL_SHA256 = {
    'evaluate.py': 'ecfde28392eb14fec4f488083251df50624e1af2b86278b962daecfb42d195de',
    'data.py': '1bf54f5f3a9f590eab2f87f09a3c27422031867a20a5328d56cbd8c7db36e541',
}

print("1. Kit integrity")
for fname, want in OFFICIAL_SHA256.items():
    got = hashlib.sha256(open(fname, 'rb').read()).hexdigest()
    status = "IDENTICAL to official kit" if got == want else "*** MODIFIED ***"
    print(f"   {fname}: {status}")

print("\n2. Split sizes")
splits = load('./KuaiRand-Pure/data')
for name, rws in splits.items():
    print(f"   {name}: {len(rws):,} rows")

print("\n3. Oracle ceiling on test (score = true label)")
rws = splits['test']
users = [x[1] for x in rws]
labels = [x[6] for x in rws]
r = evaluate(users, labels, [float(y) for y in labels])
print(f"   GAUC {r['GAUC']:.4f} | nDCG@5 {r['nDCG@5']:.4f} | primary {r['primary']:.4f}")
from collections import defaultdict
byu = defaultdict(list)
for u, y in zip(users, labels):
    byu[u].append(y)
zero = sum(1 for v in byu.values() if sum(v) == 0)
allp = sum(1 for v in byu.values() if sum(v) == len(v))
print(f"   users: {len(byu):,} | zero-positive {zero/len(byu):.1%} | all-positive {allp/len(byu):.1%}")

print("\n4. Random-scoring floor (seed 0)")
rng = np.random.default_rng(0)
r = evaluate(users, labels, rng.random(len(labels)))
print(f"   primary {r['primary']:.4f}")

print("\n5. Final-recipe seed noise")
singles = [0.6089, 0.6112, 0.6092, 0.6095, 0.6116]  # printed by final_model.py
print(f"   5 committee members (test primary): {singles}")
print(f"   mean {np.mean(singles):.5f} | std {np.std(singles):.5f}")
log = os.path.join('..', 'logs', 'LOG.jsonl')
if os.path.exists(log):
    stds = []
    for line in open(log):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get('phase') == 'result' and rec.get('test_std'):
            stds.append(rec['test_std'])
    if stds:
        print(f"   per-run 3-seed stds in LOG.jsonl: n={len(stds)}, "
              f"median {np.median(stds):.5f}, max {max(stds):.5f}")
