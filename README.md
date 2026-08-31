# Autonomous ML Research Agent for Recommender Systems

TikTok TechJam 2026, Track 2.

Final result on KuaiRand-Pure: test primary **0.6143** (GAUC 0.6857, nDCG@5
0.5429). The official baseline is 0.5946, so our delta is **+0.0197**
(GAUC +0.0247, nDCG@5 +0.0147). The final +0.0027 of that margin is the
promoted discovery of the autonomous research loop itself: tab_n, a
partitioned-familiarity feature (a per-surface impression count; per our
own R37 control, roughly half its gain needs the true surface and half
comes from the counting structure) derived from the champion's own
residuals (campaign 5 below; the pre-promotion champion scored 0.6116).

## Verify this submission in five minutes

One prerequisite first: the dataset (~200 MB) must be downloaded and
extracted per Setup below; none of these commands run without it. Then,
all from `code/`, in this order:

| Command | What it proves | Expected ending |
|---|---|---|
| `python3 score_frozen.py` | The headline score, from shipped weights, no training (~2 min) | `test ... primary 0.6143` |
| `python3 verify_claims.py` | Kit integrity vs the shipped official archive, split sizes, oracle 0.8645, seed noise (~1 min) | every check prints IDENTICAL / matching constants |
| `python3 replay_verdicts.py` | The selection trail, re-derived from validation alone (~1 s) | `matches the shipped checkpoint: YES` |
| `python3 staleness_ablation.py` | The serving-assumption sensitivity, measured on the pre-promotion champion (~6 min) | daily-batch regime at `+0.0137` |

Full retraining from raw data: `python3 final_model.py` (~5 min, ends at
the same 0.6143).

## Project overview

The task: build an agent that runs the ML research loop on its own. Read the
problem, engineer features, train, evaluate, reflect, and iterate, until the
official convergence rule says stop.

Our solution has three layers.

1. The agent. A driver (`agent/driver.py`) loops fresh LLM sessions
   (Claude Code). Each session executes one research iteration under fixed
   standing instructions (`agent/ITERATION_PROMPT.md`): observe the
   champion's residuals, take the highest expected-value-per-second
   hypothesis from a structured belief state, implement and run it, and
   falsify the mechanism before banking. Four modules make that judgment
   inspectable rather than implicit: `agent/residual_analysis.py`
   (hypotheses from the model's own worst validation slices),
   `agent/belief_state.py` (persistent structured memory whose promote()
   refuses, as code, to confirm a mechanism-tagged claim without a passing
   falsification control), `agent/priority.py` (expected value per second,
   costed from the log's real wall times), and `code/controls.py` (the
   falsification engine that synthesizes the placebo test from a claim's
   mechanism tag).
2. The lab equipment. Every experiment goes through `code/harness.py`, which
   enforces 3 seeds minimum, a 0.002 significance gate, and logging of intent
   before training. Failed runs cannot disappear.
3. The model the agent produced. A five seed committee of Factorization
   Machines (k=16), trained with a listwise objective on causal sequence
   features plus the loop's own promoted discovery (tab_n). Simple on
   purpose. Full recipe in `final_output/frozen_model/config.json`.

The three discoveries that carried the score:

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
- Surface familiarity, found by the loop itself. The autonomous v2
  iteration analyzed the champion's residuals, found its worst slice
  (tab=0), hypothesized that stream-wide history misleads on the minority
  surface, and proposed tab_n: the user's prior impression count on the
  row's surface, label-free and log-bucketed. The time-shuffle placebo
  passed (the gain collapses entirely when the count is detached from its
  impression), and the pre-committed 5-seed committee
  check promoted it: validation 0.62059 over the incumbent's 0.61906,
  test 0.6143 over 0.6116. The one feature in the submission a human
  did not think of. A sharper control run after promotion, at review
  request (R37: the identical count computed over surfaces scrambled
  within each user), then split the mechanism story: roughly half the
  gain survives scrambling (a single 3-seed measurement with both halves
  near the noise floor, so "roughly half" is the supported precision) —
  part of the effect needs the true surface, part comes from the
  partitioned counting structure itself. We revised the claim accordingly — partitioned familiarity, not
  pure surface familiarity — and the revision is in the belief state and
  the audit. The promotion is unaffected: it was earned on validation,
  not on the mechanism story.

Mechanism, proven rather than asserted. Our central causal claim was
that these features work because of when things happened, not who the user
is. The falsification test (synthesized by `code/controls.py` from the
claim's temporal tag: permute which impression each feature vector is
attached to, within each user and split, preserving every per-user
marginal) settles it: **95 percent of the sequence gain collapses when the
time alignment is broken, and the shuffled features perform identically to
random noise** (`code/mechanism_test.py`, four retrained committees).
Timing is the mechanism; identity fingerprinting contributes nothing.

A second finding: the exposure-bias frontier. Re-weighting the listwise
objective's negatives by inverse training-window exposure and scoring each
variant on both test sets shows a **steeply diminishing exchange rate: the
first debiasing step (lambda 0 to 0.5) trades one point of biased-log score
for about two points of unbiased-exposure score, but the next step trades
at only about 0.3:1** (`code/debias_frontier.py`).
Much of any model's standard-log performance on this dataset is exposure
fitting, and the measured trade-off curve is the price of correcting it.
The submission stays at lambda 0 because the competition scores the logged
exposure test.

Serving assumption, stated and measured. The history features update
continuously, which assumes a streaming feature store: a test row's
features include the outcomes of the same user's earlier test-window
impressions (each row still sees only strictly-prior events). One
distinction worth stating: the promoted tab_n counts prior IMPRESSIONS,
not outcomes — it is label-free, so while it shares the streaming-state
assumption (the count advances during the test window), no part of it
depends on any test-window label. The deployability analyses below —
this staleness curve, the unbiased-exposure evaluation, the mechanism
decomposition, and the bias frontier — were measured on the
pre-promotion champion, the 0.6116 seven-feature recipe; its weights
ship at `final_output/frozen_model_r24b/` so every number remains
reproducible, and the promoted model adds one label-free count on top of
that audited recipe (`code/staleness_ablation.py`):

| Test-time feature regime | primary | vs baseline |
|---|---|---|
| Continuous updates (the pre-promotion champion) | 0.6116 | +0.0170 |
| Daily batch refresh, shipped weights unmodified | 0.6083 | +0.0137 |
| Daily batch refresh, committee retrained for the regime (`daily_retrain.py`) | 0.6106 | +0.0160 |
| Frozen at the test boundary, shipped weights unmodified (train/serve skew) | 0.5943 | −0.0003 |
| Frozen at the test boundary, committee retrained for the regime (`protocolB_retrain.py`, 31 Aug) | 0.5979 | +0.0033 |

94 percent of the gain survives a daily refresh cadence when the model is
trained for it; 80 percent survives even without retraining. In the
strictest regime — label-derived history frozen before the test window, so
no test-row feature can depend on any test-window outcome — the retrained
committee still beats the official baseline by +0.0033, which is the
package's fully-conservative number under any reading of test isolation.

Separately, on the dataset's randomly-exposed impressions (897,721
test-window rows with no recommender selection bias; evaluation only, per
our legality analysis; `unbiased_eval.py`), the advantage persists: ours
0.3777 vs 0.3707 for a seed-matched 5-seed baseline committee, a delta of
+0.0070 with both metric components improving (+0.0095 against the
single-seed baseline). Absolute numbers are compressed in this regime
(37.2 percent of its users have no positive at all; positive rate 8.6
percent), so the fair reading is range-normalized: the attainable range
here runs 0.3149 (random floor) to 0.8138 (oracle), the baseline captures
11.2 percent of it, ours 12.6 percent, a relative gain of +12.5 percent
over the baseline's captured headroom, comparable to the +14 percent on
the standard log. The gain is not an artifact of ranking what the previous
system already favored. One scope note: features on these rows use the
same continuous-update regime as the headline, so this analysis removes
exposure bias; it does not additionally vary feature freshness.

