# Task contract

The reusable implementation lives in `src/srbench/packaging/`, `common/prediction.py` and `plotting/`. The skill orchestrates these modules; it has no second copy of the generator, template or plot code.

## Inputs and outputs

For `evaluate_explicit`, features are the declared independent variables and the target is `dependent_variable`. Parameters remain fixed unless the evolved spec explicitly promoted them into an input role.

For `integrate_system`, features are the time coordinate and all declared state variables. The target is `benchmark_output`, the RHS of `benchmark_target_state`. A state trajectory is not the same target as its derivative. ODE states are obtained by integrating the closed system from its original initial conditions.

Packaging supports any input dimension within the numerical sampler's limits. This does not imply every legacy integrator can be turned into a memoryless regression task. DDE, Basset/history integrators and ambiguous implicit branches are explicitly unsupported by this packaging interface.

The model implements `law(rows)` and returns one finite float or `{target: value}` per row. The verifier sends one row at a time in shuffled order. Each call runs in a fresh fork of the imported module, so mutable cross-row state is reset. Local plotting uses the same runner and metrics; it is process isolation, not a security sandbox.

## Spatial split

For one input, normalize its declared range to `[0, 1]`; apply log10 first for a log axis. Training owns `u <= 0.9`, hidden test owns `u > 0.9`.

For d static inputs, normalize each coordinate. Define `c = 1 - 0.1**(1/d)`. The hidden corner has `u_j > c` for every j; training is its complement. The hidden volume is `(1-c)**d = 0.1`. Individual coordinate ranges overlap. This tests extrapolation into a withheld joint region, not beyond every marginal training range. Sobol provides coverage inside those regions; it does not define their ordering.

For an ODE, apply the one-dimensional rule to time. Integrate from the original initial time for both requested output grids; do not restart the system at the test boundary. Do not independently draw arbitrary state combinations.

The spatial split remains 90%/10% if point counts are changed. Both point counts and spatial fractions are recorded. Provided CSVs instead retain their original split and are labelled `provided`.

## Package layout and truth

```text
task_name/
  manifest.json
  ground_truth.json
  split_manifest.json
  task/
    instruction.md
    task.toml
    environment/{Dockerfile,train_data.csv}
    tests/{test.sh,test_outputs.py,contract.json,prediction.py,metrics.py,test_data.csv}
    solution/{solve.sh,reference_law.py,explain.md}
```

All artifact links in the manifest are relative. Ground truth includes the complete spec, so deleting the original generation checkpoints does not break plotting.

Training and hidden test targets are exact formula outputs. Packaging sets legacy `noise` to zero and ignores `_noisy` columns; it preserves formula, parameters, domain and initial conditions. Provided CSV labels must agree with the formula. The reference must reproduce both partitions with R² approximately 1 when the metric is defined.

Generation does not use `excitation_check` or `auto_balance`. Its data-quality screen rejects ODE targets that become flat in the sampled terminal window: both the last 20% range / whole range and the shift between the last two 20% window medians / whole range must be below 0.02. This screen uses clean target values. Static Sobol samples have no temporal ordering and are not screened for terminal convergence.

Metrics use raw R², RMSE, MAE, variance, NMSE and NMAE. R² is undefined for near-constant labels under the inherited verifier convention (`variance < 1e-12` or `MAD < 1e-12`); package creation fails clearly rather than silently changing the equation or split. Execution failures record `raw_r2: null` and a failure status, while Harbor writes its failure reward of `-1`.
