# K=6 Diagnostic Gratingvector Jones Extraction Note

## Scope

This note documents the K=6 uniform scaffold diagnostic extraction fix.

It only covers complex diffraction-order vector extraction and order-resolved Jones construction for the K=6 uniform scaffold. It is not a K=7 run, not a sweep, not a phase-ramp design, and not a final metagrating result.

## Evidence

- Diagnostic script: `scripts/19_run_apcd_k6_uniform_diffraction_diagnostic.py`
- Extraction code: `src/metasurface/apcd_diffraction.py`
- Run log: `outputs/apcd_k6_metagrating_633nm/diagnostic_uniform_run/run_log.txt`
- Summary: `outputs/apcd_k6_metagrating_633nm/diagnostic_uniform_run/diagnostic_summary.md`
- Order-resolved Jones table: `outputs/apcd_k6_metagrating_633nm/diagnostic_uniform_run/order_resolved_jones.csv`

The real K=6 run reports:

```text
X: gratingvector('T',) returned type=ndarray, shape=(7, 1, 3), dtype=complex128
X: gratingvector normalized to order-vector rows=7
X: gratingvector complex extraction success
Y: gratingvector('T',) returned type=ndarray, shape=(7, 1, 3), dtype=complex128
Y: gratingvector normalized to order-vector rows=7
Y: gratingvector complex extraction success
order-resolved Jones construction success
```

## Gratingvector Return Format

For monitor `T`, Lumerical returned:

```text
shape = (7, 1, 3)
dtype = complex128
```

Interpretation used in the diagnostic:

- Axis 0: diffraction-order row index.
- Axis 1: singleton dimension for this run.
- Axis 2: Cartesian complex vector component, ordered as `(Ex, Ey, Ez)`.

The extraction code converts this array into seven per-order vectors by reshaping the array to:

```text
(7, 3)
```

Each row is then interpreted as:

```text
order_vector_i = (Ex_i, Ey_i, Ez_i)
```

The order labels are not inferred from the vector array alone. They are paired by row index with:

```text
gratingn("T")
gratingm("T")
gratingu1("T")
gratingu2("T")
grating("T")
transmission("T")
```

Thus, for each row `i`:

```text
order_n_i = gratingn("T")[i]
order_m_i = gratingm("T")[i]
u1_i      = gratingu1("T")[i]
u2_i      = gratingu2("T")[i]
Ex_i,Ey_i,Ez_i = gratingvector("T")[i,0,:]
```

## Mapping To Order-Resolved Ex/Ey/Ez

The resulting order-resolved fields are written to:

```text
diffraction_orders_X.csv
diffraction_orders_Y.csv
```

For each order row, the relevant complex field columns are:

```text
Ex_order_complex_real
Ex_order_complex_imag
Ey_order_complex_real
Ey_order_complex_imag
Ez_order_complex_real
Ez_order_complex_imag
```

The `diffraction_orders_X.csv` table stores the complex output vector for X-polarized input. The `diffraction_orders_Y.csv` table stores the complex output vector for Y-polarized input.

## Constructing J_xy From X/Y Inputs

For a given diffraction order, the diagnostic combines two linear-input simulations:

```text
X input -> (Ex_x, Ey_x)
Y input -> (Ex_y, Ey_y)
```

The order-resolved Jones matrix in the linear basis is:

```text
J_xy = [[Ex_x, Ex_y],
        [Ey_x, Ey_y]]
```

The diagnostic scales each column by the square root of the corresponding total transmission:

```text
X column scale = sqrt(total_transmission_X)
Y column scale = sqrt(total_transmission_Y)
```

This gives a source-normalized amplitude matrix while preserving the complex phase from `gratingvector("T")`.

## Alpha/Beta Basis Transform

The project alpha/beta basis uses:

```text
psi_deg = 112.5
chi_deg = 22.5
```

The code constructs:

```text
input basis  = (alpha, beta)
output basis = (alpha*, beta*)
```

For each input basis vector, the linear-basis output is first computed:

```text
E_out_xy = J_xy @ E_in_xy
```

Then it is projected onto the output basis:

```text
J_alpha_beta[o,i] = <output_basis_o, E_out_xy>
```

The resulting matrix convention is:

```text
J_alpha_beta[0,0] = t_alpha_star_from_alpha
J_alpha_beta[1,0] = t_beta_star_from_alpha
J_alpha_beta[0,1] = t_alpha_star_from_beta
J_alpha_beta[1,1] = t_beta_star_from_beta
```

These values are written to:

```text
order_resolved_jones.csv
```

## Current K=6 Uniform Result

The current source-normalized target-channel metrics are:

| order_n | target_conversion | beta_to_target_leakage | target_order_ER_dB |
|---:|---:|---:|---:|
| -1 | 7.688278874009688e-06 | 3.937129619464333e-06 | 2.906493611148719 |
| 0 | 0.9332337316784515 | 0.0034674988277662313 | 24.299741049028263 |
| 1 | 3.972795835307968e-06 | 1.577187399463742e-06 | 4.012127821656683 |

The corresponding target amplitudes are:

| order_n | t_alpha_star_from_alpha |
|---:|---:|
| -1 | -0.0015328906137444703 + 0.0023105248841559334j |
| 0 | 0.745753733408786 + 0.6140725533561231j |
| 1 | -0.0015037201492974106 + 0.0013082895504837378j |

## Conclusion

The K=6 diagnostic extraction/Jones pipeline is now fixed:

```text
complex gratingvector extraction: success
order-resolved Jones construction: success
```

The uniform scaffold still has very weak `m = +/-1` target-channel response. The current result validates the extraction and Jones-analysis pipeline only.

It is not evidence of successful `+15 deg` steering and must not be reported as a final APCD metagrating result.
