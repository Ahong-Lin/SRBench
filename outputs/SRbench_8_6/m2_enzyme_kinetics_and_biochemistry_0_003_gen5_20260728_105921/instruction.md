You have to analyze an experimental dataset to discover the underlying mathematical relationship that governs it.
The training dataset is located at `/app/data/train_data.csv` and can be loaded using `pandas.read_csv()`.

The experimental context: This is a symbolic regression task from the enzyme kinetics and biochemistry domain. The goal is to discover a mathematical expression that predicts the output variable `k_turn` based on the input variables 'pH', 'temperature', 'ionic_strength'.

The dataset columns are:
- `pH`: input variable
- `temperature`: input variable
- `ionic_strength`: input variable
- `k_turn`: output variable

You must produce two files:

1. A Python function in `/app/law.py`
This file must contain a single function named `law` with the following signature. This function should embody your discovered mathematical formula.

```python
def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a discovered law.

    Args:
        input_data: A list of dictionaries, where each dictionary is a single data
                    point containing the input variable names ('pH', 'temperature', 'ionic_strength') as keys
                    and their corresponding values.

    Returns:
        A list of dictionaries, corresponding to the input_data list, with each
        dictionary containing the predicted output variable, e.g. {"k_turn": value}.
    """
    # Your implementation here
    pass
```

2. A detailed explanation in `/app/explain.md`
This Markdown file should explain:
    * The mathematical formula you discovered.
    * Your reasoning and the methodology used to find the law.
    * The fitted values of the parameters/coefficients.

Your submitted `law` function will be tested on the right-hand extrapolation segment of the dataset.
