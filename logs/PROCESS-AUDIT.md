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
| Continuous updates (the champion as of this 30 Aug analysis, R24b; streaming feature store) | 0.61164 | +0.0170 |
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
  (Superseded 31 Aug by the fourth campaign: the total is now 42 runs,
  about 79 configurations; see section 9.)
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
convergence — at the time of this section, 0.6116 on the local test split
(+0.0170), reproducible from raw data in one command, with a research
trail of 38 runs in which negatives outnumber wins and five test-favorable
switches were refused on validation grounds. (As of 31 Aug evening: the
checkpoint is 0.6143 after the rule-following promotion of the loop's own
discovery — see section 10 — the trail is 46 runs, and a sixth
validation-grounded refusal is logged; see section 9.)

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
  across three campaigns, ~75 configurations, 5 refusals (figures as of 30
  Aug; the 31 Aug campaign brings these to 42 runs, four campaigns, 6
  refusals — see section 9). RESULTS.md's
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
test-window rows) shows the advantage persists without selection bias.
A follow-up review round asked for a seed-matched baseline and
range-normalized context; we added both, and the stricter comparison
shrank our own reported delta (+0.0095 single-seed to +0.0070
committee-vs-committee, +12.5 percent of captured headroom, comparable to
the standard log rather than larger). We report the stricter numbers as
primary. Scripts: code/daily_retrain.py, code/unbiased_eval.py. The
designated submission is untouched by both.

## 8. Pre-submission research extension (31 Aug, overnight)

