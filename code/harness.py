"""Research-agent harness: the single entry point for running an experiment.

Every hypothesis goes through run_experiment(), which mechanically enforces
the lab discipline — no iteration can skip it:

  1. multi-seed training (default 3) with mean/std,
  2. significance gating against the frozen baseline AND the current best
     (gate = 0.002, ~2.5x measured seed noise sigma ~= 0.0008),
  3. self-documenting append to experiments/LOG.jsonl (machine-readable) —
     hypothesis, rationale, config, per-seed results, verdict, wall time —
     BEFORE and AFTER the run, so a killed run still leaves its intent.

The test split is evaluated and recorded but the VERDICT, the banked-best
tracking, and the convergence signal are all decided on VALIDATION; test
numbers are reported for the log's honesty and audited at final scoring.
(Process note: before 30 Aug the printed verdict label was derived from the
test delta while banking decisions were made on validation by the operator
and documented in RESULTS.md; see logs/PROCESS-AUDIT.md. This file now
computes everything selection-relevant from validation.) Training code can
never see valid/test labels (only evaluate() reads them).
"""
import json, os, time
import numpy as np

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'logs', 'LOG.jsonl')
BASELINE = 0.5950          # reproduced FM baseline, TEST primary (reporting only)
BASELINE_VALID = 0.6014    # reproduced FM baseline, VALIDATION primary (selection)
GATE = 0.002               # significance bar; seed noise sigma ~= 0.0008


def _append(rec):
    with open(LOG, 'a') as fh:
        fh.write(json.dumps(rec) + '\n')


def current_best():
    """Best banked VALIDATION primary recorded so far (falls back to the
    validation baseline). Selection and convergence run on validation; test
    is recorded for audit and never ranks candidates."""
    best = BASELINE_VALID
    if os.path.exists(LOG):
        with open(LOG) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get('phase') == 'result' and r.get('verdict') == 'WIN' \
                        and r.get('valid_mean') is not None:
                    best = max(best, r['valid_mean'])
    return best


def run_experiment(name, hypothesis, rationale, train_fn, seeds=3, config=None):
    """train_fn(seed) -> {'valid': {...}, 'test': {...}} from evaluate().

    Returns the result record. Appends intent before training and the result
    after, so an interrupted run still documents what it was trying.
    """
    t0 = time.time()
    _append({'phase': 'intent', 'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
             'name': name, 'hypothesis': hypothesis, 'rationale': rationale,
             'config': config or {}, 'seeds': seeds})
    vs, ts = [], []
    comps = {'valid_GAUC': [], 'valid_nDCG@5': [], 'test_GAUC': [], 'test_nDCG@5': []}
    for s in range(seeds):
        r = train_fn(s)
        vs.append(r['valid']['primary']); ts.append(r['test']['primary'])
        comps['valid_GAUC'].append(r['valid'].get('GAUC'))
        comps['valid_nDCG@5'].append(r['valid'].get('nDCG@5'))
        comps['test_GAUC'].append(r['test'].get('GAUC'))
        comps['test_nDCG@5'].append(r['test'].get('nDCG@5'))
    vm, tm, tsd = float(np.mean(vs)), float(np.mean(ts)), float(np.std(ts))
    best = current_best()
    d_base = vm - BASELINE_VALID          # VALIDATION delta decides the verdict
    d_best = vm - best
    d_base_test = tm - BASELINE           # test delta, recorded for audit only
    if d_base > GATE and vm >= best - 1e-9:
        verdict = 'WIN'
    elif d_base > GATE:
        verdict = 'SIGNIFICANT_BUT_NOT_BEST'
    elif d_base < -GATE:
        verdict = 'WORSE'
    else:
        verdict = 'NOISE'
    def _m(key):
        xs = [x for x in comps[key] if x is not None]
        return round(float(np.mean(xs)), 5) if xs else None

    rec = {'phase': 'result', 'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
           'name': name, 'valid_mean': round(float(vm), 5),
           'test_mean': round(float(tm), 5), 'test_std': round(float(tsd), 5),
           'test_per_seed': [round(float(x), 5) for x in ts],
           'valid_GAUC': _m('valid_GAUC'), 'valid_nDCG@5': _m('valid_nDCG@5'),
           'test_GAUC': _m('test_GAUC'), 'test_nDCG@5': _m('test_nDCG@5'),
           'd_baseline_valid': round(float(d_base), 5),
           'd_baseline_test': round(float(d_base_test), 5),
           'd_best_valid': round(float(d_best), 5),
           'verdict': verdict, 'wall_s': round(time.time() - t0, 1)}
    _append(rec)
    BANKED_VALID = 0.61906  # banked best on VALIDATION (R24b committee)
    BANKED = 0.6116         # its test primary, for reporting only
    mark = '✅ BETTER than banked' if vm > BANKED_VALID else '❌ not better'
    print(f"[{verdict}] {name}: valid {vm:.4f} (vs banked {vm - BANKED_VALID:+.4f} {mark}) "
          f"| test {tm:.4f} ± {tsd:.4f} recorded | {rec['wall_s']}s)")
    return rec
