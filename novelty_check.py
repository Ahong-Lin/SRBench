"""
Novelty Check: judge whether an evolved equation is scientifically novel.
=========================================================================

A "Novelty Evaluator" that asks an LLM whether a candidate equation, given its
scientific context, is genuinely novel (must be discovered from data) or is just
a well-known textbook/literature formula that could be recited directly.

Designed to be called from `equation_evolve.py` once an equation has been
evolved a few times (e.g. from generation 5 onward), but it is also a standalone
tool you can run on any equations file:

    export ANTHROPIC_API_KEY="sk-..."

    # Check every equation in a file:
    python novelty_check.py --input outputs/evolutions/evolution_xxx.jsonl

    # Check one equation by id, write augmented output:
    python novelty_check.py --input equations.jsonl --id m2_xxx_000 \
        --output equations.novelty.jsonl

The verdict is a dict {"reasoning": "...", "answer": "Yes"|"No"}:
  answer == "Yes"  -> novel; cannot be directly recited, needs data-driven inference.
  answer == "No"   -> a well-known classical formula (recitable).
For traceability, successful checks also attach `llm_qa_history`, recording the
exact prompt/response history used for the verdict.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import BaseModel

from model_provider import ModelCaller, ModelRequestError, build_model_caller


# ============================================================
# Prompts (kept verbatim per the project spec)
# ============================================================

SYSTEM_PROMPT = """\
You are a top-tier scientist with deep expertise across physics, biology,
chemistry, and materials science. Your task is to act as a "Novelty Evaluator":
objectively judge whether a newly generated mathematical equation is
"scientifically novel" within its given scientific context.

CORE CRITERIA:
- NOT NOVEL: the equation is a well-known classical formula that already exists
  in textbooks, on the internet, or in the open scientific literature — i.e. a
  formula that could be obtained simply by recall/recitation.
- NOVEL: while remaining scientifically sound, the equation introduces uncommon,
  nonlinear, or genuinely new composite mechanism terms, such that neither a
  human nor an AI could guess it from background knowledge alone — it could only
  be recovered through data-driven inference from experimental observations.
"""

USER_PROMPT_TEMPLATE = """\
[SCIENTIFIC CONTEXT]:
Field: {discipline}
Problem description: {problem_description}

[VARIABLES & PARAMETERS]:
- Target variable: {target_line}
- Input features: {input_lines}
- Parameters: {param_lines}

[CANDIDATE EQUATION]:
{candidate_equation}
(Note: this equation comes from an equation-evolution pipeline; assume it is
mathematically solvable and numerically stable.)

[NOTE ON KNOWN / CLASSICAL TERMS]:
{classical_note}

---

REASONING & OUTPUT REQUIREMENTS:
Let's think step by step:
1. Analyze each term in the candidate equation. Which terms are established
   classical knowledge in this scientific context, and which are newly
   introduced composite terms?
2. Drawing on your knowledge of the scientific literature, does this COMPLETE
   combined form of the equation appear directly in any existing textbook or
   public reference? Could a large language model "recite" this exact formula
   purely from the context and variable names above?
3. Assess whether it has true novelty (i.e. it could only be discovered by
   reasoning over subsequent experimental observation data).

