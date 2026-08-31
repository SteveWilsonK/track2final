# Written Project Description (for Devpost)

## How our solution addresses the problem statement

Track 2 asks for an autonomous ML research agent that improves a recommender
model on the KuaiRand-Pure within-user ranking task. The label is long_view,
the primary metric is the mean of GAUC and nDCG@5, and the official baseline
scores 0.5946.

We built that agent. It runs the loop a TikTok ML engineer runs daily:
propose a hypothesis, implement it in code, train, evaluate, reflect, and
decide what to try next. It iterates until the official convergence rule
fires (no validation improvement above 0.002 for 3 consecutive iterations).

The trade-off at the heart of this track, stated up front. Fully unaided,
in a strict clean-room run from a bare baseline with zero human input, our
agent reaches +0.0028 over the official baseline. Most of the margin we
submit came from a longer supervised campaign in which a human made three
enumerated strategic decisions, the most consequential being permission to
explore the feature family that produced most of the gain. And the final
+0.0027 of the margin is the loop's alone: a feature the autonomous
iteration derived from the champion's residuals, verified with a placebo,
and promoted through a pre-committed rule. We think the clean-room number
is the honest measure of the agent alone, and 0.6143 is the honest measure
of the system, meaning the agent plus a few human judgment calls, which is
the configuration real recommender teams would actually run. All numbers
ship with full logs, and the gap between them is itself a finding: on this
task, a handful of strategic human decisions was worth several times the
unaided improvement, though the runs also differ in length, so this bounds
rather than isolates the value of the human decisions.

Result: test primary **0.6143** (GAUC 0.6857, nDCG@5 0.5429), which is
**+0.0197 over the official baseline** (GAUC +0.0247, nDCG@5 +0.0147, and
the score under the official formula is the mean of those deltas). The
record behind it: 53 logged runs (29 interactive research, 3 verification,
6 clean-room, 4 in an unattended loop iteration, 4 in the completion run
that promoted its discovery, 1 post-promotion mechanism control, 6 in a
final converged unattended campaign) covering
about 89 configurations, including a
clean-room run
where the agent, restarted with zero prior knowledge and zero human input,
independently reached 0.59744 (+0.0028 over baseline) in 6 iterations and
1 hour 48 minutes, and a final unattended campaign (campaign 6, 3
iterations, 49 minutes, converged by the official rule) in which the agent
refuted its own top two hypotheses, held the champion, and repaired a
measurable bias in its own hypothesis-ranking instrument.

On the optional bonus benchmark, the frozen recipe transferred to
KuaiRand-1K with zero re-tuning scores **+0.0637 over the kit baseline
reproduced there** (test primary 0.6931 vs 0.6293) — over three times
the Pure margin, because 1K's users carry ~220x deeper histories and the
causal behavioral-state features scale with history depth. One
self-contained script reproduces it (`code/bonus_1k.py`); KuaiRand-27K
was not attempted.

The three discoveries that carried the score (all found and implemented by
the agent; the second family's exploration was human-permitted and
agent-executed, as the interventions summary records):

1. Match the training objective to the metric. The baseline trains pointwise
   but is graded on within-user ranking. A listwise objective (softmax over
   one positive and four within-user negatives) gave +0.0028, with a
   capacity matched control proving the gain came from the objective alone.
2. Causal sequence features. Seven features computed strictly from each
   impression's past: previous impression outcome, rolling watch rates, per
   author and per tag history, session gap. Never the row's own label, never
   anything later in time. This family carried the largest share of the
   final margin: +0.0038 at introduction under a fixed model class, about
   +0.013 once the richer variants and the committee were built on it. It
   also explained an earlier plateau: the models had been information
   starved, not under powered.
3. Surface familiarity — the autonomous loop's own discovery, promoted
   into the final submission. The v2 iteration analyzed the champion's
   residuals unattended, found its worst slice (tab=0, where stream-wide
   history reports behavior from a surface with a 10x higher positive
   rate), and proposed tab_n: the user's prior impression count on the
   row's surface, label-free. The time-shuffle placebo passed, the
   pre-committed 5-seed committee check cleared the
   promotion margin (validation 0.62059 over the incumbent 0.61906), and
   the completion run converged on it by the official rule: test 0.6143
   over the previous 0.6116. The one feature in the submission no human
   proposed. A post-promotion discriminating control (R37,
   surface-scrambled counts) then split the mechanism: about half the
   gain needs the true surface, half comes from the partitioned counting
   structure itself — the claim was revised to match, which is the
   falsification discipline working on our own newest result.

