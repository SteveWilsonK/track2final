"""Pillar 3b: hypotheses from the model's actual mistakes, not brainstorming.

Slices the frozen model's validation predictions by row attributes the
pipeline already computes (user history depth, tab, video-duration bucket)
and scores each slice with the official evaluate() on the filtered subset.
The worst slice becomes a structured hypothesis written into the belief
state, with a mechanism suggestion attached.

Three headroom measures are reported per slice (v3, 31 Aug):

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
        this slice perfectly. This is an upper bound. It was what the queue
        was ordered by until campaign 6 iteration 3.
  EVx : excess oracle headroom (v3, 31 Aug, campaign 6 iteration 3). EVo
        is an upper bound, and every slice has one roughly in proportion to
        its size: perfectly ranking any large chunk of the validation set
        helps, whether or not the model is bad there. So EVo ranks by SIZE,
        and the loop paid for that twice. Iteration 2/3 took hist=31-100 on
        EVo 0.13222 — a slice scoring 0.62154 against 0.62059 overall,
        i.e. ABOVE the model's average, with EV(old) of exactly 0.0 — and
        refuted it; the queue's next pick, hist=11-30, is the same shape
        (EV(old) 0.00153) while dur=8, where the model scores 0.518 against
        0.621, sat at rank 4. EVx subtracts a matched null: the oracle
        headroom of a slice holding the SAME number of each user's rows,
        drawn at random from that user's rows (see
        matched_null_headroom). What survives is headroom attributable to
        the model being
        differentially wrong inside this slice rather than to its size
        and user footprint. It is signed: a slice the model handles
        UNUSUALLY WELL scores negative, which EVo cannot express. A slice
        the model handles at its average scores
        EVx ~ 0 no matter how large it is. The queue is now ordered by EVx;
        EV(old) and EVo are still computed and printed for continuity.

Note on units: hypotheses written before iteration 3 carry EVo in their
`expected_value` field; from iteration 3 the field carries EVx. All the
pre-iteration-3 records are resolved, so next_open() never compares across
the two conventions, but the numbers are not interchangeable.

Uses evaluate.py completely unmodified — subsets in, scores out.

Run from code/ (needs dataset + frozen weights):
    python3 ../agent/residual_analysis.py
Self-test (synthetic, no dataset):
    python3 residual_analysis.py --selftest
"""
import collections, os, sys
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


def matched_null_headroom(users, labels, scores, idx, overall, seeds=2):
    """Oracle headroom of a NULL slice matched to `idx` in shape.

    The slice takes c_u of user u's rows. The null takes c_u of user u's
    rows too, chosen uniformly at random from that user's rows. Which users
    the slice touches and how many of each user's rows it takes — the two
    things a per-user metric's headroom is mechanically driven by — are
    preserved exactly; WHICH of the user's rows are in it is destroyed.
    The construction is exactly feasible, so the null is always size-matched
    (unlike dealing the counts out to other users, which the real data's
    skewed rows-per-user distribution makes infeasible: the cap binds on
    most slices and undersizes the null precisely where the slice is large).

    Same shape as the falsification controls (controls.time_shuffle):
    preserve the marginals, destroy the attachment, read off what the
    attachment was worth.

    Blind spot, reported rather than hidden: for a user whose rows lie
    ENTIRELY inside the slice there is nothing to reshuffle, so the null
    reproduces the slice and contributes no excess. Returns (mean headroom,
    locked_share) where locked_share is the fraction of the slice's rows
    belonging to such users; at a high locked_share, EVx is biased toward
    zero and should not be trusted. On this dataset every slicing attribute
    (history depth, tab, duration bucket) varies within a user's own
    validation rows, so locked_share stays small.
    """
    by_user = collections.defaultdict(list)
    for i, u in enumerate(users):
        by_user[u].append(i)
    want = collections.Counter(users[i] for i in idx)
    locked = sum(c for u, c in want.items() if c == len(by_user[u]))
    vals = []
    for s in range(seeds):
        rng = np.random.default_rng(1000 + s)
        null = []
        for u, c in want.items():
            rows = by_user[u]
            null.extend(int(i) for i in
                        rng.choice(rows, size=c, replace=False))
        vals.append(oracle_headroom(users, labels, scores, null, overall))
    return float(np.mean(vals)), float(locked / max(1, len(idx)))


