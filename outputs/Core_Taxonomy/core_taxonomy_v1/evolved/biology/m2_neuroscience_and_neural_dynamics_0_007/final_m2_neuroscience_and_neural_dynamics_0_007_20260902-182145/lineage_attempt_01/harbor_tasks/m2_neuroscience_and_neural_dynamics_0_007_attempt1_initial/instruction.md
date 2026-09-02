You have to analyze an experimental dataset to discover the underlying mathematical relationship that governs it.
The training dataset is located at `/app/data/train_data.csv` and can be loaded using `pandas.read_csv()`.

The experimental context: This is a symbolic regression task from the biology domain. A group of coupled neural oscillators receives increasing coupling strength and their collective phase alignment is assessed at steady state. Below a critical coupling the phases remain scattered, while above it a macroscopic fraction locks into synchrony that grows with coupling. We measure the synchronization order as a function of coupling strength. This captures the onset of collective phase locking.
The goal is to discover a closed-form mathematical expression that predicts `r` from the observed input variables.

The dataset columns are:
- `K`: input variable
- `r`: output variable (the value you must predict)

You must produce two files:

1. A Python function in `/app/law.py` named `law` with this signature. The
verifier supplies exactly one row per call:

```python
def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    # Compute one {"r": prediction} dict from this row only.
    return [{"r": prediction}]
```

2. A detailed explanation in `/app/explain.md` describing the discovered formula,
methodology, and fitted parameters.

## Required solution style

The scientific target is `r`. Express it as an explicit, interpretable
pointwise function of the listed variables.

Implement the discovered relationship in `/app/law.py`; `law` is the submitted
answer. It must map each input row independently to one `r` prediction.
Do not use a machine-learning black box, fitted lookup table, interpolation,
sequence/trajectory processing, numerical differentiation, file reads,
hidden-data access, input ordering, or state carried between calls. The
relationship may use only the declared variables (K) and fixed
constants/parameters inferred from the training data.

The hidden verifier calls `law([row])` with exactly one row at a time, in random
order, and in a fresh process for each row. It checks the returned `r`
value against the reference value for that row. Return a list containing exactly
one dictionary with key `r`.
