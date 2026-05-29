# APCD K=7 Dimer Phase-Gradient Sanity Check

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

- uniform_A_plus1_normalized_abs: 2.242989226691107e-17
- uniform_A_minus1_normalized_abs: 2.242989226691107e-17
- plus_ramp_A_plus1_normalized_abs: 1.0
- plus_ramp_A_minus1_normalized_abs: 9.24808149876991e-17
- minus_ramp_A_plus1_normalized_abs: 4.7580986769649563e-17
- minus_ramp_A_minus1_normalized_abs: 1.0

## Required Phase Ramp

- K: 7
- phase_step_deg: 51.42857142857143

| dimer_index | x_nm | plus_ramp_phase_deg | minus_ramp_phase_deg |
|---:|---:|---:|---:|
| 0 | -1048.1675109273947 | 0.0 | 0.0 |
| 1 | -698.7783406182632 | 51.42857142857143 | 308.57142857142856 |
| 2 | -349.38917030913154 | 102.85714285714286 | 257.14285714285717 |
| 3 | -5.684341886080802e-14 | 154.28571428571428 | 205.71428571428572 |
| 4 | 349.38917030913166 | 205.71428571428572 | 154.28571428571428 |
| 5 | 698.7783406182634 | 257.14285714285717 | 102.85714285714286 |
| 6 | 1048.1675109273947 | 308.57142857142856 | 51.42857142857143 |

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
