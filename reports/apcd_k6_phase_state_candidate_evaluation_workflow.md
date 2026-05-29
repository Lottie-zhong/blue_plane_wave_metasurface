# APCD K6 Phase-State Candidate Evaluation Workflow



## 1. Purpose



This document defines the minimal evaluation workflow for K=6 APCD dimer phase-state candidates.



This is a planning and workflow document only.



It is not an FDTD run.  

It is not an `.fsp` export.  

It is not a K=7 study.  

It is not a sweep.  

It is not a phase-ramp supercell result.  

It is not evidence of +15 deg steering.



## 2. Current basis



The current project has completed:



- Phase 1 APCD alpha-pass single dimer Gate 1.

- K=6/K=7 scaffold and setup-only export.

- K=6 uniform diagnostic run.

- Complex `gratingvector("T")` extraction.

- Order-resolved Jones construction.

- Alpha/beta to alpha*/beta* basis transform.

- K=6 phase-state design plan.

- K=6 phase-state library schema.

- K=6 minimal candidate route.



The current minimal candidate route contains 13 variants:



- baseline

- p1L_m10

- p1L_m5

- p1L_p5

- p1L_p10

- p1W_m5

- p1W_p5

- p2L_m5

- p2L_p5

- p2W_m10

- p2W_m5

- p2W_p5

- p2W_p10



All candidates are one-factor-at-a-time geometry variants.



## 3. Baseline alpha-pass geometry



The baseline APCD alpha-pass dimer is:



pillar 1:



- length = 130 nm

- width = 70 nm

- rotation = 67.5 deg



pillar 2:



- length = 85 nm

- width = 150 nm

- rotation = 112.5 deg



The original beta-selective pillar 2 geometry, 150 x 85 nm, must not be used as the baseline.



## 4. Evaluation target



Each candidate should eventually be evaluated in the APCD target channel:



`t_{alpha*<-alpha}`



The evaluation must be performed in the alpha/beta input basis and alpha*/beta* output basis.



The main desired properties are:



1. high `|t_{alpha*<-alpha}|`

2. low beta leakage

3. useful phase variation in `arg(t_{alpha*<-alpha})`

4. small phase error relative to the target phase state



The target K=6 phase states are:



plus ramp:



- 0 deg

- 60 deg

- 120 deg

- 180 deg

- 240 deg

- 300 deg



minus ramp:



- 0 deg

- -60 deg

- -120 deg

- -180 deg

- -240 deg

- -300 deg



The current phase convention is `\[-180, 180)`.



## 5. Minimal evaluation sequence



### Step A: candidate setup-only export



For each candidate dimer geometry, export a single-dimer setup-only `.fsp`.



Do not run FDTD during setup export.



The setup should preserve the Phase 1 single-dimer environment as much as possible:



- wavelength = 633 nm

- c-Si nanopillars

- Al2O3 substrate

- period close to the APCD baseline

- normal incidence

- x/y input capability

- T and T_fields monitors



### Step B: single-candidate diagnostic run



For each candidate, run two input polarizations:



- x-polarized input

- y-polarized input



Use the stable lifecycle:



setup / save  

鈫?close  

鈫?load  

鈫?run  

鈫?extract  

鈫?close



Do not call `switchtolayout` after `fdtd.run()`.



### Step C: construct candidate Jones matrix



Use the x/y runs to construct:



```text

J_xy =

\[\[Ex_x, Ex_y],

&#x20;\[Ey_x, Ey_y]]


