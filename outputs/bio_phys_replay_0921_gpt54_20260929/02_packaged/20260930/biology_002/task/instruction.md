# Discover the governing function

Infer a formula from `/app/data/train_data.csv` and implement it in `/app/law.py`.
The CSV contains 4500 training rows with exact formula outputs without observation noise.
H_g is the response to independently sampled experimental conditions.

Input features, in their declared roles:

- H0: independent input.
- Ne: independent input.
- g: independent input.
- mu: independent input.

The target column is `H_g`. Infer the governing relationship from the supplied training observations. The evaluator independently tests the submitted function on hidden observations.

Implement `law(rows)`. Each row is a dictionary with numeric keys H0, Ne, g, mu.
Return one finite prediction per row, as a list of floats or dictionaries with key `H_g`.
The verifier evaluates 500 hidden rows in shuffled order, calling `law([row])` in a fresh child process each time. Predictions must depend on the supplied row, without cross-row state, access to hidden labels, or assumptions about row order.

Use the training data to fit the formula's parameters. Save a concise explanation of the formula and fitting method in `/app/explain.md`.
The score is raw, unclipped R² on hidden labels. Invalid predictions or execution failures fail verification.