The final model is deliberately simple: a five seed committee of
Factorization Machines (k=16), reproducible from raw data in one command in
about 5 minutes on a laptop CPU. Its serving assumption is stated and
measured: the history features assume a streaming feature store; measured
on the pre-promotion champion, a daily batch refresh still scores +0.0137
without retraining and +0.0160 with a committee retrained for that regime
(94 percent of that champion's headline), and even with history frozen
before the test window entirely, a retrained committee keeps +0.0033
(all ablations ship in the repo). On the dataset's randomly-exposed
impressions, where exposure carries no recommender bias, the advantage
persists (+0.0070 against a seed-matched baseline committee; +12.5 percent
of the baseline's captured headroom, comparable to the standard log), so
the gain is not an artifact of selection bias.

Three properties of the process matter as much as the score:

- Falsification before banking. The agent's central causal claim (the
  sequence features work because of timing) was subjected to a placebo
  test synthesized mechanically from the claim's own mechanism tag:
  time-shuffling the features within each user collapses 95 percent of
  the gain, and the shuffled features do no better than random noise. The
  agent's memory (`agent/belief_state.py`) enforces this as code: a
  mechanism-tagged hypothesis cannot be marked confirmed without a passing
  control on record. Hypotheses themselves come from measured residuals
  (worst validation slices ranked by expected value), and experiment order
  comes from expected value per second of compute.
- A measured discovery about the dataset: the exposure-bias frontier. The
  exchange rate is steeply diminishing: the first debiasing step (lambda 0
  to 0.5) trades one point of biased-log score for about two points of
  unbiased-exposure score, and the next step trades at only about 0.3:1,
  under inverse-exposure weighting. The submission stays undebiased because the competition
  scores the logged-exposure test; the curve quantifies what that choice
  costs in true-preference terms.
- Enforced discipline. Every experiment runs through a harness that requires
  at least 3 seeds, a pre-committed 0.002 significance bar, and logging of
  intent before training, so failed runs cannot be hidden. All selection
  uses validation only. The logs document six separate occasions where a
  configuration was refused or declined on validation grounds despite a
  better looking test score. Three of those were made by unattended agents
  with nobody watching — including the loop's own 3-seed decline of tab_n,
  which only entered the submission after the pre-committed 5-seed
  committee check cleared the promotion margin.
- Honest negatives. The log contains more rejected ideas than accepted ones,
  each with a diagnosed mechanism, including a target-encoding leakage trap
  the agent caught and fixed, and a legality analysis that retired the
  dataset's random exposure file unused because its rows overlap the
  evaluation window.
- Autonomy with a defined boundary. A driver loops fresh agent sessions to
  convergence under the official rule, restarting crashes automatically
  (the organizers ruled restarts are not interventions). The interactive
  campaign needed 3 strategic human decisions in total, enumerated in
  `logs/INTERVENTIONS.md`. The four unattended campaigns needed zero
  during their iterations; the completion run (campaign 5) was operator-driven
  bookkeeping of a promotion the loop had already earned, documented
  step by step.

## Development tools used

- Claude Code (Anthropic): the autonomous agent itself. It wrote the
  experiment code, ran the research loop, and authored the run logs and the
  experimental commits, which are visible in the git history.
- Git and GitHub for version control. The commit trail doubles as a
  timestamped record of the agent's iterations.
- macOS terminal, zsh, and caffeinate for unattended runs on a laptop.
- Python 3.12 (CPython).

## APIs used

- Anthropic Claude API, through the Claude Code CLI. This powers the agent's
  reasoning and code generation. No other external APIs. Training and
  evaluation are fully local and offline.

## Libraries and frameworks used

- NumPy. The only numerical dependency. All models and training loops are
  implemented from scratch in NumPy. No ML framework.
- Python standard library: csv, json, collections, subprocess, os, time.

## Datasets and assets used

- KuaiRand-Pure (official Track 2 dataset, Kuaishou research release):
  1.14M train, 125K validation, 171K test logged impressions, used only
  through the official date split.
- The official Track 2 starter kit. Its scoring code and split are used byte
  identical and unmodified.
- The dataset's random exposure file was deliberately not used. Its rows
  fall inside the evaluation window, so training on it would leak future
  information. The analysis is recorded in the logs.
- No other datasets, no pretrained models, no manually labelled data.
