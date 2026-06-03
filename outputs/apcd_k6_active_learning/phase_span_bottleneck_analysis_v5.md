# APCD K=6 Phase-Span Bottleneck Analysis v5

Scope: 09-P33/P35 accumulated diagnosis only. No FDTD/lumapi/.fsp/YAML/training was run or generated in this stage. No phase-ramp supercell was built.

Usable phase span: 72.24132809604521 to 118.07875127181353 deg.
Usable 60-120 deg count: 16 of 16 early-pass rows.
Usable negative-phase count: 0.

Coverage v5:
- `0` deg: `evidence_only`
- `60` deg: `early_covered`
- `120` deg: `strong_covered`
- `-180` deg: `evidence_only`
- `-120` deg: `open_gap`
- `-60` deg: `open_gap`

Diagnosis: the current APCD dimer family produces many low-leakage usable states between roughly 60 and 120 deg, but attempts to move to 0 deg, negative bins, or pi-wrap usually fail by leakage/ratio or return to positive phase.

Failure modes:
- phase-near target but leakage high: 0 deg and pi-wrap evidence points exist, but leakage/ratio fail.
- early-pass but not target: some negative-bin candidates remain optically good but sit near positive phase.
- phase-wrap evidence but leakage high: `pl_pi_wrap_04` is close to -180 deg but not usable.
- negative target pulled back to positive phase: -60 redesign repeatedly returns near 80-100 deg.

The K=6 phase-state library remains incomplete. This is not a +15 deg steering proof.
