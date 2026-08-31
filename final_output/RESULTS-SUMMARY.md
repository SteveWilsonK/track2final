# Final Submission and Results Summary

## Final model output

Our final submission consists of three reproducible artefacts.

- `submission.csv` contains the frozen model's score for every row in the test split using the starter-kit schema: `row_id, user_id, video_id, score`. We validated all **170,588 rows** with the starter kit's own checker and then re-evaluated the written scores in the official row order. Running `code/make_final_submission.py` reproduces the final primary score of **0.61430**.

- `frozen_model/` contains the final model checkpoint, **R33c**, including five seed-specific weight files and a `config.json` file describing the complete modelling recipe. The full model can be regenerated from raw data by running `python3 final_model.py` inside `code/`. Training takes approximately **five minutes on CPU**.

- `frozen_model_r24b/` preserves the previous champion, which achieved **0.6116** on the test set. We retain this checkpoint because several later analyses were performed before the final promotion, and preserving it ensures that those results remain exactly reproducible.

---

## Main benchmark: KuaiRand-Pure

The scored submission is the checkpoint that achieved the best validation result at convergence. The test split was then evaluated once using that frozen model.

| Metric | Official baseline (test) | Ours (validation) | Ours (test) | Improvement vs baseline |
|---|---:|---:|---:|---:|
| GAUC | 0.6610 | 0.6948 | **0.6857** | **+0.0247** |
| nDCG@5 | 0.5282 | 0.5464 | **0.5429** | **+0.0147** |
| Primary | 0.5946 | 0.6206 | **0.6143** | **+0.0197** |

Under the official scoring formula, the final improvement is the mean absolute gain across GAUC and nDCG@5:

```text
(0.0247 + 0.0147) / 2 = +0.0197
```

The final score is therefore:

## **0.5946 → 0.6143**

This checkpoint was promoted on **31 August** as R33c. It combines the seven-feature behavioural recipe with the autonomous research loop's `tab_n` discovery, which passed the pre-committed committee check before the campaign converged.

The previous champion, R24b, scored **0.6116** and remains archived because several post-freeze analyses were run before R33c was promoted.

### How large is the improvement in context?

A random scoring system achieves approximately **0.475**, while the estimated oracle ceiling is **0.8645**.

The official baseline therefore captures roughly **31% of the available improvement between random performance and the ceiling**, whereas our final submission captures approximately **36%**.

We independently derived the arithmetic behind the ceiling before comparing it with the organisers' published figures. In the test set, **27.1% of users have no positive label**, while **9.2% have only positive labels**, and our calculation matches the organisers' result.

The comparison helps contextualise the numerical gain: the model moves meaningfully further through the attainable performance range rather than producing only a small change around an arbitrary score.

---

# Bonus benchmark: KuaiRand-1K

On the final night, we tested whether the frozen recipe could transfer to the substantially larger **KuaiRand-1K** dataset.

Importantly, we performed **zero benchmark-specific retuning**.

The transferred model preserved the same:

- label definition;
- split dates;
- evaluation metric;
- behavioural features, including `tab_n`;
- objective;
- model class;
- hyperparameters; and
- committee construction.

The baseline arm reproduces the starter kit's pointwise factorisation-machine recipe using three seeds, which scored **0.6338, 0.6300, and 0.6243**.

The entire transfer experiment can be reproduced with:

```bash
python3 code/bonus_1k.py
```

The complete output is stored in:

```text
logs/bonus_1k.out
```

| KuaiRand-1K — 11.7M rows, 1,000 users | Validation | Test primary |
|---|---:|---:|
| Reproduced kit baseline, 3-seed mean | — | 0.6293 |
| **Our frozen recipe, 5-seed committee** | **0.6868** | **0.6931** |
| **Improvement** |  | **+0.0637** |

The committee achieved **GAUC 0.7017** and **nDCG@5 0.6844**, while individual seeds scored between **0.6874 and 0.6920**.

Model selection remained validation-only throughout. Early stopping and committee construction never used the test split, which was evaluated only after each arm had been frozen.

## Why this result matters

