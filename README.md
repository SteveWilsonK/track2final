# Autonomous ML Research Agent for Recommender Systems

TikTok TechJam 2026, Track 2.

Final result on KuaiRand-Pure: test primary **0.6116** (GAUC 0.6825, nDCG@5
0.5408). The official baseline is 0.5946, so our delta is **+0.0170**
(GAUC +0.0215, nDCG@5 +0.0126).

## Verify this submission in five minutes

All from `code/`, dataset in place (see Setup), in this order:

| Command | What it proves | Expected ending |
|---|---|---|
| `python3 score_frozen.py` | The headline score, from shipped weights, no training (~2 min) | `test ... primary 0.6116` |
| `python3 verify_claims.py` | Kit integrity vs the shipped official archive, split sizes, oracle 0.8645, seed noise (~1 min) | every check prints IDENTICAL / matching constants |
| `python3 replay_verdicts.py` | The selection trail, re-derived from validation alone (~1 s) | `matches the shipped checkpoint: YES` |
| `python3 staleness_ablation.py` | The serving-assumption sensitivity (~6 min) | daily-batch regime at `+0.0137` |

Full retraining from raw data: `python3 final_model.py` (~5 min, ends at
the same 0.6116).

## Project overview

The task: build an agent that runs the ML research loop on its own. Read the
problem, engineer features, train, evaluate, reflect, and iterate, until the
official convergence rule says stop.

Our solution has three layers.

1. The agent. A driver (`agent/driver.py`) loops fresh LLM sessions
   (Claude Code). Each session executes one research iteration under fixed
   standing instructions (`agent/ITERATION_PROMPT.md`): pick a hypothesis,
   implement it, run it, judge it on validation, log everything, commit.
2. The lab equipment. Every experiment goes through `code/harness.py`, which
   enforces 3 seeds minimum, a 0.002 significance gate, and logging of intent
   before training. Failed runs cannot disappear.
3. The model the agent produced. A five seed committee of Factorization
   Machines (k=16), trained with a listwise objective on causal sequence
   features. Simple on purpose. Full recipe in
   `final_output/frozen_model/config.json`.

The two discoveries that carried the score:

- Train on the question being graded. The baseline predicts "will this video
  be watched" but the metric grades ranking within a user. Switching to a
  listwise objective (softmax over one positive and four sampled negatives
  from the same user) gave +0.0028, verified with a capacity matched control.
- Show the model what the user just did. Seven features computed strictly
  from events before each impression: previous impression outcome, rolling
  watch rates, per author and per tag history, session gap. No feature ever
  sees its own row's label or anything later in time. This family carried
  the largest share of the final margin (+0.0038 at introduction, about
  +0.013 with its richer variants and the committee built on it).

Serving assumption, stated and measured. The history features update
continuously, which assumes a streaming feature store: a test row's
features include the outcomes of the same user's earlier test-window
impressions (each row still sees only strictly-prior events). We measured
what the gain looks like under weaker serving assumptions with the shipped
weights (`code/staleness_ablation.py`):

| Test-time feature regime | primary | vs baseline |
|---|---|---|
| Continuous updates (as submitted) | 0.6116 | +0.0170 |
| Daily batch refresh | 0.6083 | +0.0137 |
| Frozen at the test boundary (lower bound; train/serve skew) | 0.5943 | −0.0003 |

About 80 percent of the gain survives a realistic daily refresh cadence.

Three campaigns were run. Together they cover the autonomy spectrum:

| Campaign | Start state | Manual interventions | Converged at |
|---|---|---|---|
| Interactive research (29 runs; the culminating run is iterations 17 to 27) | official baseline | 3 loop-relevant, 0 iteration-level | 0.6116, the designated final submission |
| Verification run (3 iterations, overnight, unattended; a non-regression check, banked nothing) | frozen research state | 0 | 0.6116 survives re-challenge |
| Clean-room run (6 iterations, unattended, empty memory) | bare baseline | 0 | 0.59744, its own discovery, +0.0028 over baseline |

The designated final submission is 0.6116. The other two campaigns are
supplementary autonomy demonstrations, not the scored result.

The clean-room agent also refused to select two configurations whose test
scores looked better but whose validation did not justify them. It did that
with no human watching. The project logs five such refusals in total.

