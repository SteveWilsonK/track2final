"""Operator bookkeeping (31 Aug): write the R33 outcome into the belief
state through the module's own API, exercising the control gate live.

The v2-loop session recorded its evidence and control in the harness log
but never called attach_evidence()/attach_control(), a gap disclosed in
PROCESS-AUDIT section 9. With the hypothesis now promoted into the final
submission (campaign 5), the belief state is brought up to date the only
legitimate way the module allows: evidence attached, the passing
time-shuffle control attached, then promote() — which raises if the
control is missing or failed, and this run is the gate's first live
exercise. The pre-update file (the agent session's untouched artifact) is
preserved in git history at commit 59fcafe and earlier.

Run from agent/:  python3 close_the_loop.py
"""
import belief_state as BS

if __name__ == '__main__':
    st = BS.load()
    h = BS.get(st, 'residual_tab_0')

    # the agent's residual analyzer v2 superseded its own EV measure with
    # oracle headroom; the promoted outcome supersedes both — keep the
    # original value in the record, annotated
    h['mechanism'] = 'temporal'   # per tab_surface.py's stated claim
    BS.attach_evidence(st, 'residual_tab_0', {
        'run': 'R33b RICH + tab_n only (3 seeds)',
        'valid_mean': 0.61955, 'test_mean': 0.6124,
        'control_run': 'R33-ctrl RICH (control)', 'control_valid': 0.61715})
    BS.attach_evidence(st, 'residual_tab_0', {
        'run': 'R33c RICH + tab_n 5-seed committee (BANKED)',
        'valid': 0.62059, 'test': 0.61429,
        'note': 'promoted, campaign 5; designated final submission'})
    BS.attach_control(st, 'residual_tab_0', 'time_shuffle', 'passed',
                      'R33-placebo valid 0.61612 vs control 0.61715: the '
                      'entire +0.0024 gain collapses when the per-surface '
                      'count is detached from its impression')
    BS.promote(st, 'residual_tab_0')   # raises unless the control passed
    BS.save(st)
    print("residual_tab_0 -> confirmed (control-gated promote() exercised "
          "live); belief state saved")
    print("open hypotheses remaining:",
          [x['id'] for x in st['hypotheses']
           if x['status'] in ('proposed', 'testing')])