Provide your final answer STRICTLY in the following JSON format, with no extra
Markdown markup (no ```json):
{{
  "reasoning": "Write your detailed step-by-step scientific analysis and novelty assessment here.",
  "answer": "Yes" or "No" (write "Yes" if the equation is novel and cannot be directly recited; write "No" if it is a well-known classical formula or can be directly recited)
}}
"""


# ============================================================
# Output schema
# ============================================================

class NoveltyResult(BaseModel):
    reasoning: str
    answer: str


class NoveltyCheckError(RuntimeError):
    """Carry prompt/response history when novelty evaluation fails."""

    def __init__(self, message: str, qa_history: list[dict]):
        super().__init__(message)
        self.qa_history = qa_history


# ============================================================
# Helpers
# ============================================================

def _strip_code_fence(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if present."""
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def _normalize_answer(ans: str) -> str:
    """Coerce free-form Yes/No into a clean 'Yes' / 'No' (else return as-is)."""
    a = (ans or "").strip().lower()
    if a.startswith("y") or a in ("是", "新颖", "true"):
        return "Yes"
    if a.startswith("n") or a in ("否", "不新颖", "false"):
        return "No"
    return ans.strip()


def _describe_variables(eq: dict):
    """Split an equation record into (target, [inputs], [parameters]) using roles."""
    syms = eq.get("symbols", [])
    descs = eq.get("symbol_descriptions", [])
    props = eq.get("symbol_properties", [])
    target, inputs, params = None, [], []
    for i, sym in enumerate(syms):
        role = props[i] if i < len(props) else "?"
        desc = descs[i] if i < len(descs) else ""
        entry = (sym, desc)
        if role == "O":
            target = entry
        elif role == "V":
            inputs.append(entry)
        elif role == "P":
            params.append(entry)
    return target, inputs, params


def _fmt_pairs(pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        return "(none)"
    return "; ".join(f"{sym} ({desc})" if desc else sym for sym, desc in pairs)


def _classical_note(base: dict | None) -> str:
    """Build the 'known/classical terms' block from the base (generation-0) equation."""
    if base and base.get("expression"):
        bt = base.get("target_symbol", "y")
        be = base.get("expression", "")
        return (
            f"The classical / textbook starting point for this phenomenon "
            f"(the baseline equation) is:\n"
            f"  {bt} = {be}\n"
            f"The terms appearing in this baseline equation can be regarded as the "
            f"well-known classical terms for this problem. Use this as the reference "
            f"to judge whether the candidate equation, relative to this classical "
            f"baseline, introduces additional novel composite terms that cannot be "
            f"recited directly and could only be discovered through data-driven "
            f"reasoning."
        )
    return (
        "No baseline equation is provided. Using your knowledge of textbooks and "
        "the open literature, decide for yourself which terms in this problem are "
        "classical/known and which are novel composite terms."
    )


def build_user_prompt(
    candidate: dict,
    discipline: str,
    scenario_text: str,
    base: dict | None = None,
) -> str:
    target, inputs, params = _describe_variables(candidate)
    target_sym = candidate.get("target_symbol", target[0] if target else "y")
    target_line = (
        f"{target[0]} ({target[1]})" if target and target[1]
        else (target[0] if target else target_sym)
    )
    candidate_equation = f"{target_sym} = {candidate.get('expression', '')}"

    return USER_PROMPT_TEMPLATE.format(
        discipline=discipline or "science",
        problem_description=scenario_text or "(no scenario description)",
        target_line=target_line,
        input_lines=_fmt_pairs(inputs),
        param_lines=_fmt_pairs(params),
        candidate_equation=candidate_equation,
        classical_note=_classical_note(base),
    )


# ============================================================
# Core: one novelty check
# ============================================================

def check_novelty(
    caller: ModelCaller,
    candidate: dict,
    discipline: str,
    scenario_text: str,
    model: str = "claude-opus-4-7",
    base: dict | None = None,
    max_retries: int = 3,
    max_tokens: int = 2000,
) -> dict:
    """Ask the LLM whether `candidate` is scientifically novel.

    Returns {"reasoning": str, "answer": "Yes"|"No", "llm_qa_history": list}.
    Raises on repeated API/parse failure (let the caller decide how to record).
    """
    prompt = build_user_prompt(candidate, discipline, scenario_text, base)

    last_err: Exception | None = None
    qa_history: list[dict] = []
    for attempt in range(max_retries + 1):
        raw = ""
        try:
            raw = caller.complete(
                prompt,
                model=model,
                max_tokens=max_tokens,
                system_prompt=SYSTEM_PROMPT,
            )
            if not raw.strip():
                raise ValueError("empty response")
            parsed = json.loads(_strip_code_fence(raw))
            result = NoveltyResult.model_validate(parsed)
            out = result.model_dump()
            out["answer"] = _normalize_answer(out["answer"])
            qa_history.append({
                "attempt": attempt + 1,
                "model": model,
                "system_prompt": SYSTEM_PROMPT,
                "user_prompt": prompt,
                "raw_response": raw,
                "parsed_response": {
                    "reasoning": out["reasoning"],
                    "answer": out["answer"],
                },
            })
            out["llm_qa_history"] = qa_history
            return out
        except (
            ModelRequestError,
            json.JSONDecodeError,
            ValueError,
        ) as e:
            last_err = e
            qa_history.append({
                "attempt": attempt + 1,
                "model": model,
                "system_prompt": SYSTEM_PROMPT,
                "user_prompt": prompt,
                "raw_response": raw,
                "error": f"{type(e).__name__}: {e}",
            })
            if attempt < max_retries:
                print(f"      [novelty] retry {attempt+1}: {type(e).__name__}: {e}",
                      file=sys.stderr, flush=True)
                continue
            raise NoveltyCheckError(
                f"{type(e).__name__}: {e}",
                qa_history=qa_history,
            ) from e
    raise last_err  # pragma: no cover


# ============================================================
# Standalone CLI
# ============================================================

def _load_records(input_path: Path) -> list[dict]:
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")
    if input_path.suffix == ".jsonl":
        records = []
        with input_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
    if input_path.suffix == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else [data]
    raise SystemExit(f"Unsupported input format: {input_path.suffix} (use .jsonl or .json)")


def _eq_id(r: dict) -> str:
    return r.get("scenario_id") or r.get("id") or r.get("base_id") or "equation"


def main() -> None:
    p = argparse.ArgumentParser(
        description="Judge whether equations are scientifically novel (recitable or not)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input", required=True, help="equations/evolution .jsonl or .json")
    p.add_argument("--id", default=None,
                   help="only check the record whose scenario_id/id/base_id matches")
    p.add_argument("--discipline", default=None,
                   help="discipline label (default: inferred from record, else 'science')")
    p.add_argument("--model", default="claude-opus-4-7")
    p.add_argument("--provider", choices=["anthropic", "openrouter"],
                   default="anthropic",
                   help="Model API protocol. OpenRouter uses /chat/completions")
    p.add_argument("--base-url", default=None,
                   help="Provider base URL. Defaults to the selected provider's environment value")
    p.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"],
                   default="auto",
                   help="auto prefers ANTHROPIC_API_KEY then ANTHROPIC_AUTH_TOKEN")
    p.add_argument("--output", default=None,
                   help="write records with an added 'novelty' field to this .jsonl")
    args = p.parse_args()

    input_path = Path(args.input)
    records = _load_records(input_path)
    usable = [r for r in records if r.get("expression")]
    if not usable:
        raise SystemExit(f"No records with an 'expression' field in {input_path}")

    # Map base_id -> generation-0 record, so evolved rows get a classical anchor.
    base_map = {r.get("base_id"): r for r in records if r.get("generation") == 0}

    if args.id:
        selected = [r for r in usable
                    if args.id in (r.get("scenario_id"), r.get("id"), r.get("base_id"))]
        if not selected:
            raise SystemExit(f"No record matches id '{args.id}'.")
    else:
        selected = usable

    caller = build_model_caller(
        args.provider,
        base_url=args.base_url,
        auth_source=args.auth_source,
    )

    n_yes = 0
    for i, r in enumerate(selected, 1):
        discipline = args.discipline or r.get("discipline") or "science"
        scenario_text = r.get("scenario_text", "")
        base = base_map.get(r.get("base_id")) if r.get("generation") else None
        if base is r:  # a gen-0 record is its own base — no anchor
            base = None

        print(f"\n[{i}/{len(selected)}] {_eq_id(r)}  "
              f"(gen {r.get('generation', '?')})", file=sys.stderr, flush=True)
        print(f"    {r.get('target_symbol','?')} = {r.get('expression','')}",
              file=sys.stderr)
        try:
            verdict = check_novelty(
                caller=caller,
                candidate=r,
                discipline=discipline,
                scenario_text=scenario_text,
                model=args.model,
                base=base,
            )
        except Exception as e:
            print(f"    FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            verdict = {"answer": "ERROR", "reasoning": f"{type(e).__name__}: {e}"}
            qa_history = getattr(e, "qa_history", None)
            if qa_history:
                verdict["llm_qa_history"] = qa_history
        r["novelty"] = verdict
        if verdict.get("answer") == "Yes":
            n_yes += 1
        print(f"    -> novel? {verdict.get('answer')}", file=sys.stderr)

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Novelty: {n_yes}/{len(selected)} judged NOVEL (Yes).", file=sys.stderr)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for r in selected:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Wrote augmented records to {out_path}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()
