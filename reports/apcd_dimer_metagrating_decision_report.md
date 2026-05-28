# APCD Dimer Metagrating Decision Report

Date: 2026-05-28

## Data Inventory

Requested output locations:

- `outputs/apcd_single_dimer_633nm/`
- `outputs/apcd_single_dimer_sweep_633nm/`
- `outputs/apcd_single_dimer_tio2_633nm/`
- `outputs/apcd_k6_metagrating_633nm/`
- `outputs/apcd_k7_metagrating_633nm/`

Available evidence:

- `outputs/apcd_single_dimer_633nm/results.csv`
- `outputs/apcd_single_dimer_633nm/summary.md`

The available single-dimer files are dry-run outputs only. They do not contain physical simulation results.

Missing evidence:

- No completed `apcd_single_dimer_sweep_633nm` output was found.
- No completed `apcd_single_dimer_tio2_633nm` output was found.
- No completed `apcd_k6_metagrating_633nm` output was found.
- No completed `apcd_k7_metagrating_633nm` output was found.

Server check:

- No `outputs/apcd*` result directory was found on the server at the time of this report.

Therefore, all physics decisions below are limited by missing completed simulations.

## 1. Single-Dimer Result

Question:

```text
Does APCD-like spin-selective conversion work at 633 nm?
```

Answer:

```text
Inconclusive.
```

Reason:

The only available single-dimer result is a dry-run file:

```text
status = dry_run
note = single APCD dimer setup only; lumapi was not imported
```

No completed FDTD / RCWA result is available for the APCD-like c-Si / Al2O3 single dimer.

Baseline geometry prepared in the config, not validated by simulation:

| Parameter | Value |
| --- | --- |
| wavelength | 633 nm |
| substrate | Al2O3 |
| meta material | c-Si |
| period_x | 340 nm |
| period_y | 340 nm |
| height | 300 nm |
| nanopillar_1 | 130 nm x 70 nm |
| nanopillar_2 | 150 nm x 85 nm |

Best geometry:

```text
No best geometry is available from physical results.
```

Metrics:

| Metric | Value |
| --- | --- |
| target_conversion | unavailable |
| opposite_spin_leakage | unavailable |
| spin_ER_dB | unavailable |

Gate 1 status:

```text
Not passed. No physical result is available.
```

## 2. TiO2 Feasibility

Question:

```text
Does TiO2 show meaningful APCD-like behavior at 633 nm?
```

Answer:

```text
Inconclusive.
```

Reason:

No `outputs/apcd_single_dimer_tio2_633nm/` result was found. TiO2 feasibility has not been simulated.

Blue-scaling risk:

```text
HIGH, due to absence of TiO2 feasibility evidence.
```

This is a risk classification from missing evidence, not from a demonstrated TiO2 physics failure.

## 3. K=6 Result

Question:

```text
Does the K=6 APCD-dimer metagrating achieve LCP_in -> RCP_out, +15 deg?
```

Answer:

```text
Inconclusive.
```

Reason:

No `outputs/apcd_k6_metagrating_633nm/` result was found.

Metrics:

| Metric | Value |
| --- | --- |
| eta_target | unavailable |
| eta_leak | unavailable |
| DCP_plus15 | unavailable |
| directionality | unavailable |
| wrong_orders | unavailable |

K=6 should not be judged until Gate 1 passes and K=6 simulation outputs exist.

## 4. K=7 Result

Question:

```text
Does the K=7 APCD-dimer metagrating achieve LCP_in -> RCP_out, +15 deg?
```

Answer:

```text
Inconclusive.
```

Reason:

No `outputs/apcd_k7_metagrating_633nm/` result was found.

Metrics:

| Metric | Value |
| --- | --- |
| eta_target | unavailable |
| eta_leak | unavailable |
| DCP_plus15 | unavailable |
| directionality | unavailable |
| wrong_orders | unavailable |

K=7 should not be judged until Task 4 structure generation and evaluation scripts work.

## 5. K=6 vs K=7 Conclusion

Question 1:

```text
Which K has higher eta_target?
```

Answer:

```text
Inconclusive. No K=6 or K=7 result is available.
```

Question 2:

```text
Which K has lower leakage?
```

Answer:

```text
Inconclusive. No K=6 or K=7 leakage result is available.
```

Question 3:

```text
Which K has better DCP at +15 deg?
```

Answer:

```text
Inconclusive. No K=6 or K=7 DCP result is available.
```

Question 4:

```text
Is K=7 degraded by stronger inter-dimer coupling?
```

Answer:

```text
Inconclusive. There is no K=7 simulation result.
```

Question 5:

```text
Should we continue with K=6, K=7, or pause the APCD-metagrating route?
```

Answer:

```text
Pause K=6 / K=7 metagrating construction until the single-dimer Gate 1 result exists.
```

## 6. Decision

Chosen decision:

```text
D. Pause and redesign dimer physics.
```

Interpretation:

This does not mean APCD dimer physics has failed. It means the project should pause supercell construction and return to single-dimer validation only, because no completed physical Gate 1 result is available.

Supporting evidence:

- The available `apcd_single_dimer_633nm` output is dry-run only.
- No single-dimer sweep result exists.
- No TiO2 feasibility result exists.
- No K=6 result exists.
- No K=7 result exists.
- Earlier attempts to run the single-dimer FDTD baseline timed out before producing output.

## 7. Next Recommended Task

Because the decision is D:

```text
Return to single-dimer design only.
```

Recommended next steps:

1. Add a setup-only path for the APCD single dimer runner and save a `.fsp` file for GUI inspection.
2. Inspect source placement, monitor placement, boundary conditions, simulation span, and material settings in Lumerical.
3. Reduce the single-dimer model to the smallest reliable 633 nm validation case.
4. Re-run Gate 1 c-Si / Al2O3 single dimer.
5. Only if Gate 1 passes, proceed to a small dimer parameter sweep.
6. Only after a working c-Si / Al2O3 reference exists, test TiO2 feasibility.
7. Only after dimer physics is validated, build K=6 and K=7 metagratings.

Do not start DenseNet or cVAE.

Do not generate a large dataset.

Do not proceed to K=6 / K=7 supercells before Gate 1 passes.
