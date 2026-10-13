"""Syntax shared by formula checks and the numeric/SymPy parsers."""
import ast
import re


CONDITION_FUNCTIONS = frozenset({"Eq", "Ne", "Lt", "Le", "Gt", "Ge", "And", "Or", "Not"})


def validate_condition_functions(expression: str) -> None:
    """Validate expression syntax and restrict predicates to Piecewise conditions.

    A call such as Eq(rate, 0) is a valid branch condition. An outer Eq(y, rhs)
    is an equation object rather than the scalar expression the pipeline needs.
    This check does not evaluate or rewrite a formula.
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"invalid expression syntax: {exc.msg}") from exc
    called = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", expression))
    if not called & CONDITION_FUNCTIONS:
        return
    condition_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Piecewise":
            for branch in node.args:
                if isinstance(branch, ast.Tuple) and len(branch.elts) == 2:
                    condition_nodes.update(id(item) for item in ast.walk(branch.elts[1]))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in CONDITION_FUNCTIONS and id(node) not in condition_nodes):
            raise ValueError(
                f"{node.func.id} is allowed only inside a Piecewise condition; "
                "expression/RHS must be numeric, not Eq(target, rhs) or a Boolean predicate."
            )
