# APCD K=6 Dimer Phase-Gradient Sanity Check

## Current State

- Current K-dimer setup is a geometry scaffold.
- Each dimer is already represented as a structure group.
- Current geometry does not imply a t_{alpha*<-alpha} phase-gradient.
- No FDTD, RCWA, far-field, or diffraction-order result is reported here.

## APCD Target Channel

The metagrating target channel is `t_{alpha*<-alpha}`, not ordinary x/y, L/R, or total transmission alone.

A useful dimer state must simultaneously provide:

- high `|t_{alpha*<-alpha}|`
- low beta leakage
- prescribed target-channel phase `phi_i`

## Structure-Factor Sanity Check

Using the approximate discrete structure factor

```text
A_m = sum_i a_i * exp(-i 2*pi*m*i/K)
```

uniform identical dimers have `a_i = 1`. For `m = +1` and `m = -1`, the normalized structure factor should be near zero when K > 1. Therefore, the current uniform scaffold alone should not be claimed as a +15 deg directional metagrating.

- uniform_A_plus1_normalized_abs: 5.851389114294502e-17
- uniform_A_minus1_normalized_abs: 5.851389114294502e-17
- plus_ramp_A_plus1_normalized_abs: 1.0
- plus_ramp_A_minus1_normalized_abs: 1.8503717077085943e-16
- minus_ramp_A_plus1_normalized_abs: 2.068778461039394e-16
- minus_ramp_A_minus1_normalized_abs: 1.0

## Required Phase Ramp

- K: 6
- phase_step_deg: 60.0

| dimer_index | x_nm | plus_ramp_phase_deg | minus_ramp_phase_deg |
|---:|---:|---:|---:|
| 0 | -1019.0517467349671 | 0.0 | 0.0 |
| 1 | -611.4310480409802 | 59.99999999999999 | 300.0 |
| 2 | -203.81034934699338 | 119.99999999999999 | 240.00000000000003 |
| 3 | 203.81034934699343 | 180.0 | 180.0 |
| 4 | 611.4310480409804 | 239.99999999999997 | 120.00000000000001 |
| 5 | 1019.0517467349673 | 299.99999999999994 | 60.000000000000036 |

## Sign Convention Caveat

Both plus-ramp and minus-ramp targets are listed because the sign corresponding to the GUI/FDTD +15 deg order must be verified by later diffraction-order extraction. This report does not assert which ramp sign is final.

## Recommended Route

Step B: build diffraction-order / far-field extraction and verify the order sign convention.

Step C: build a dimer phase-state design mechanism, for example dynamic phase through small geometry variants, detour phase / local displacement, or possibly constrained dimer rotation only if the alpha/beta target remains valid.

Global rotation may change the APCD allowed state alpha and should not be used casually as a phase knob.

Step D: find K dimer variants that simultaneously satisfy alpha-pass, beta-suppressed, and the target-channel phase ramp.

## Explicit Non-Goals

- Do not treat the current uniform scaffold as the final metagrating.
- Do not claim +15 deg steering is already achieved.
- Do not start a large sweep from this report.
- Do not switch to TiO2 or 450 nm.
- Do not do ML.
- Do not treat K as the number of individual nanopillars.