Executed in response to the Innovation critique, with the frozen submission
untouched throughout. (a) A falsification engine (`code/controls.py`) that
synthesizes placebo tests from a claim's mechanism tag; applied to the
headline claim it shows 95 percent of the sequence gain is timing and the
time-shuffled features equal random noise (`code/mechanism_test.py`).
(b) The exposure-bias frontier (`code/debias_frontier.py`): a steeply
diminishing exchange rate between unbiased-exposure gains and biased-log
losses under inverse-exposure negative weighting — about 2:1 on the first
debiasing step (lambda 0 to 0.5), falling to about 0.3:1 on the second;
submission remains lambda 0.
(c) Research machinery in `agent/`: structured belief state with
control-gated promotion enforced as code, residual-driven hypothesis
generation (its first live run surfaced tab=0, validation primary 0.304 vs
0.619 overall, as the model's largest weakness), and cost-aware experiment
ordering from logged wall times; the iteration prompt (v2) wires them into
the loop, and a further unattended campaign was launched under it. Every
module ships with a passing self-test. Two float-serialization crashes
during the night were fixed and are visible in the working history.

## 9. The v2-loop campaign (31 Aug morning), audited

The campaign launched under the v2 prompt ran one full unattended
iteration and then halted on an infrastructure fault: the agent session
exited cleanly at 10:13 but the driver wrapper died without logging its
iteration-end event, so `agent/driver_log.jsonl` records only the start
events. Nothing about the iteration itself is reconstructed from memory;
every step is in committed artifacts. In order: the residual analyzer ran
and surfaced tab=0; the session identified a bias in the analyzer's own
expected-value measure (slice-restricted scoring is degenerate when 92
percent of a slice's users carry no positive label inside it) and rewrote
the analyzer to rank by oracle headroom, with a self-test; it wrote
`code/tab_surface.py` with an explicit mechanism claim; it ran a control
(R33-ctrl, valid 0.61715), two arms (R33a 0.61806, R33b 0.61955), and an
unprompted time-shuffle placebo (0.61612, below control, gain fully
collapsed); and it declined to bank R33b because +0.00049 over the banked
0.61906 is under the 0.001 promotion margin. The frozen submission is
unchanged. Honest accounting: this campaign demonstrates one iteration of
the loop, not a converged run; it is labeled that way everywhere it is
mentioned. A second gap, also disclosed: the session recorded its evidence
and control in the harness log but never wrote them back into the belief
state via attach_evidence()/attach_control(), so belief_state.json still
shows both hypotheses as proposed with the analyzer's pre-repair EV, and
the code-enforced promote() gate — exercised in the module's self-test —
was not exercised live; the decline came from the harness promotion
margin. The file is preserved exactly as the agent left it rather than
groomed after the fact.

## 10. The promotion (31 Aug evening), audited

The submission changed on the final day, and this section records exactly
how and why, because a late change to a frozen result is the kind of event
an auditor should distrust by default.

The sequence: (a) a peer review flagged that tab_surface.py's pre-committed
rule had an unverifiable final step — its 5-seed committee promotion check
ran outside the harness and the driver fault destroyed the output; (b) the
operator re-ran that exact step, logged through the harness
(tab_committee_check.py, record R33c with per-seed test scores): committee
validation 0.62059, above the banked 0.61906 plus the 0.001 margin, so the
rule written before any R33 arm ran says promote; (c) the promotion was
executed inside campaign 5 (campaign5.py), a four-iteration run banked and
converged under the official rule (R34 -0.00355, R35 -0.00170, R36
-0.00070, three consecutive sub-epsilon iterations); (d) the checkpoint
was re-frozen from scratch (final_model.py) and the submission file
regenerated with two independent alignment checks
(make_final_submission.py); (e) the belief state was brought up to date
through its own API, exercising the control-gated promote() live for the
first time (close_the_loop.py).

Selection integrity: every decision in the chain used validation only.
The test numbers of R33c were recorded (as every harness record does) but
the promotion condition was the validation margin, the same rule that
governed every earlier banking event. The 3-seed decline that preceded it
(v2 loop, sub-margin) and the 5-seed promotion that followed are both
correct applications of the same written rule at different evidence
levels.

Authorship: the hypothesis, the mechanism claim, the placebo control, and
the experiment code are the unattended agent session's (verified
externally against the pre-commit working tree). The committee completion,
campaign 5, and the freeze are operator work, labeled as such everywhere.

What did NOT move with the champion: the post-freeze analyses of sections
7-9 (staleness curve, unbiased evaluation, mechanism decomposition, bias
frontier) were measured on the R24b champion and are now labeled with
that provenance; the R24b weights ship at final_output/frozen_model_r24b
so every one of those numbers remains reproducible. The new champion adds
one label-free count feature on top of the audited recipe.

## 11. The R37 mechanism revision (31 Aug, after review round 9)

The ninth review round observed that the R33 time-shuffle placebo does not
discriminate between two live mechanisms for tab_n — surface familiarity
and bare counting structure — because full detachment destroys both. The
requested control was run (code/tab_mechanism_control.py, harness record
R37): the identical count computed over surface labels scrambled within
each user and split, preserving the chronological counting structure and
every per-user marginal, destroying only which surface each count tracks.

Result: valid 0.61849 — roughly half of the R33b gain survives scrambling (56 percent as measured, a single 3-seed run with both components near the noise floor)
(the pre-committed collapse criterion was under 50 percent surviving). The
pure surface-familiarity story is therefore refuted as the sole mechanism:
roughly half the effect needs the true surface, roughly half comes from
the partitioned counting structure itself (parallel monotone counters add
positional resolution beyond the global hist_n). With 3-seed noise around
0.001 the split is approximate — the honest statement is "about half and
half," not a precise decomposition.

Consequences, applied: the mechanism claim is revised everywhere from
"surface familiarity" to "partitioned familiarity" (README, project
description, belief state evidence); the promotion itself is unaffected,
because banking was decided by the validation margin under the
pre-committed rule, never by the mechanism narrative. This is the second
time in the project a falsification control has overturned part of our own
preferred story (the first shrank the sequence-feature claim to timing),
and it is recorded with the same prominence as the claims it revised.

## 12. Campaign 6 (31 Aug evening), audited

The final unattended campaign, run on the repaired driver (session output
to files, process-group kill on timeout — the campaign-4 wedge cannot
recur). Driver-timed: 3 iterations, 18:02:23 to 18:51:34, converged by
the official rule with zero human input after launch. Nothing was banked;
the champion and submission are untouched (validation 0.62059 / test
0.61429), which was verified after the run by re-deriving the trajectory
(replay_verdicts.py) and re-reading BANKED_VALID.

What the campaign produced is negatives and instrument repairs, and both
are the point. Iteration 1 took the analyzer's top hypothesis (tab=1
session depth), grounded it on train-only data, tested it, refuted it by
the pre-committed rule, and diagnosed why the plausible pre-filter that
would have endorsed it is not trustworthy. Iterations 2-3 (one experiment
across two driver iterations — the iteration-2 session exited with its
arms still training, and iteration 3 adjudicated the in-flight experiment
rather than duplicating it) refuted the partition-count generalisation
(tag_n/auth_n), and the refutation exposed a real defect in the loop's
own instrument: the expected-value queue was ranking residual slices by
size, so an above-average slice with zero collectable headroom reached
the top. The agent replaced the measure with a matched-null version
(EVx), shipped a regression self-test for the exact defect, and
documented a discarded null design rather than hiding it.

Counting note, stated as with the clean-room run: iteration 2 counted
toward the below-epsilon streak without an adjudicated experiment. The
official rule counts iterations without improvement, so the convergence
stands; a stricter result-bearing reading would require one more
iteration. Both readings are in ITERATION-LOGS.

Authorship: every hypothesis, experiment, refutation, post-mortem, and
instrument repair in this campaign is the agent's, committed by its own
sessions with agent-prefixed messages (ad3f95e, e070d48, 76f7f48). The
operator's contributions were the pre-launch driver fix and this audit
section, written after convergence.