def slice_report(users, labels, scores, tags, min_users=50, null_seeds=2):
    """tags: list of dicts per row, e.g. {'hist': 'cold', 'tab': '1'}.
    Returns [(slice_name, primary, n_users, ev, ev_oracle, degen_share,
    ev_excess)] sorted worst-first by ev_excess (see the module docstring on
    why not ev and no longer ev_oracle).
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
            null, locked = matched_null_headroom(
                users, labels, scores, idx, overall, seeds=null_seeds)
            if locked > 0.25:
                print(f"  [warn] {k}={v}: {locked:.0%} of the slice's rows "
                      f"belong to users who are entirely inside it, so the "
                      f"null cannot reshuffle them and this EVx is biased "
                      f"toward zero")
            pos = {}
            for i in idx:
                u = users[i]
                pos[u] = pos.get(u, 0) + int(labels[i])
            degen = sum(1 for c in pos.values() if c == 0) / len(pos)
            out.append((f"{k}={v}", float(r), n_u, ev, float(evo),
                        float(degen), float(evo - null)))
    out.sort(key=lambda x: -x[6])
    return overall, out


RESOLVED = ('confirmed', 'refuted', 'refuted_by_control')


def first_unresolved(rep, state):
    """The worst slice (by oracle headroom) whose hypothesis is not already
    resolved in the belief state.

    Added campaign 6, iteration 1. The analyzer previously always proposed
    `rep[0]`, and `propose()` dedups by id without reviving a record, so
    once the worst slice had been tried and refuted the analyzer kept
    re-proposing a refuted hypothesis, `next_open()` returned nothing, and
    the loop stalled with an empty queue. Walking down the ranking instead
    keeps the loop live and preserves the ordering rule: the next-best
    *unresolved* slice, never a slice the loop has already settled.
    Returns None when every slice above `min_users` is resolved.
    """
    resolved = {h['id'] for h in state.get('hypotheses', [])
                if h.get('status') in RESOLVED}
    for row in rep:
        if f"residual_{row[0].replace('=', '_')}" not in resolved:
            return row
    return None


MECHANISM_HINT = {
    'hist': 'temporal',    # history-depth slices point at sequence starvation
    'tab': 'none',         # surface slices: no single mechanism implied
    'dur': 'capacity',     # duration slices: representation granularity
}


def to_hypothesis(slice_name, slice_primary, overall, n_users, ev,
                  ev_oracle=None, degen=None, ev_excess=None):
    key = slice_name.split('=')[0]
    extra = ''
    if ev_oracle is not None:
        extra = (f"; oracle headroom on the overall metric {ev_oracle:.4f}"
                 + (f", of which {ev_excess:.4f} is EXCESS over a matched "
                    f"null slice (same users, same per-user row counts, rows "
                    f"drawn at random) and therefore attributable to the "
                    f"model rather than to slice size"
                    if ev_excess is not None else '')
                 + (f"; {degen:.0%} of the slice's users are all-negative "
                    f"inside it, so the slice-restricted score understates "
                    f"the model" if degen is not None else ''))
    return {
        'id': f"residual_{slice_name.replace('=', '_')}",
        'claim': (f"slice {slice_name} scores {slice_primary:.4f} vs overall "
                  f"{overall:.4f} across {n_users} users; a feature or prior "
                  f"targeted at this slice should close part of the gap"
                  + extra),
        'mechanism': MECHANISM_HINT.get(key, 'none'),
        'expected_value': round(
            ev_excess if ev_excess is not None
            else ev_oracle if ev_oracle is not None else ev, 5),
    }


def _selftest():
    # The fixture reproduces, in miniature, the defect that cost campaign 6
    # two iterations. Every user contributes rows to every slice, so each
    # slice is a WITHIN-user subset -- the regime the real validation set is
    # in. `hist=cold` is SMALL (2 of each user's 12 rows) and genuinely
    # broken: the model scores those rows at noise. The `tab` slices and
    # `hist=warm` are LARGER and perfectly normal. Oracle headroom therefore
    # ranks the broken slice LAST and a healthy slice first; EVx must invert
    # that.
    rng = np.random.default_rng(0)
    users, labels, scores, tags = [], [], [], []
    for u in range(200):
        for i in range(12):
            cold = i < 2                    # 2 of EVERY user's 12 rows
            y = int(rng.random() < 0.4)
            s = y * 2.0 + rng.normal()      # informative scores...
            if cold:
                s = rng.normal()            # ...except on cold rows: noise
            users.append(f"u{u}"); labels.append(y); scores.append(float(s))
            tags.append({'hist': 'cold' if cold else 'warm',
                         'tab': str(i % 2)})
    # 8 null draws here: the fixture is small, so a 2-draw null is visibly
    # noisy on it (the live report has 22k users and does not need this many).
    overall, rep = slice_report(users, labels, scores, tags, min_users=20,
                                null_seeds=8)
    worst = rep[0]
    assert worst[0] == 'hist=cold', f"expected hist=cold worst, got {worst[0]}"
    assert worst[4] > 0, "oracle headroom must be positive for a broken slice"
    h = to_hypothesis(worst[0], worst[1], overall, worst[2], worst[3],
                      worst[4], worst[5], worst[6])
    assert h['mechanism'] == 'temporal'
    assert abs(h['expected_value'] - round(worst[6], 5)) < 1e-9, \
        "hypothesis EV must be the EXCESS oracle headroom (v3)"

    # v3, the regression test for the ranking defect. EVo must get this
    # fixture WRONG and EVx must get it right; if EVo ever ranks it correctly
    # the fixture has stopped exercising the bug and needs rebuilding.
    by = {r[0]: r for r in rep}
    evo_rank = [r[0] for r in sorted(rep, key=lambda x: -x[4])]
    assert evo_rank[0] != 'hist=cold' and evo_rank[-1] == 'hist=cold', \
        f"fixture no longer exercises the size bias: EVo order {evo_rank}"
    assert rep[0][0] == 'hist=cold', \
        f"EVx must rank the broken slice first, got {[r[0] for r in rep]}"
    # the healthy slices are LARGER than the broken one and must still score
    # near zero: their headroom is size, and the null accounts for all of it
    for name in ('tab=0', 'tab=1', 'hist=warm'):
        assert by[name][4] > by['hist=cold'][4], \
            f"{name} should out-size hist=cold on EVo"
        assert abs(by[name][6]) < 0.25 * by['hist=cold'][6], \
            f"{name} is a size artifact: its EVx must be near zero"
    # EVx is signed: a slice the model handles BETTER than an arbitrary
    # same-shaped one scores below zero, which EVo can never express.
    assert by['hist=warm'][6] < 0 < by['hist=warm'][4], \
        "a slice the model is unusually good on must have negative EVx"
    # and the null must actually be size-matched on this fixture
    _, locked = matched_null_headroom(
        users, labels, scores,
        [i for i, t in enumerate(tags) if t['hist'] == 'cold'], overall)
    assert locked == 0.0, \
        f"fixture slices must vary within user for EVx to be meaningful "\
        f"(locked share {locked})"

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
    # the analyzer must walk PAST a slice the belief state has settled,
    # or the loop stalls once its worst slice is refuted (campaign 6 fix)
    st = {'hypotheses': [{'id': 'residual_hist_cold', 'status': 'refuted'}]}
    nxt = first_unresolved(rep, st)
    assert nxt is not None and nxt[0] != 'hist=cold', \
        "a resolved slice must not be re-proposed"
    assert first_unresolved(rep, {'hypotheses': []})[0] == 'hist=cold', \
        "with an empty belief state the worst slice is still the pick"
    allres = {'hypotheses': [{'id': f"residual_{r[0].replace('=', '_')}",
                              'status': 'confirmed'} for r in rep]}
    assert first_unresolved(rep, allres) is None, \
        "fully resolved report must yield no proposal"

    print(f"selftest OK: found broken slice '{worst[0]}' "
          f"(primary {worst[1]:.3f} vs overall {overall:.3f}, "
          f"EV {worst[3]:.4f}, oracle headroom {worst[4]:.4f} -- which "
          f"ranks it LAST of {len(rep)} -- of which excess over the matched "
          f"null {worst[6]:.4f}, ranking it first; the larger healthy slices "
          f"keep at most "
          f"{max(abs(by[n][6]) for n in by if n != 'hist=cold') / worst[6]:.0%}"
          f" of that), "
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
    from staleness_ablation import build_features, RICH
    from tab_surface import add_tab_features
    # score the CURRENT champion (R33c: RICH + tab_n, 31 Aug promotion);
    # the pre-promotion analyses used R24b via staleness_ablation._frozen_dir
    splits = add_tab_features(build_features('continuous'))
    enc, dim = encode_rows(splits, RICH + ['tab_n'])
    Xva, yva, uva = enc['valid']
    frozen = None
    for c in ('frozen_model', os.path.join('..', 'final_output',
                                           'frozen_model')):
        if os.path.exists(os.path.join(c, 'fm_seed0.npz')):
            frozen = c
            break
    if frozen is None:
        raise FileNotFoundError('frozen_model (current champion) not found')
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
    overall, rep = slice_report(uva, list(yva), scores, tags,
                                null_seeds=3)
    print(f"\noverall validation primary {overall:.5f}; worst slices "
          f"(ordered by EVx, the headroom the MODEL is responsible for):")
    print(f"  {'slice':<14} {'primary':>9} {'users':>7} {'EV(old)':>9} "
          f"{'EVo':>8} {'EVx':>8} {'all-neg users':>14}")
    for name, r, n_u, ev, evo, degen, evx in rep[:8]:
        print(f"  {name:<14} {r:>9.5f} {n_u:>7,} {ev:>9.5f} {evo:>8.5f} "
              f"{evx:>8.5f} {degen:>13.0%}")

    import json
    with open(os.path.join('..', 'agent', 'residual_report.json'), 'w') as fh:
        json.dump({'overall': overall,
                   'slices': [{'slice': n, 'primary': r, 'users': nu,
                               'ev_old': ev, 'ev_oracle': evo,
                               'ev_excess': evx,
                               'allneg_user_share': dg}
                              for n, r, nu, ev, evo, dg, evx in rep]},
                  fh, indent=1)

    st = BS.load()
    worst = first_unresolved(rep, st)
    if worst is None:
        print("\nevery slice above the user floor is already resolved in the "
              "belief state; nothing new to propose.")
        raise SystemExit(0)
    if worst is not rep[0]:
        print(f"\n(top slice {rep[0][0]} is already resolved; taking the "
              f"next unresolved one)")
    h = to_hypothesis(worst[0], worst[1], overall, worst[2], worst[3],
                      worst[4], worst[5], worst[6])
    BS.propose(st, h['id'], h['claim'], h['mechanism'], h['expected_value'])
    BS.save(st)
    print(f"\nwritten to belief state: {h['id']} (mechanism {h['mechanism']}, "
          f"EV {h['expected_value']})")
