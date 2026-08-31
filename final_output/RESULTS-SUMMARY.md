# Final Submission and Results Summary

## Final model output

- `submission.csv`: the frozen model's score for every test split row, in
  the starter kit schema (row_id, user_id, video_id, score). Validated with
  the kit's own checker (170,588 rows, aligned) and by re-evaluating the
  written scores in the kit's row order (`code/make_final_submission.py`
  prints primary 0.61430).
- `frozen_model/`: the model checkpoint (R33c). Five seed weight files plus
  config.json with the full recipe. Regenerate everything from raw data
  with `python3 final_model.py` in `code/` (about 5 minutes, CPU only).
- `frozen_model_r24b/`: the pre-promotion champion (0.6116), kept so every
  analysis measured on it stays reproducible.

## Results table (required benchmark: KuaiRand-Pure)

The scored submission is the validation-best checkpoint at convergence,
evaluated once on the test split.

| Metric | Official baseline (test) | Ours (validation) | Ours (test) | Delta vs baseline (test) |
|---|---|---|---|---|
| GAUC | 0.6610 | 0.6948 | 0.6857 | +0.0247 |
| nDCG@5 | 0.5282 | 0.5464 | 0.5429 | +0.0147 |
| primary | 0.5946 | 0.6206 | 0.6143 | +0.0197 |

Score under the official formula (mean over metrics of the absolute delta):
(0.0247 + 0.0147) / 2 = **+0.0197**.

This is the 31 Aug promoted checkpoint (R33c: the seven-feature recipe
plus the autonomous loop's tab_n discovery, banked at the pre-committed
committee check and converged in campaign 5). The pre-promotion champion
(R24b, 0.6116 test) is archived at `frozen_model_r24b/`; the post-freeze
analyses below that predate the promotion were measured on it and are
labeled accordingly.

Context: the attainable range runs from random scoring (about 0.475; the
official statement quotes 0.4753, our seeded examples in verify_claims.py
average 0.4747) to the
oracle ceiling at 0.8645. The baseline captures about 31 percent of that
range. Our submission captures about 36 percent. We derived the ceiling
arithmetic ourselves (27.1 percent of test users have no positive label,
9.2 percent are all positive) before reading the organizers' numbers, and
they match exactly.

Bonus benchmarks (KuaiRand-1k, KuaiRand-27k): not attempted.

## Resource usage

Measured, not estimated. Token counts are summed from the recorded usage
fields of every unattended agent session transcript. Wall-clock comes from
driver event timestamps. No GPU was used at any point (GPU-hours: 0). All
training is single machine laptop CPU, numpy only.

| Run | Iterations (cap 50) | Wall-clock (ceiling 6h) | LLM tokens in+out | Including cache reads and writes |
|---|---|---|---|---|
| Verification run (unattended, overnight) | 3 | 52 min 32 s | 149,658 | 6,188,547 |
| Clean-room run (unattended, from bare baseline) | 6 | 1 h 47 min 41 s | 325,476 | 17,978,927 |
| Interactive culminating run (iterations 17 to 27) | 11 | at most 1 h 38 m measured | not separately metered (shared a supervised session) | n/a |
| v2-loop iteration (31 Aug, ended by a driver fault) | 1 | about 18 min of session work | not fully metered (driver fault lost the session tail) | n/a |
| Campaign 5 completion run (operator-driven) | 4 | about 13 min measured training | no agent sessions (scripted experiments through the harness) | n/a |

All runs terminated by the official convergence rule (epsilon 0.002, N 3,
on validation), inside the 50 iteration cap and the 6 hour ceiling.
Model training inside an iteration is a small share of wall-clock (about 40
to 90 seconds per 3 seed experiment). The cost is agent reasoning.

## The campaigns side by side

To be explicit: **the designated final submission is 0.6143**, the
converged checkpoint of campaign 5 — the interactive campaign's recipe
plus the autonomous loop's promoted tab_n discovery. The verification,
clean-room, and v2-loop runs are autonomy demonstrations. They are not
the scored submission and should not be averaged with it.

