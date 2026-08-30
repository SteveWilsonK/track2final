# Final Submission and Results Summary

## Final model output

- `submission.csv`: the frozen model's score for every test split row, in
  the starter kit schema (row_id, user_id, video_id, score). Validated with
  the kit's own checker: 170,588 rows, aligned.
- `frozen_model/`: the model checkpoint. Five seed weight files plus
  config.json with the full recipe. Regenerate everything from raw data
  with `python3 final_model.py` in `code/` (about 5 minutes, CPU only).

## Results table (required benchmark: KuaiRand-Pure)

The scored submission is the validation-best checkpoint at convergence,
evaluated once on the test split.

| Metric | Official baseline (test) | Ours (validation) | Ours (test) | Delta vs baseline (test) |
|---|---|---|---|---|
| GAUC | 0.6610 | 0.6926 | 0.6825 | +0.0215 |
| nDCG@5 | 0.5282 | 0.5455 | 0.5408 | +0.0126 |
| primary | 0.5946 | 0.6191 | 0.6116 | +0.0170 |

Score under the official formula (mean over metrics of the absolute delta):
(0.0215 + 0.0126) / 2 = **+0.0170**.

Context: the attainable range runs from random scoring (about 0.475; the
official statement quotes 0.4753, our seeded examples in verify_claims.py
average 0.4747) to the
oracle ceiling at 0.8645. The baseline captures about 31 percent of that
range. Our submission captures about 37 percent. We derived the ceiling
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

All runs terminated by the official convergence rule (epsilon 0.002, N 3,
on validation), inside the 50 iteration cap and the 6 hour ceiling.
Model training inside an iteration is a small share of wall-clock (about 40
to 90 seconds per 3 seed experiment). The cost is agent reasoning.

## The three campaigns side by side

To be explicit: **the designated final submission is 0.6116**, the
converged checkpoint of the interactive campaign's culminating run. The
verification and clean-room runs are supplementary autonomy demonstrations.
They are not the scored submission and should not be averaged with it.

| Campaign | Start state | Manual interventions | Converged at |
|---|---|---|---|
| Interactive research (29 runs; culminating run 17 to 27) | official baseline | 3 loop-relevant, 0 iteration-level | **0.6116, the designated final submission** |
| Verification run (3 iterations; non-regression check, banked nothing) | frozen research state | 0 | 0.6116 survives re-challenge |
| Clean-room run (6 iterations) | bare baseline, empty memory | 0 | 0.59744 (+0.0028 over baseline; supplementary demonstration) |

The clean-room agent also refused two configurations whose test scores
looked better but whose validation did not justify them (its iterations 4
and 5). Those are the project's fourth and fifth documented refusals of
test-based selection, and the agent made them alone.

## Serving-assumption ablation (added 30 Aug)

The sequence features assume a streaming feature store. Measured with the
shipped weights (`code/staleness_ablation.py`), only test featurization
changing: continuous 0.6116 (+0.0170), daily batch refresh 0.6083
(+0.0137), frozen at the test boundary 0.5943 (a lower bound distorted by
train/serve skew). See logs/PROCESS-AUDIT.md for the full reading.

## Post-freeze impact analyses (30 Aug night)

Run after the freeze in response to review-round impact critiques. Neither
touches the designated submission; the frozen checkpoint is unchanged.

1. Daily-regime retraining (`code/daily_retrain.py`): every row's features
   rebuilt under a daily batch refresh and the 5-seed committee retrained
   from scratch. Result: valid 0.6145 / test 0.6106 (+0.0160 over
   baseline). This replaces the earlier mismatch-penalized figure (0.6083)
   as the deployable-cadence number: 94 percent of the headline gain
   survives when the model is trained for the serving regime.

2. Unbiased evaluation on random exposure (`code/unbiased_eval.py`):
   the frozen committee and the retrained official baseline scored on
   897,721 test-window impressions from log_random, where videos were
   exposed uniformly at random (no selection bias). Evaluation only; the
   training retirement of this file stands. Result: ours 0.3777 vs
   baseline 0.3682 (+0.0095; GAUC +0.0090, nDCG@5 +0.0100). The model's
   advantage is not an artifact of the previous recommender's exposure
   choices. Absolute numbers are lower in this regime because random
   exposure yields few positives per user.
