"""Pillar 3b: hypotheses from the model's actual mistakes, not brainstorming.

Slices the frozen model's validation predictions by row attributes the
pipeline already computes (user history depth, tab, video-duration bucket)
and scores each slice with the official evaluate() on the filtered subset.
The worst slice becomes a structured hypothesis written into the belief
state, with a mechanism suggestion attached.

Two headroom measures are reported per slice (v2, 31 Aug):

  EV  : (overall - slice-restricted score) x share of users. The original
        measure, kept for continuity. It is BIASED: a slice-restricted
        evaluation changes the user population and its degeneracy. A slice
        where most users have no positive label scores near zero under the
        official rule (nDCG counts 0.0, GAUC skips the user) no matter how
        good the model is, so EV credits it with headroom that cannot be
        collected. Measured on run 4's tab=0: 92% of that slice's users are
        all-negative inside it, and EV claimed 0.078 of headroom.
  EVo : oracle headroom. Re-score the FULL validation set with this slice's
        rows replaced by an oracle that knows their labels (positives above
        every other row, negatives below), and take the gain in the overall
        primary. Same user population, same metric, no degeneracy artifact:
        it is exactly the most the overall score could gain from ranking
        this slice perfectly. This is an upper bound and is what the queue
        is now ordered by.

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


def oracle_headroom(users, labels, scores, idx, overall=None):
    """Overall-primary gain from ranking the rows in `idx` with oracle
    knowledge of their labels, everything else untouched. Upper bound on
    what any intervention targeted at this slice can be worth."""
    if overall is None:
        overall = float(evaluate(users, labels, scores)['primary'])
    sc = np.asarray(scores, dtype=float)
    big = float(np.abs(sc).max()) + 1.0
    patched = sc.copy()
    for i in idx:
        # oracle placement, with the model's own score as a tie-break so the
        # patch never reorders rows the oracle is indifferent about
        patched[i] = (big if labels[i] else -big) + 1e-6 * sc[i]
    return float(evaluate(users, labels, list(patched))['primary']) - overall


def slice_report(users, labels, scores, tags, min_users=50):
    """tags: list of dicts per row, e.g. {'hist': 'cold', 'tab': '1'}.
    Returns [(slice_name, primary, n_users, ev, ev_oracle, degen_share)]
    sorted worst-first by ev_oracle (see the module docstring on why not ev).
    degen_share = fraction of the slice's users with no positive label
    inside the slice; a high value means the slice-restricted score (and
    therefore ev) is mostly metric degeneracy, not model error."""
    overall = float(evaluate(users, labels, scores)['primary'])
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
            ev = float(max(0.0, overall - r) * (n_u / total_users))
            evo = oracle_headroom(users, labels, scores, idx, overall)
            pos = {}
            for i in idx:
                u = users[i]
                pos[u] = pos.get(u, 0) + int(labels[i])
            degen = sum(1 for c in pos.values() if c == 0) / len(pos)
            out.append((f"{k}={v}", float(r), n_u, ev, float(evo),
                        float(degen)))
    out.sort(key=lambda x: -x[4])
    return overall, out


MECHANISM_HINT = {
    'hist': 'temporal',    # history-depth slices point at sequence starvation
    'tab': 'none',         # surface slices: no single mechanism implied
    'dur': 'capacity',     # duration slices: representation granularity
}


def to_hypothesis(slice_name, slice_primary, overall, n_users, ev,
                  ev_oracle=None, degen=None):
    key = slice_name.split('=')[0]
    extra = ''
    if ev_oracle is not None:
        extra = (f"; oracle headroom on the overall metric {ev_oracle:.4f}"
                 + (f" ({degen:.0%} of the slice's users are all-negative "
                    f"inside it, so the slice-restricted score understates "
                    f"the model)" if degen is not None else ''))
    return {
        'id': f"residual_{slice_name.replace('=', '_')}",
        'claim': (f"slice {slice_name} scores {slice_primary:.4f} vs overall "
                  f"{overall:.4f} across {n_users} users; a feature or prior "
                  f"targeted at this slice should close part of the gap"
                  + extra),
        'mechanism': MECHANISM_HINT.get(key, 'none'),
        'expected_value': round(ev_oracle if ev_oracle is not None else ev, 5),
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
    assert worst[4] > 0, "oracle headroom must be positive for a broken slice"
    h = to_hypothesis(worst[0], worst[1], overall, worst[2], worst[3],
                      worst[4], worst[5])
    assert h['mechanism'] == 'temporal'
    assert abs(h['expected_value'] - round(worst[4], 5)) < 1e-9, \
        "hypothesis EV must be the oracle headroom"

    # a slice that is merely degenerate (every user all-negative inside it)
    # must NOT outrank a slice the model actually gets wrong
    du, dl, ds, dt = [], [], [], []
    for u in range(120):
        for i in range(6):
            y = int(i == 0 and u < 60)          # 'thin' slice: never positive
            thin = (i >= 4)
            du.append(f"v{u}"); dl.append(0 if thin else y)
            ds.append(float(rng.normal() + (0 if thin else 2.0 * y)))
            dt.append({'grp': 'thin' if thin else 'main'})
    _, rep2 = slice_report(du, dl, ds, dt, min_users=20)
    thin_row = [r for r in rep2 if r[0] == 'grp=thin'][0]
    assert thin_row[5] == 1.0, "all-negative slice should be flagged degenerate"
    assert thin_row[4] == 0.0 or thin_row[4] < thin_row[3], \
        "oracle headroom must not credit a slice with nothing to gain"
    print(f"selftest OK: found broken slice '{worst[0]}' "
          f"(primary {worst[1]:.3f} vs overall {overall:.3f}, "
          f"EV {worst[3]:.4f}, oracle headroom {worst[4]:.4f}), "
          f"suggested mechanism '{h['mechanism']}'; degenerate slice "
          f"(EV {thin_row[3]:.4f}) correctly given oracle headroom "
          f"{thin_row[4]:.4f}")


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
    print(f"\noverall validation primary {overall:.5f}; worst slices "
          f"(ordered by oracle headroom EVo, the collectable one):")
    print(f"  {'slice':<14} {'primary':>9} {'users':>7} {'EV(old)':>9} "
          f"{'EVo':>8} {'all-neg users':>14}")
    for name, r, n_u, ev, evo, degen in rep[:8]:
        print(f"  {name:<14} {r:>9.5f} {n_u:>7,} {ev:>9.5f} {evo:>8.5f} "
              f"{degen:>13.0%}")

    import json
    with open(os.path.join('..', 'agent', 'residual_report.json'), 'w') as fh:
        json.dump({'overall': overall,
                   'slices': [{'slice': n, 'primary': r, 'users': nu,
                               'ev_old': ev, 'ev_oracle': evo,
                               'allneg_user_share': dg}
                              for n, r, nu, ev, evo, dg in rep]}, fh, indent=1)

    worst = rep[0]
    h = to_hypothesis(worst[0], worst[1], overall, worst[2], worst[3],
                      worst[4], worst[5])
    st = BS.load()
    BS.propose(st, h['id'], h['claim'], h['mechanism'], h['expected_value'])
    BS.save(st)
    print(f"\nwritten to belief state: {h['id']} (mechanism {h['mechanism']}, "
          f"EV {h['expected_value']})")