## Repository map

| Folder | Contents |
|---|---|
| `PROJECT-DESCRIPTION.md` | The written project description for Devpost |
| `code/` | The solution: agent harness, model, training, evaluation. Entry point `final_model.py` |
| `agent/` | The autonomy driver and the agent's standing instructions |
| `logs/` | Run and iteration logs, the interventions summary, the clean-room records, and every experiment script |
| `final_output/` | `submission.csv` (kit schema, validated), the frozen model weights, and the results and resource summary |

## Setup

Requirements: Python 3.10 or newer, and numpy. Nothing else. No GPU.

```bash
pip install numpy
# download the official dataset (184MB logs + 10MB features):
wget https://zenodo.org/records/10439422/files/KuaiRand-Pure.tar.gz
tar -xzvf KuaiRand-Pure.tar.gz -C code/
# so that code/KuaiRand-Pure/data/*.csv exists
```

## Steps to reproduce our results

All commands run from `code/`. Training is fully seeded, so results are
deterministic.

```bash
cd code

# 1. Official baseline, about 1 minute. Expect test primary near 0.595.
python3 baseline.py --model fm

# 2. Our final model, about 5 minutes. Retrains all five committee members
#    from raw data and prints: test primary 0.6116.
python3 final_model.py

# 3. Or score the shipped weights without retraining, about 2 minutes.
#    Finds final_output/frozen_model automatically. Prints the same 0.6116.
python3 score_frozen.py

# 4. Regenerate and validate the official submission file:
python3 submit.py --check --split test ../final_output/submission.csv
```

The scoring code (`evaluate.py`) and the data split (`data.py`) are byte
identical to the official starter kit, and you can check that yourself:
`python3 verify_claims.py` re-derives the kit hashes, the split sizes, the
oracle ceiling (0.8645) and user composition, the random floor, and the
seed-noise summary from the shipped artifacts. Every reported number comes
from the organizers' own scoring code on the organizers' own split.

A note on process: before submission we commissioned an adversarial review
of this repository and repaired what it found, including a real
inconsistency between our harness code and our selection claims. The
findings and corrections are stated plainly in `logs/PROCESS-AUDIT.md`.
The interactive phase's per-run commit history is archived in the public
research repository: https://github.com/SteveWilsonK/techjam-2026-workspace

To run the autonomous loop itself (needs the Claude Code CLI, authenticated):

```bash
python3 agent/driver.py    # from the repo root
```

## Limitations, and what we would improve with more time

- The evaluation is offline, on logged impressions. It measures ranking of
  what users were shown, not full catalog retrieval. This is the track's
  setup, not our choice, but it is worth naming.
- The information ceiling belongs to the dataset, not the model. Four model
  classes converged to the same score once features were equal. Without
  video content signal there was no path we found past roughly 0.612.
- Verdicts use 3 to 5 seeds. That is enough for our 0.002 gate against the
  measured noise floor (sigma about 0.0008), but finer effects are
  deliberately not claimed.
- The clean-room run shows the agent alone reaches +0.0028 in one strict
  run. The larger score needed a longer campaign with three strategic human
  decisions. We report that gap honestly rather than hiding it.
- Given more time: real sequence models with attention over the ordered
  history, a time-respecting use of the random exposure data for debiasing,
  and a hardened self-verification step inside each agent iteration.

## Team member contributions

The AI/human division of labor is documented throughout this repository:
the agent (Claude Code) proposed, implemented, and evaluated every
experiment; the enumerated human decisions are in `logs/INTERVENTIONS.md`.
Human team roles:

- [NAME], [role: e.g. project direction, research decisions, submission]
- [NAME], [role: e.g. repository management, verification runs]
- [NAME], [role: e.g. write-up review, video]
- [NAME], [role]
- [NAME], [role]

(Team: replace the placeholders above before submitting.)

## Acknowledgements and AI tooling disclosure

Dataset: KuaiRand (Gao et al., CIKM 2022), https://kuairand.com, used via
the official Track 2 starter kit. The research agent is powered by Claude
(Anthropic) through the Claude Code CLI. The agent wrote the experiment
code, ran the research loop, and authored the experimental commits. Humans
set direction and constraints; the details are in
`logs/INTERVENTIONS.md`.