The improvement on KuaiRand-1K is more than three times larger than the **+0.0197** margin achieved on KuaiRand-Pure.

That difference directly supports the central idea behind the project.

KuaiRand-Pure provides approximately **53 logged impressions per user**, whereas KuaiRand-1K provides roughly **11,700**.

Our model is designed to represent a user's recent behavioural state, so a deeper history gives those features much more evidence from which to infer changing preferences.

In simple terms:

> **When the model had much more behavioural history, the advantage of modelling recent user behaviour became substantially larger.**

The comparison is especially useful because the larger gain emerged without retuning the modelling recipe for the second dataset.

### Engineering changes required for scale

Two implementation changes were necessary because KuaiRand-1K is approximately eight times larger.

First, we replaced row-oriented feature generation with columnar feature construction, while preserving exactly the same feature definitions and chronological ordering.

Second, we used sparse Adam updates with frequency-capped ID vocabularies because dense optimisation is impractical with approximately **4.4 million video IDs**. Video IDs appearing fewer than two times during training share an `UNK` representation, following the same principle already used by the starter kit for unseen IDs.

These changes alter how the model is computed, not what the model is designed to learn.

The transfer experiment was conducted after the designated KuaiRand-Pure submission had been frozen, so it serves as an impact and generalisation analysis rather than a model-selection event.

KuaiRand-27K was not attempted.

---

# Resource usage

All resource measurements are based on recorded logs rather than estimates.

Token counts were summed from the usage fields of unattended agent-session transcripts, while wall-clock times were calculated from driver timestamps.

No GPU was used at any stage.

**GPU-hours: 0**

All model training ran on a single laptop CPU using NumPy.

| Run | Iterations | Wall-clock | LLM tokens in + out | Including cache reads/writes |
|---|---:|---:|---:|---:|
| Verification run | 3 | 52 min 32 s | 149,658 | 6,188,547 |
| Clean-room run | 6 | 1 h 47 min 41 s | 325,476 | 17,978,927 |
| Interactive culminating run | 11 | ≤ 1 h 38 min measured | Not separately metered | n/a |
| v2-loop iteration | 1 | ~18 min | Not fully metered | n/a |
| Campaign 5 completion | 4 | ~13 min measured training | No agent sessions | n/a |
| Campaign 6 | 3 | 49 min 11 s | Not separately metered | n/a |

All completed runs remained within the official limit of **50 iterations** and the **six-hour wall-clock ceiling**.

They also terminated according to the predefined convergence rule: an improvement threshold of **epsilon = 0.002** across **three consecutive validation iterations**.

Model training itself consumed only a small fraction of the total research time. A typical three-seed experiment required approximately **40–90 seconds**, so the larger computational cost came from the agent's reasoning and experimental process.

---

# Research campaigns

The project contains several research campaigns, but only one is the designated competition submission.

The final scored submission is:

## **Campaign 5 — R33c — test primary 0.6143**

The verification, clean-room, v2-loop, and later campaigns evaluate autonomy, reproducibility, falsification, or convergence. They are therefore supporting research runs rather than alternative competition submissions.

| Campaign | Starting point | Manual intervention | Outcome |
|---|---|---|---|
| Interactive research | Official baseline | 3 loop-relevant interventions, none at iteration level | 0.6116 |
| Verification run | Frozen research state | 0 | 0.6116 survives re-challenge |
| Clean-room run | Bare baseline, empty memory | 0 | 0.59744 |
| v2-loop iteration | Frozen research state + belief state | 0 | Full hypothesis and falsification loop demonstrated |
| **Campaign 5** | Banked research state | Operator-driven by design | **0.6143 final submission** |
| Campaign 6 | Banked state + belief state | 0 | Converged with no new feature promoted |

### Interactive research

The interactive research campaign developed the main behavioural recipe and produced the previous champion score of **0.6116**.

### Verification run

The unattended verification run challenged the frozen champion across three iterations and found no justified replacement. The **0.6116** model therefore survived re-evaluation.

### Clean-room run

The clean-room experiment restarted from the bare official baseline with no saved research memory or manual intervention.

It converged at **0.59744**, approximately **+0.0028 above baseline**.

