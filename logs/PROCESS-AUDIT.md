# Process audit and corrections (30 Aug)

Before submission we commissioned an adversarial review of this repository
and repaired what it found. This file records the findings honestly, because
several of them are about the gap between what our documents claimed and
what our code did. The score itself was never in question: the reviewer
recomputed 0.61164 from the shipped weights with the official evaluator.

## 1. The harness verdict label was computed from test deltas

Finding, confirmed: before 30 Aug, `harness.py` derived its printed verdict
label (WIN and so on) and its banked-best tracking from the TEST mean, while
its docstring and our documents said verdicts are decided on validation. The
driver's convergence constant was likewise a test-derived number.

What was actually true underneath: every banking decision in this project
was made on validation by the operator, and the evidence ships. LOG.jsonl
carries valid_mean for every result; the five refusal events (Runs 15 and
29, and the clean-room agent's iterations 4 and 5) are precisely occasions
where a test-favorable machine label was overridden because validation did
not support it. The segmentation and convergence table in ITERATION-LOGS.md
was computed from validation deltas from the start.

Correction applied: `harness.py` now computes the verdict, the banked-best
tracking, and the printed marker from validation (`BASELINE_VALID`,
`BANKED_VALID`); the test mean is recorded for audit and plays no selection
role. `driver.py` reads the validation constant, so convergence is a
validation-derived decision. `ITERATION_PROMPT.md` was updated to match.
Historical LOG.jsonl records keep their original labels; read them as
display markers, with the authoritative selection trail in RESULTS.md and
the valid_mean fields.

Accurate summary sentence, replacing looser earlier phrasing: test was
computed and visible throughout; selection was validation-only; on the five
occasions the test-derived label favored a switch that validation did not
justify, the switch was refused, and all five are logged.

## 2. Serving assumption of the sequence features, now measured

Finding, confirmed: the causal history features update continuously, so a
test row's features include the realized labels of the same user's earlier
test-window impressions. Each row still sees only strictly-prior events
(the documented rule holds), but this assumes a streaming feature store,
and the baseline has no such signal. No run had quantified the dependence.

Correction applied: `code/staleness_ablation.py` ships and its results are
now part of the submission (same frozen weights, only test featurization
changes):

| Test-time feature regime | primary | vs baseline |
|---|---|---|
| Continuous updates (as submitted; streaming feature store) | 0.61164 | +0.0170 |
| Daily batch refresh (within-day feedback withheld) | 0.60828 | +0.0137 |
| Frozen at the test boundary (no test-window feedback) | 0.59429 | −0.0003 |

Reading: about 80 percent of the headline gain survives a realistic daily
refresh cadence. The frozen number is a lower bound distorted by
train/serve skew (gap and hist_n go out of distribution); a model trained
for that regime would land between the two. The README now states the
serving assumption explicitly.

## 3. Smaller corrections, from the same review

- "The selection process never touched test" (old RESULTS.md wording) was
  wrong as written and is corrected to "never selected on test."
- The verification run (Runs 30 to 32) is a non-regression check: it
  started from the frozen state and banked nothing. Tables now label it so;
  it demonstrates that a converged state survives autonomous re-challenge,
  not autonomous improvement.
- Clean-room iterations 2 and 4 ended without a completed experiment (the
  session was waiting on a still-training grid) yet counted toward the
  below-epsilon streak. Under the official rule (iterations without
  improvement count) the convergence stands; under a stricter
  result-bearing-iterations reading the run would have needed one more
  iteration. Both readings are stated rather than hidden.
- Run 25b (cross-view blend, alpha = 1.0) is by construction identical to
  Run 24b; it is a search that selected the incumbent, not an independent
  result, and is now annotated as such.
- Run and configuration counts are reconciled everywhere as: 29 interactive
  runs + 3 verification + 6 clean-room = 38 runs, about 75 configurations.
- "The order the agent found them" (project description) is rephrased: the
  agent found both discoveries; the second family's exploration was
  human-permitted (intervention 2 in INTERVENTIONS.md) and agent-executed.
- The strict-rule segmentation of the interactive phase is a retrospective
  mapping of a supervised session onto the run formalism, and is now
  labeled as such where it appears.
- The interactive phase's per-run commits live in the research archive
  repository (github.com/SteveWilsonK/techjam-2026-workspace, public),
  linked from the README; this repo ships the scripts and logs themselves.
- `score_frozen.py` and the ablation now locate the shipped weights
  automatically (no manual copy step).
- `code/verify_claims.py` ships: it re-derives the oracle ceiling (0.8645),
  the user composition (27.1 percent zero-positive, 9.2 percent
  all-positive), the split sizes, the kit-integrity hashes (evaluate.py and
  data.py byte-identical to the official archive), and the seed-noise
  summary (median per-run 3-seed std 0.00061; final committee members' std
  0.00110) from the shipped artifacts.
- Full clean-room session transcripts are included under
  `cleanroom/transcripts/` so the per-iteration token counts and takeaways
  can be checked against raw records.

## 4. Reviewer claims we checked and rejected

- "The Run 15 refusal rests on narrative, with no shipped record of the
  rejected arm's validation margin." LOG.jsonl contains valid_mean for all
  four Run 15 arms (0.60407 / 0.60372 / 0.60406 / 0.60386).
- "No run measures the seed distribution of the final recipe." The five
  committee members' individual test scores are printed by final_model.py
  and their per-seed arrays ship in LOG.jsonl; verify_claims.py now
  summarizes them (std 0.00110).

## 5. What remains true after all corrections

The designated final submission is the validation-best checkpoint at
convergence, 0.6116 on the local test split, +0.0170 over the official
baseline, reproducible from raw data in one command, with a research trail
of 38 runs in which negatives outnumber wins and five test-favorable
switches were refused on validation grounds.

## 6. Second review round (30 Aug, evening)

The reviewer re-judged the corrected repository, verified the harness fix
behaviorally (an adversarial arm with test 0.65 and weak validation cannot
win), replayed all logged results under the validation rule and confirmed
the trajectory ends at the shipped checkpoint, and reconciled the
clean-room token figure against the shipped transcripts to the exact
number. Two findings from round one were formally withdrawn (section 4).
The remaining findings were of one type: documents asserting corrections
or tallies that a grep falsifies. All are now fixed:

- The "never touched test" sentence that section 3 claimed was corrected
  had survived in logs/RESULTS.md. It is now actually corrected. The irony
  of an audit document misstating its own corrections is not lost on us;
  this appendix was written after re-checking every claim below with grep.
- Tallies reconciled: ITERATION-LOGS.md's closing tally now reads 38 runs
  across three campaigns, ~75 configurations, 5 refusals. RESULTS.md's
  freeze-day tally is labeled as point-in-time with the final figures
  alongside.
- The promotion rule is now precise in code and prompt: a challenger must
  beat the incumbent's validation by more than PROMOTION_MARGIN (0.001,
  the noise scale); ties and sub-noise differences keep the incumbent.
  This is the rule the refusals actually followed.
