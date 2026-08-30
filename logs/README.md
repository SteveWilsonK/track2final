# Logs folder guide

| File | What it is |
|---|---|
| ITERATION-LOGS.md | The compiled per-iteration index: hypothesis, code reference, metrics, verdict for every run, plus the strict-rule segmentation and compliance tables |
| INTERVENTIONS.md | The manual interventions summary (count, enumeration, classification) |
| RESULTS.md | The full research narrative, run by run, with mechanism analysis |
| LOG.jsonl | Machine readable log. Intent records are written before training, results after |
| IDEAS.md | The agent's idea backlog: banked, dead, and open, each with the run that decided it |
| demoA_driver_log.jsonl | Driver event stream of the unattended verification run |
| cleanroom/ | The complete clean-room campaign: its own experiments, logs, driver events, and agent commit list |
| experiment_scripts/ | The exact code of every numbered experiment, preserved as run |