The score is not intended to compete with the final model. Instead, the experiment evaluates whether the research loop can produce an improvement from an intentionally weak starting point without inheriting the previous campaign's discoveries.

More importantly, the clean-room agent rejected two configurations whose test scores appeared stronger because the corresponding validation results did not justify promotion.

Those decisions provide direct evidence that the system can resist selecting models simply because they happen to perform well on the test split.

### v2 research loop

The v2-loop iteration demonstrated the complete research process:

```text
Residual analysis
      ↓
Mechanism hypothesis
      ↓
Experiment
      ↓
+0.0024 over control
      ↓
Placebo falsification
      ↓
Three-seed confirmation
```

The iteration ended because of a driver fault, but the full hypothesis-to-falsification process was recorded before termination.

### Campaign 5

Campaign 5 promoted the autonomous loop's `tab_n` discovery after it passed the pre-committed five-seed committee check.

The campaign then completed three consecutive sub-epsilon iterations and converged according to the official stopping rule.

The resulting R33c checkpoint achieved the designated final score of:

## **0.6143**

### Campaign 6

Campaign 6 ran unattended for **49 minutes and 11 seconds** after the final promotion.

It promoted nothing.

Instead, the agent rejected its two highest-ranked hypotheses, concerning session depth and partition-count generalisation, recorded post-mortems for both failures, and corrected a size bias it discovered in its own hypothesis-ranking procedure.

That outcome is valuable because autonomous research should not require every campaign to produce a positive result.

A system that can identify and preserve negative evidence reduces the chance of repeatedly pursuing the same failed explanation.

---

# Serving assumptions

Our behavioural features are most naturally used with a streaming feature store, where user state updates after each new interaction.

However, production systems may refresh behavioural features less frequently.

We therefore tested three different assumptions about how fresh the user's history remains.

The original ablation changed only test-time feature freshness while keeping the R24b model weights fixed:

| Serving assumption | Test primary | Improvement |
|---|---:|---:|
| Continuous updates | 0.6116 | +0.0170 |
| Daily batch refresh | 0.6083 | +0.0137 |
| Frozen at test boundary | 0.5943 | approximately baseline |

The frozen result is deliberately conservative because the model had been trained under fresher conditions, creating a mismatch between training and deployment.

We therefore ran additional serving-matched retraining experiments.

---

# Post-freeze impact analyses

These experiments were conducted after the 29 August freeze to investigate practical deployment and evaluation questions.

They were measured using R24b, the champion available at that time, and were not used to select the final R33c submission.

## Daily-refresh retraining

`code/daily_retrain.py` rebuilds every behavioural feature under a daily-refresh regime and retrains the full five-seed committee from scratch.

The resulting model achieved:

- Validation: **0.6145**
- Test: **0.6106**
- Improvement over baseline: **+0.0160**

The result shows that approximately **94% of the continuous-update gain survives under daily feature refresh**.

This is more informative than simply applying stale features to a model trained with continuous updates because the training and serving assumptions now match.

## Fully frozen retraining

`code/protocolB_retrain.py` tests the strictest possible interpretation of test isolation.

User history is frozen at the validation or test boundary, meaning that no outcome observed during the test period can influence any later test-row feature.

Validation features are similarly frozen at the training boundary, ensuring that model selection occurs under the same serving conditions.

The retrained model achieved:

- Validation: **0.6038**
- Test: **0.5979**
- Improvement over baseline: **+0.0033**
- Individual seeds: **0.5967–0.5981**

The result recovers **+0.0036** relative to the earlier mismatched frozen evaluation.

More importantly, the recipe still exceeds the official baseline even when no test-window behavioural feedback is permitted.

The complete freshness curve is therefore:

## **Frozen +0.0033 → Daily +0.0160 → Continuous +0.0170**

The relationship is monotonic: fresher behavioural state produces stronger recommendation performance.

However, three measured serving regimes are not enough to justify fitting a continuous per-day performance model, so we report the observed shape without extrapolating beyond the evidence.

---

# Evaluation under random exposure

Recommendation logs contain an important source of bias because users can only respond to videos that the previous recommendation system decided to show them.

