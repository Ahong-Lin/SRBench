import unittest

import pandas as pd

from srbench.generation.response_diagnostics import mechanism_coverage, parent_absorption


class ResponseDiagnosticsTests(unittest.TestCase):
    def test_coverage_marks_visible_and_extended_group(self):
        spec = {
            "parameters": [{"symbol": "K", "value": 2.0}],
            "mechanism_observation_history": [{
                "generation": 1,
                "contract": {"diagnostic_groups": [{
                    "name": "scaled_input", "expression": "x/K", "role": "scale"
                }]},
            }],
        }
        train = pd.DataFrame({"x": [0.1, 1.0, 2.0]})
        hidden = pd.DataFrame({"x": [3.0, 4.0]})
        report = mechanism_coverage(spec, train, hidden)
        self.assertEqual(report["groups"][0]["train_status"], "visible")
        self.assertEqual(report["groups"][0]["hidden_status"], "extended")

    def test_parent_absorption_returns_deterministic_error_or_metric(self):
        spec = {"parameters": [{"symbol": "a", "value": 1.0}]}
        parent = {"expression": "a*x", "symbols": ["y", "x", "a"],
                  "symbol_properties": ["O", "V", "P"]}
        child = {"expression": "a*x + b*x**2"}
        train = pd.DataFrame({"x": [0.0, 1.0], "y": [0.0, 1.0]})
        hidden = pd.DataFrame({"x": [2.0, 3.0], "y": [4.0, 9.0]})
        report = parent_absorption(parent, child, spec, train, hidden)
        self.assertIn(report["status"], {"ok", "error"})


if __name__ == "__main__":
    unittest.main()
