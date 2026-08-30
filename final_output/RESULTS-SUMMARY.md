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

Context: the attainable range runs from random scoring at 0.4753 to the
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

| Campaign | Start state | Manual interventions | Converged at |
|---|---|---|---|
| Interactive research (29 runs; culminating run 17 to 27) | official baseline | 3 loop-relevant, 0 iteration-level | 0.6116, the designated final submission |
| Verification run (3 iterations) | frozen research state | 0 | 0.6116 confirmed |
| Clean-room run (6 iterations) | bare baseline, empty memory | 0 | 0.59744 (+0.0028 over baseline) |

The clean-room agent also refused two configurations whose test scores
looked better but whose validation did not justify them (its iterations 4
and 5). Those are the project's fourth and fifth documented refusals of
test-based selection, and the agent made them alone.
