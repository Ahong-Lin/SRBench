# Discover the governing function

Infer a formula from `/app/data/train_data.csv` and implement it in `/app/law.py`.
The CSV contains 4500 training rows with exact formula outputs without observation noise.
dv_dt is the instantaneous time derivative of state v. Inputs contain time and observed states along a trajectory.

Input features, in their declared roles:

- t: time.
- x: observed dynamical state; use its value in each input row.
- v: observed dynamical state; use its value in each input row.
- internal_loss_level: observed dynamical state; use its value in each input row.
- loss_activation_level: observed dynamical state; use its value in each input row.

The target column is `dv_dt`. Infer the governing relationship from the supplied training observations. The evaluator independently tests the submitted function on hidden observations.

Implement `law(rows)`. Each row is a dictionary with numeric keys t, x, v, internal_loss_level, loss_activation_level.
Return one finite prediction per row, as a list of floats or dictionaries with key `dv_dt`.
The verifier evaluates 500 hidden rows in shuffled order, calling `law([row])` in a fresh child process each time. Predictions must depend on the supplied row, without cross-row state, access to hidden labels, or assumptions about row order.

Use the training data to fit the formula's parameters. Save a concise explanation of the formula and fitting method in `/app/explain.md`.
The score is raw, unclipped R² on hidden labels. Invalid predictions or execution failures fail verification.
