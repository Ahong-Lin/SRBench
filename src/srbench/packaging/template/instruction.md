# Discover the governing function

Infer a formula from `/app/data/train_data.csv` and implement it in `/app/law.py`.
The CSV contains {{TRAIN_POINTS}} training rows with {{LABEL_DESCRIPTION}}.
{{TARGET_DESCRIPTION}}

Input features, in their declared roles:

{{VARIABLES}}

The target column is `{{TARGET}}`. {{REGION}}

Implement `law(rows)`. Each row is a dictionary with numeric keys {{FEATURES}}.
Return one finite prediction per row, as a list of floats or dictionaries with key `{{TARGET}}`.
The verifier evaluates {{TEST_POINTS}} hidden rows in shuffled order, calling `law([row])` in a fresh child process each time. Predictions must depend on the supplied row, without cross-row state, access to hidden labels, or assumptions about row order.

Use the training data to fit the formula's parameters. Save a concise explanation of the formula and fitting method in `/app/explain.md`.
The score is raw, unclipped R² on hidden labels. Invalid predictions or execution failures fail verification.
