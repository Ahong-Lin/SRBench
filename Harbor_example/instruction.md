You have to analyze an experimental dataset to discover the underlying mathematical relationship that governs it.
The training dataset is located at `/app/data/train_data.csv` and can be loaded using `pandas.read_csv()`.

The experimental context: This is a symbolic regression task from the biology domain. The goal is to discover a closed-form mathematical expression that predicts the output variable `X` based on the input variables `t` and `I_light_prev`.

The dataset columns are:
- `t`: input variable
- `I_light_prev`: input variable
- `X`: output variable (the value you must predict)

You must produce two files:

1. A Python function in `/app/law.py`
This file must contain a single function named `law` with the following signature. This function should embody your discovered mathematical formula.

```python
def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    # The verifier supplies exactly one row in input_data per call.
    row = input_data[0]
    # Compute one explicit prediction from that row only.
    return [{"X": prediction}]
```

2. A detailed explanation in `/app/explain.md`
This Markdown file should explain:
    * The mathematical formula you discovered.
    * Your reasoning and the methodology used to find the law.
    * The fitted values of the parameters/coefficients.

The hidden verifier calls `law([row])` one row at a time, in random order, in
fresh processes. It checks each returned value against the hidden reference and
then aggregates the pointwise errors into R². Do not assume that multiple rows
are available in a call.

**IMPORTANT — save early and often:** Write a runnable `/app/law.py` as soon as you have any working formula, even a rough first version, and then keep refining it in place. Do NOT wait until you have found the perfect formula before writing the file. At all times, `/app/law.py` should contain your current best working version, so that a valid answer exists even if you run out of time.
