# Manual Interventions Summary

Definition used (from the track owner's webinar): an intervention is a human
changing the agent's behavior. Restarting a crashed or interrupted run is
explicitly not an intervention, and neither is launching a run.

## The count

| Campaign | Loop-relevant interventions |
|---|---|
| Interactive research campaign (Runs 1 to 29) | **3** |
| Verification run (3 iterations, unattended, overnight) | **0** |
| Clean-room run (6 iterations, unattended, from bare baseline) | **0** |

## The three interventions, enumerated

1. Deferring three idea families (sequence features, multi-task labels, the
   random exposure log). Between Runs 13 and 14. This constrained the
   agent's search space for Runs 14 to 17.
2. Permitting those families. Between Runs 17 and 18. This directly enabled
   the Run 18 breakthrough (causal sequence features) and was the single
   most consequential human decision of the project.
3. Setting an additional stopping rule (stop at 0.65, or after 5 runs with
   no new banked best). Before Run 26. This governed when exploration ended.

Two further human actions are recorded but classified as administrative,
not loop interventions: choosing which competition track to enter (this
happened before any agent loop existed) and a request about report
formatting (cosmetic only).

At the iteration level, zero interventions occurred in any campaign. No
human proposed, implemented, tuned, or interpreted any experiment. Every
hypothesis, every piece of experiment code, every verdict, and every log
entry came from the agent.

## Recovery events (not interventions, listed for completeness)

- One external interruption (laptop lid closed during Run 6) killed a
  process after one of three configurations. The finished configuration's
  result was already logged. The rest were relaunched. Nothing was lost.
- One driver false start (the CLI was not yet authenticated). Detected in
  seconds, the log was archived rather than deleted, and the run was
  relaunched cleanly. The archived log is kept in the repository history.
- The two unattended campaigns ran with no errors and no restarts.