A strong model may therefore partly learn the behaviour of the previous recommender rather than underlying user preference.

To test that possibility, `code/unbiased_eval.py` evaluates the R24b committee on **897,721 impressions** from `log_random`, where videos were exposed uniformly at random.

We compare it against a seed-matched five-seed starter-kit baseline retrained on the standard training split.

| Random-exposure evaluation | Primary score |
|---|---:|
| Baseline committee | 0.3707 |
| **Our behavioural model** | **0.3777** |
| **Improvement** | **+0.0070** |

Against the single-seed official-style baseline, the advantage is **+0.0095**.

Absolute scores are lower because this test is substantially more difficult: **37.2% of users have no positive interaction**, and the overall positive rate is only **8.6%**.

To contextualise the result, we also calculated the attainable range.

- Random floor: **0.3149**
- Oracle ceiling: **0.8138**
- Baseline captures: **11.2%** of attainable headroom
- Our model captures: **12.6%**
- Relative gain over baseline's captured headroom: **+12.5%**

That relative improvement is comparable to the approximately **+14%** gain observed under the standard logged evaluation.

The result therefore suggests that our advantage is not simply an artefact of what the previous recommendation system chose to expose.

This experiment isolates exposure bias rather than feature freshness because it retains the same continuous-update behavioural regime as the headline model.

---

# Cost of the behavioural features

The final behavioural recipe is deliberately lightweight.

For each user, the model maintains:

- the previous impression's label;
- two bounded recent-label buffers of length 10 and 30;
- an impression counter;
- one timestamp;
- positive-interaction counts by author; and
- positive-interaction counts by tag.

The resulting state requires approximately a few hundred bytes to a few kilobytes per user, depending on how many authors and tags that user has encountered.

Across a population of approximately **27,000 users**, this corresponds to roughly tens of megabytes rather than a large distributed feature store.

Each impression updates the relevant state in **O(1)** time, while serving requires only constant-time lookups.

A complete chronological backfill across the **1.4 million-impression** KuaiRand-Pure stream takes approximately **two minutes on a single CPU core**, including data loading.

The deployment trade-off between daily and continuous refresh is comparatively small:

- Daily retrained: **+0.0160**
- Continuous: **+0.0170**

The additional gain from continuous freshness is therefore approximately **0.001 primary**, although the appropriate production choice would depend on the operational cost of maintaining streaming state.

---

# Research extension: testing the mechanism

The project claims that recent behavioural features improve recommendation quality because they capture **what the user has just been doing**.

A score increase alone cannot establish that mechanism, so we designed an experiment intended to falsify it.

Using `code/controls.py` and `code/mechanism_test.py`, we shuffled the behavioural feature vectors within each user's history and within each dataset split.

This procedure preserves:

- the same users;
- the same labels;
- the same feature distributions;
- the same split membership; and
- the same amount of information.

What it destroys is the alignment between a behavioural state and the moment when that behaviour actually occurred.

We then retrained five-seed committees under four conditions.

| Experiment | Test primary |
|---|---:|
| **A. Full behavioural recipe** | **0.61164** |
| B. Remove sequence features | 0.59808 |
| C. Keep features but shuffle their timing | 0.59872 |
| D. Replace them with matched random noise | 0.59876 |

The full sequence features provide a gain of approximately:

```text
0.61164 - 0.59808 = +0.01356
```

When temporal alignment is destroyed, nearly all of that gain disappears.

Approximately **95% of the sequence-feature advantage depends on timing**.

More importantly, shuffled behavioural features and matched random noise perform almost identically:

```text
0.59872 vs 0.59876
```

The difference is only **0.00004**.

This comparison rules against a simpler explanation in which the model merely benefits from receiving additional high-cardinality signals or another indirect user identifier.

Instead, the evidence indicates that the useful information comes predominantly from attaching behavioural history to the **correct point in time**.

The experiment therefore converts the qualitative claim that “recent behaviour matters” into a directly testable mechanism.

---

# Autonomous research machinery

The `agent/` directory contains the components that allow the system to maintain and challenge research hypotheses across iterations.

## `belief_state.py`