- current_best() no longer walks legacy display labels (which included the
  refused R29b at 0.61907); it counts only records stamped with the
  corrected rule tag and floors at the frozen champion's 0.61906.
- code/replay_verdicts.py ships: it re-derives every historical verdict
  from validation means alone, writes a non-mutating companion log
  (logs/LOG-replay.jsonl), and prints the champion trajectory. It ends at
  the shipped checkpoint (valid 0.61906 / test 0.61164). One intermediate
  differs from the narrative (R13a briefly leads under this margin before
  the sequence-feature era); the endpoint is invariant to that choice.
- The official starter-kit archive now ships in third_party/, and
  verify_claims.py compares our files against the archive's bytes rather
  than recorded constants, so the integrity check is self-contained.
- The random floor is reported as a 5-seed mean alongside the official
  0.4753; the single-seed 0.4732 in the first version of the script was a
  seeded example, not a discrepancy.
- verify_claims.py --full recomputes the five committee singles from the
  shipped weights and retrains one baseline seed to derive its GAUC and
  nDCG@5 components, removing the last hardcoded numbers.
- The verification run's session transcripts now ship
  (logs/demoA_transcripts/), so its 149,658-token figure reconciles the
  same way the clean-room figure does.
- Attribution correction: the dataset symlink removed in an earlier commit
  was the reviewer's own footprint from their first-round ablation, not
  our mistake. Our commit message at the time guessed wrong.

Known and accepted, not fixed: the team-contributions section awaits the
team's text; the frozen-regime row of the staleness table remains a lower
bound (no model was retrained for that regime); shipped transcripts contain
local filesystem paths (scanned: no credentials).

## 7. Post-freeze impact analyses (30 Aug night)

Responding to the review's Impact critiques with measurements rather than
prose: (a) a committee retrained under the daily-batch feature regime
scores 0.6106 (+0.0160), converting the staleness table's deployable row
from a mismatch-penalized figure into a trained one; (b) an
evaluation-only use of the random-exposure log (897,721 unbiased
test-window rows) shows the advantage persists without selection bias
(+0.0095). Scripts: code/daily_retrain.py, code/unbiased_eval.py. The
designated submission is untouched by both.
