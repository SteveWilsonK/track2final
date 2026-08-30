"""Pillar 3b: hypotheses from the model's actual mistakes, not brainstorming.

Slices the frozen model's validation predictions by row attributes the
pipeline already computes (user history depth, tab, video-duration bucket),
scores each slice with the official evaluate() on the filtered subset, and
ranks slices by expected value: (overall - slice score) x share of users.
The worst slice becomes a structured hypothesis written into the belief
state, with a mechanism suggestion attached.

Uses evaluate.py completely unmodified — subsets in, scores out.

Run from code/ (needs dataset + frozen weights):
    python3 ../agent/residual_analysis.py
Self-test (synthetic, no dataset):
    python3 residual_analysis.py --selftest
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'code'))
import numpy as np
from evaluate import evaluate


def slice_report(users, labels, scores, tags, min_users=50):
    """tags: list of dicts per row, e.g. {'hist': 'cold', 'tab': '1'}.
    Returns [(slice_name, primary, n_users, expected_value)] sorted worst-first
    by expected value."""
    overall = evaluate(users, labels, scores)['primary']
    total_users = len(set(users))
    out = []
    keys = tags[0].keys()
    for k in keys:
        vals = sorted({t[k] for t in tags})
        for v in vals:
            idx = [i for i, t in enumerate(tags) if t[k] == v]
            su = [users[i] for i in idx]
            n_u = len(set(su))
            if n_u < min_users:
                continue
            r = evaluate(su, [labels[i] for i in idx],
                         [scores[i] for i in idx])['primary']
            ev = max(0.0, overall - r) * (n_u / total_users)
            out.append((f"{k}={v}", r, n_u, ev))
    out.sort(key=lambda x: -x[3])
    return overall, out


MECHANISM_HINT = {
    'hist': 'temporal',    # history-depth slices point at sequence starvation
    'tab': 'none',         # surface slices: no single mechanism implied
    'dur': 'capacity',     # duration slices: representation granularity
}


def to_hypothesis(slice_name, slice_primary, overall, n_users, ev):
    key = slice_name.split('=')[0]
    return {
        'id': f"residual_{slice_name.replace('=', '_')}",
        'claim': (f"slice {slice_name} scores {slice_primary:.4f} vs overall "
                  f"{overall:.4f} across {n_users} users; a feature or prior "
                  f"targeted at this slice should close part of the gap"),
        'mechanism': MECHANISM_HINT.get(key, 'none'),
        'expected_value': round(ev, 5),
    }


def _selftest():
    rng = np.random.default_rng(0)
    users, labels, scores, tags = [], [], [], []
    for u in range(200):
        cold = u < 60                       # 30% cold users, deliberately broken
        for i in range(8):
            y = int(rng.random() < 0.4)
            s = y * 2.0 + rng.normal()      # informative scores...
            if cold:
                s = rng.normal()            # ...except for cold users: noise
            users.append(f"u{u}"); labels.append(y); scores.append(float(s))
            tags.append({'hist': 'cold' if cold else 'warm',
                         'tab': str(u % 3)})
    overall, rep = slice_report(users, labels, scores, tags, min_users=20)
    worst = rep[0]
    assert worst[0] == 'hist=cold', f"expected hist=cold worst, got {worst[0]}"
    h = to_hypothesis(*worst[0:1], worst[1], overall, worst[2], worst[3]) \
        if False else to_hypothesis(worst[0], worst[1], overall, worst[2], worst[3])
    assert h['mechanism'] == 'temporal'
    print(f"selftest OK: found broken slice '{worst[0]}' "
          f"(primary {worst[1]:.3f} vs overall {overall:.3f}), "
          f"suggested mechanism '{h['mechanism']}'")


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        _selftest()
        sys.exit(0)
    # live mode: frozen model on validation, sliced
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'code'))
    import collections, csv
    from baseline import FM
    from sequences import load_sequenced, encode_rows, BASE, SEQ, DATA
    import belief_state as BS_import  # noqa
    sys.path.insert(0, os.path.join('..', 'agent'))
    import belief_state as BS

    print("building features + scoring frozen committee on validation ...")
    from staleness_ablation import build_features, RICH, _frozen_dir
    splits = build_features('continuous')
    enc, dim = encode_rows(splits, RICH)
    Xva, yva, uva = enc['valid']
    frozen = _frozen_dir()
    preds = []
    for seed in range(5):
        z = np.load(os.path.join(frozen, f'fm_seed{seed}.npz'))
        m = FM(dim, k=16, seed=seed)
        m.V, m.W, m.b = z['V'], z['W'], np.float32(z['b'])
        p = m.predict(Xva)
        preds.append((p - p.mean()) / p.std())
    scores = list(np.mean(preds, 0))

    tags = [{'hist': x['hist_n'], 'tab': x['tab'], 'dur': x['dur_bucket']}
            for x in splits['valid']]
    overall, rep = slice_report(uva, list(yva), scores, tags)
    print(f"\noverall validation primary {overall:.5f}; worst slices by EV:")
    for name, r, n_u, ev in rep[:8]:
        print(f"  {name:<14} primary {r:.5f}  users {n_u:>6,}  EV {ev:.5f}")

    worst = rep[0]
    h = to_hypothesis(worst[0], worst[1], overall, worst[2], worst[3])
    st = BS.load()
    BS.propose(st, h['id'], h['claim'], h['mechanism'], h['expected_value'])
    BS.save(st)
    print(f"\nwritten to belief state: {h['id']} (mechanism {h['mechanism']}, "
          f"EV {h['expected_value']})")
