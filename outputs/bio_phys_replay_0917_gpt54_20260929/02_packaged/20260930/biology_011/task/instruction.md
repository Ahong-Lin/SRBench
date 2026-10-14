# Discover the governing function

Infer a formula from `/app/data/train_data.csv` and implement it in `/app/law.py`.
The CSV contains 4500 training rows with exact formula outputs without observation noise.
dD_dt is the instantaneous time derivative of state D. Inputs contain time and observed states along a trajectory.

Input features, in their declared roles:

- t: time.
- D: observed dynamical state; use its value in each input row.
- recombination_rate: observed dynamical state; use its value in each input row.
- occupancy_buffer: observed dynamical state; use its value in each input row.
- refractory_occupancy: observed dynamical state; use its value in each input row.

The target column is `dD_dt`. Infer the governing relationship from the supplied training observations. The evaluator independently tests the submitted function on hidden observations.

Implement `law(rows)`. Each row is a dictionary with numeric keys t, D, recombination_rate, occupancy_buffer, refractory_occupancy.
Return one finite prediction per row, as a list of floats or dictionaries with key `dD_dt`.
The verifier evaluates 500 hidden rows in shuffled order, calling `law([row])` in a fresh child process each time. Predictions must depend on the supplied row, without cross-row state, access to hidden labels, or assumptions about row order.

Use the training data to fit the formula's parameters. Save a concise explanation of the formula and fitting method in `/app/explain.md`.
The score is raw, unclipped R² on hidden labels. Invalid predictions or execution failures fail verification.