| Campaign | Start state | Manual interventions | Converged at |
|---|---|---|---|
| Interactive research (29 runs; culminating run 17 to 27) | official baseline | 3 loop-relevant, 0 iteration-level | 0.6116 (the champion until 31 Aug) |
| Verification run (3 iterations; non-regression check, banked nothing) | frozen research state | 0 | 0.6116 survives re-challenge |
| Clean-room run (6 iterations) | bare baseline, empty memory | 0 | 0.59744 (+0.0028 over baseline; supplementary demonstration) |
| v2-loop iteration (31 Aug, 1 iteration; see ITERATION-LOGS addendum) | frozen research state + belief state | 0 | full loop demonstrated: residual analysis -> mechanism hypothesis -> experiment (+0.0024 over control) -> placebo falsification -> sub-margin 3-seed decline |
| Campaign 5, completion run (4 iterations, operator-driven; see ITERATION-LOGS) | banked state | operator-driven by design | **0.6143, the designated final submission** (the loop's tab_n banked at the pre-committed 5-seed committee check, then three sub-epsilon iterations) |

The clean-room agent also refused two configurations whose test scores
looked better but whose validation did not justify them (its iterations 4
and 5). Those are the project's fourth and fifth documented refusals of
test-based selection, and the agent made them alone.

## Serving-assumption ablation (added 30 Aug)

The history features assume a streaming feature store. Measured on the
pre-promotion champion's weights (R24b; `code/staleness_ablation.py`),
only test featurization
changing: continuous 0.6116 (+0.0170), daily batch refresh 0.6083
(+0.0137), frozen at the test boundary 0.5943 (a lower bound distorted by
train/serve skew). See logs/PROCESS-AUDIT.md for the full reading.

## Post-freeze impact analyses (30 Aug night)

Run after the 29 Aug freeze in response to review-round impact critiques,
all measured on the champion of that date (R24b, 0.6116); none is a
selection event. The 31 Aug promotion post-dates them and changes none of
their numbers.

1. Daily-regime retraining (`code/daily_retrain.py`): every row's features
   rebuilt under a daily batch refresh and the 5-seed committee retrained
   from scratch. Result: valid 0.6145 / test 0.6106 (+0.0160 over
   baseline). This replaces the earlier mismatch-penalized figure (0.6083)
   as the deployable-cadence number: 94 percent of the headline gain
   survives when the model is trained for the serving regime.

1b. Frozen-batch retraining (`code/protocolB_retrain.py`, added 31 Aug),
   completing the freshness curve at its strict end: history frozen at
   the validation/test boundary (no test-window feedback of any kind),
   with validation rows featurized frozen at the train boundary so model
   selection happens under serving-matched staleness. Result: valid
   0.6038 / test 0.5979 (+0.0033 over baseline; singles 0.5967–0.5981).
   Retraining recovers +0.0036 of the earlier mismatch-penalized lower
   bound (0.59429). This is the fully-conservative number: in this regime
   no test-row feature can depend on any test-window outcome, so it holds
   under the strictest possible reading of test isolation, and the recipe
   still beats the official baseline there. The measured freshness curve
   is monotone: frozen +0.0033, daily +0.0160, continuous +0.0170.

2. Unbiased evaluation on random exposure (`code/unbiased_eval.py`),
   measured on the pre-promotion champion (R24b): its committee scored on
   897,721 test-window impressions from
   log_random, where videos were exposed uniformly at random (no selection
   bias), against a seed-matched 5-seed kit-baseline committee retrained
   on the standard training split. Evaluation only; the training
   retirement of this file stands. Result: ours 0.3777 vs baseline 0.3707
   (+0.0070; +0.0095 against the single-seed baseline). Range-normalized
   (floor 0.3149, oracle 0.8138, both derived in the script): baseline
   captures 11.2 percent of the attainable range, ours 12.6 percent, a
   relative gain of +12.5 percent of the baseline's captured headroom,
   comparable to the standard log's +14 percent. The advantage is not an
   artifact of the previous recommender's exposure choices. Scope note:
   features here use the same continuous-update regime as the headline,
   so this isolates exposure bias, not feature freshness. Absolute numbers
   are compressed because 37.2 percent of users in this set have no
   positive and the positive rate is 8.6 percent.

3. Precision notes on both analyses. The daily-regime retrain is a single
   5-seed committee run; its per-seed singles spread (0.6059 to 0.6081,
   std about 0.0008) matches the campaign-measured noise floor, so no
   replicate was run. Neither analysis went through the campaign harness:
   both are post-freeze impact measurements, not selection events.

4. Feature cost accounting. The seven causal features require, per user:
   the last impression's label, two bounded label deques (10 and 30), an
   impression counter, one timestamp, and positive-count maps keyed by
   author and by tag (bounded by the distinct authors/tags the user has
   seen). This is a few hundred bytes to a few KB per user, roughly tens
   of MB for the 27K-user population; every update is O(1) per impression
   and serving reads are O(1) lookups. Backfill is one chronological pass
   over the log (the shipped scripts perform it in about two minutes,
   single core, for the 1.4M-impression stream, data load included). The
   freshness trade between the two deployable cadences is about 0.001
   primary (streaming +0.0170 vs daily-batch retrained +0.0160). With the
   frozen-batch retrain (1b) the curve now has a properly-trained point at
   its strict end too: +0.0033 with no test-window feedback at all. We
   still do not fit a per-day rate — three cadences is a shape, not a
   model.

## Research extension (31 Aug, pre-submission night)

Three additions aimed at the review's Innovation critique. None touches
the designated submission.

1. Mechanism falsification of the headline claim
   (`code/controls.py` + `code/mechanism_test.py`). Our central causal
   claim was that the sequence features work because they carry
   what-the-user-just-did information. The falsification test, synthesized
   mechanically from the claim's "temporal" tag: permute which impression
   each feature vector is attached to, within each user and each split
   (per-user marginals preserved, alignment destroyed, no split-crossing,
   labels untouched), then retrain. Result, 5-seed committees per arm:

   | Arm | test primary |
   |---|---|
   | A full recipe (the champion when this ran, R24b) | 0.61164 |
   | B no sequence features | 0.59808 |
   | C features time-shuffled | 0.59872 |
   | D features replaced by matched-cardinality noise | 0.59876 |

   Decomposition of the +0.01356 sequence gain: **95 percent is timing**
   (collapses when alignment breaks), ~5 percent is generic added
   capacity, and ~0 percent is user-identity fingerprinting — the
   shuffled features perform identically to random noise (C vs D within
   0.00004). The causal-recency mechanism is proven mechanically, not
   asserted.

2. Agent research machinery (`agent/`): `belief_state.py` (structured
   persistent memory whose promote() refuses, as code, to confirm a
   mechanism-tagged hypothesis without a passing falsification control),
   `residual_analysis.py` (hypotheses generated from the champion's own
   worst validation slices, ranked by expected value), `priority.py`
   (expected value per second of compute, costed from the actual wall
   times in LOG.jsonl), and `ITERATION_PROMPT.md` v2 wiring them into the
   loop: observe residuals -> take the priciest hypothesis -> experiment
   -> falsify before banking. Each module ships with a passing self-test.

3. Exposure-debiasing frontier (`code/debias_frontier.py`): negatives in
   the listwise objective re-weighted by inverse train-window exposure
   (lambda-parameterized; a train-only statistic), each lambda trained as
   a 3-seed committee and scored on BOTH tests:

   | lambda | biased (standard) test | unbiased (random-exposure) test |
   |---|---|---|
   | 0.0 (the undebiased recipe) | 0.6009 | 0.3785 |
   | 0.5 | 0.5840 (−0.017) | 0.4122 (+0.034) |
   | 1.0 | 0.5654 (−0.035) | 0.4181 (+0.040) |

   The finding: on KuaiRand-Pure, the exchange rate is steeply diminishing.
   The first step (lambda 0 to 0.5) trades one point of biased-log score
   for about two points of unbiased-exposure score (−0.017 for +0.034);
   the second step (0.5 to 1.0) trades at only about 0.3:1 (−0.019 for
   +0.006), so most of the recoverable preference signal comes from mild
   debiasing. The curve quantifies how much of
   standard-log performance is exposure-bias fitting rather than
   preference modeling. The designated submission remains lambda = 0
   because the competition scores the logged-exposure test; a production
   system optimizing true preference would choose otherwise, and this
   curve is the measured cost of that choice.
