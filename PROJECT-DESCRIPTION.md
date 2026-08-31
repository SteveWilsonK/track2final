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
agent reaches +0.0028 over the official baseline. The +0.0170 we submit
came from a longer supervised campaign in which a human made three
enumerated strategic decisions, the most consequential being permission to
explore the feature family that produced most of the gain. We think the
clean-room number is the honest measure of the agent alone, and 0.6116 is
the honest measure of the system, meaning the agent plus a few human
judgment calls, which is the configuration real recommender teams would
actually run. Both numbers ship with full logs, and the gap between them
is itself a finding: on this task, a handful of strategic human decisions
was worth about six times the unaided improvement, though the two runs also
differ in length (6 iterations against 29), so this bounds rather than
isolates the value of the human decisions.

Result: test primary **0.6116** (GAUC 0.6825, nDCG@5 0.5408), which is
**+0.0170 over the official baseline** (GAUC +0.0215, nDCG@5 +0.0126, and
the score under the official formula is the mean of those deltas). The
record behind it: 42 logged runs (29 interactive research, 3 verification,
6 clean-room, 4 in a final unattended loop iteration) covering about 79
configurations, including a clean-room run
where the agent, restarted with zero prior knowledge and zero human input,
independently reached 0.59744 (+0.0028 over baseline) in 6 iterations and
1 hour 48 minutes.

The two discoveries that carried the score (both found and implemented by
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

The final model is deliberately simple: a five seed committee of
Factorization Machines (k=16), reproducible from raw data in one command in
about 5 minutes on a laptop CPU. Its serving assumption is stated and
measured: the sequence features assume a streaming feature store; under a
daily batch refresh the shipped model still scores +0.0137, and a committee
retrained for that regime scores +0.0160, 94 percent of the headline
(both ablations ship in the repo). On the dataset's randomly-exposed
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
  uses validation only. The logs document five separate occasions where a
  configuration with a better looking test score was refused because
  validation did not justify it. Two of those refusals were made by the
  unattended agent with nobody watching.
- Honest negatives. The log contains more rejected ideas than accepted ones,
  each with a diagnosed mechanism, including a target-encoding leakage trap
  the agent caught and fixed, and a legality analysis that retired the
  dataset's random exposure file unused because its rows overlap the
  evaluation window.
- Autonomy with a defined boundary. A driver loops fresh agent sessions to
  convergence under the official rule, restarting crashes automatically
  (the organizers ruled restarts are not interventions). The interactive
  campaign needed 3 strategic human decisions in total, enumerated in
  `logs/INTERVENTIONS.md`. The two unattended campaigns needed zero.

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
