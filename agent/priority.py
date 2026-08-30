"""Pillar 3c: cost-aware experiment ordering.

Every run in logs/LOG.jsonl already records wall_s; this module finally
uses it. It buckets historical runs into rough cost categories, takes each
category's median wall time as the cost estimate, and ranks the belief
state's open hypotheses by expected value per second of compute, with a
bonus for mechanisms that have never been control-tested (zero
falsification evidence is worth more than a fourth confirmation).

Usage:
    python3 priority.py --recompute     # refresh cost estimates from the log
    python3 priority.py                 # print the ranked open queue
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, '..', 'logs', 'LOG.jsonl')
COSTS = os.path.join(HERE, 'cost_estimates.json')

BUCKETS = (
    ('committee', re.compile(r'committee|ensemble', re.I)),
    ('mlp', re.compile(r'mlp|interest|attention', re.I)),
    ('single_fm', re.compile(r'.', re.I)),          # fallback bucket
)


def recompute():
    import statistics
    times = {name: [] for name, _ in BUCKETS}
    with open(LOG) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get('phase') != 'result' or 'wall_s' not in r:
                continue
            for name, pat in BUCKETS:
                if pat.search(r.get('name', '')):
                    times[name].append(r['wall_s'])
                    break
    est = {name: (statistics.median(ts) if ts else 300.0)
           for name, ts in times.items()}
    with open(COSTS, 'w') as fh:
        json.dump(est, fh, indent=1)
    for name, ts in times.items():
        print(f"{name:<12} n={len(ts):>3}  median {est[name]:.0f}s")
    return est


def cost_for(claim):
    est = json.load(open(COSTS)) if os.path.exists(COSTS) else {}
    for name, pat in BUCKETS:
        if pat.search(claim):
            return est.get(name, 300.0)
    return est.get('single_fm', 300.0)


def ranked_queue():
    import belief_state as BS
    st = BS.load()
    opens = [h for h in st['hypotheses']
             if h['status'] in ('proposed', 'testing')]
    rows = []
    for h in opens:
        ev = h['expected_value'] if h['expected_value'] is not None else 1e-3
        cost = h['cost_estimate_s'] or cost_for(h['claim'])
        bonus = 1.2 if (h['mechanism'] != 'none' and h['control'] is None) else 1.0
        rows.append((ev / cost * bonus, h['id'], ev, cost, h['mechanism']))
    rows.sort(reverse=True)
    return rows


if __name__ == '__main__':
    if '--recompute' in sys.argv:
        recompute()
    q = ranked_queue()
    if not q:
        print("queue empty")
    for score, hid, ev, cost, mech in q:
        print(f"{score:.2e}  {hid:<40} EV {ev}  cost {cost:.0f}s  [{mech}]")