Six campaigns were run. Together they cover the autonomy spectrum:

| Campaign | Start state | Manual interventions | Converged at |
|---|---|---|---|
| Interactive research (29 runs; the culminating run is iterations 17 to 27) | official baseline | 3 loop-relevant, 0 iteration-level | 0.6116, the champion until 31 Aug |
| Verification run (3 iterations, overnight, unattended; a non-regression check, banked nothing) | frozen research state | 0 | 0.6116 survives re-challenge |
| Clean-room run (6 iterations, unattended, empty memory) | bare baseline | 0 | 0.59744, its own discovery, +0.0028 over baseline |
| v2-loop iteration (31 Aug, unattended; ended by a driver fault after one full iteration) | frozen state + belief state | 0 during the iteration | produced the tab_n hypothesis, its passing placebo, and a sub-margin 3-seed decline |
| Campaign 5, completion run (4 iterations, operator-driven) | banked state | operator-driven by design | **0.6143, the designated final submission** (banked the loop's tab_n at the pre-committed committee check, then 3 sub-epsilon iterations) |
| Campaign 6 (31 Aug evening, unattended; 3 iterations, converged by the official rule in 49 minutes) | banked state + belief state | 0 | nothing banked, champion held: refuted its own top two hypotheses (session depth R38, partition-count generalisation R39), claimed the negatives, and repaired its own hypothesis queue — it discovered the expected-value ranking favoured slice SIZE, built a matched-null corrected measure (EVx) with a regression self-test, and re-ranked the queue |

The designated final submission is 0.6143: the interactive campaign's
recipe plus the autonomous loop's own promoted discovery. The verification,
clean-room, v2-loop and campaign-6 runs are autonomy demonstrations, not the
scored result.

The clean-room agent also refused to select two configurations whose test
scores looked better but whose validation did not justify them. It did that
with no human watching. The project logs six validation-grounded refusals
in total (the sixth, the v2 loop's 3-seed decline of tab_n, was superseded
when the pre-committed 5-seed committee check cleared the promotion bar).

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
#    from raw data and prints: test primary 0.6143.
python3 final_model.py

# 3. Or score the shipped weights without retraining, about 2 minutes.
#    Finds final_output/frozen_model automatically. Prints the same 0.6143.
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