This module stores structured research beliefs and the evidence supporting or contradicting them.

For hypotheses that make a specific mechanism claim, `promote()` can refuse confirmation unless a corresponding falsification control has passed.

The rule moves scientific caution from an instruction in a prompt into the executable research system itself.

## `residual_analysis.py`

This module examines the current champion's weakest validation slices and converts those failures into candidate hypotheses.

The agent therefore begins new research from observed model errors rather than generating changes without reference to the current model's behaviour.

## `priority.py`

Candidate experiments are ranked partly according to their expected value per second of computation.

The cost estimate uses measured wall-clock times recorded in `LOG.jsonl`, which anchors prioritisation in observed experiment cost rather than arbitrary assumptions.

## `ITERATION_PROMPT.md`

The iteration prompt connects these components into the full research loop:

```text
Observe residuals
      ↓
Generate a mechanism hypothesis
      ↓
Rank candidate experiments
      ↓
Run the highest-value experiment
      ↓
Attempt falsification
      ↓
Promote or reject
      ↓
Update the belief state
```

Each component ships with a passing self-test.

Collectively, these modules move the agent beyond simple automated parameter search by requiring it to connect model weaknesses with explanations that can be experimentally challenged.

---

# Exposure-debiasing frontier

Our final research extension examines the difference between performing well on historical recommendation logs and estimating preference under more neutral exposure.

`code/debias_frontier.py` reweights negative training examples according to inverse historical exposure frequency.

The parameter `lambda` controls the strength of this correction.

Each value is trained as a three-seed committee and evaluated on both the ordinary logged test and the random-exposure test.

| Exposure correction | Standard logged test | Random-exposure test |
|---|---:|---:|
| `lambda = 0.0` | **0.6009** | 0.3785 |
| `lambda = 0.5` | 0.5840 | **0.4122** |
| `lambda = 1.0` | 0.5654 | **0.4181** |

The first correction step produces a clear trade-off:

- Standard logged score: **−0.017**
- Random-exposure score: **+0.034**

In other words, the model sacrifices roughly one point of logged-test performance for approximately two points of performance under random exposure.

The second correction step produces much weaker returns:

- Standard logged score: **−0.019**
- Random-exposure score: **+0.006**

Most of the recoverable unbiased-preference signal therefore appears after mild correction, while stronger correction continues to sacrifice logged-test performance for relatively little additional gain.

This frontier makes an important distinction visible.

A recommendation system can optimise the historical log very effectively while still learning patterns influenced by what the previous recommender chose to expose.

By contrast, exposure correction pushes the model towards performance under more neutral exposure, but doing so reduces its score on the competition's logged test.

The designated competition submission therefore uses:

```text
lambda = 0
```

because the competition evaluates the standard logged-exposure test.

A production system designed to estimate underlying preference more directly could choose a different point on the measured frontier.

The experiment does not claim that one objective is universally better. Instead, it quantifies the cost of moving between them.

---

# Summary

The final KuaiRand-Pure submission improves the official primary score from:

## **0.5946 → 0.6143**

The same frozen recipe transfers to KuaiRand-1K without retuning and improves the reproduced baseline from:

## **0.6293 → 0.6931**

The larger transfer result strengthens the project's central behavioural argument because users in KuaiRand-1K provide substantially more interaction history.

The mechanism experiment further shows that approximately **95% of the sequence-feature gain disappears when temporal alignment is destroyed**, indicating that timing rather than simple feature capacity drives most of the improvement.

Practical serving experiments show that a daily-refresh implementation retains approximately **94% of the continuous-update gain**, while even the strictest frozen-history regime remains above the official baseline after serving-matched retraining.

Finally, the random-exposure and debiasing experiments show that strong logged-test performance and unbiased preference estimation are related but distinct objectives.

Collectively, the results support three central claims:

1. **Recent behavioural state provides useful recommendation signal beyond static user identity.**
2. **The value of that signal increases when substantially more behavioural history is available.**
3. **An autonomous research loop can identify improvements, challenge its own explanations, preserve negative evidence, and promote only results supported by predefined validation rules.**

The final score is important, but the broader contribution is the research process that produced and tested it.
