"""Shared structural vocabulary and taxonomy-aware mechanism profiles.

The ontology describes *how* a mechanism changes an equation.  Taxonomy
profiles describe *which* mechanisms are scientifically plausible in a
subfield.  Keeping those layers separate lets the same evolution machinery
serve physics, biology, economics, and AI scaling laws without pretending
that one domain-specific concept applies everywhere.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ONTOLOGY_PATH = ROOT / "taxonomy" / "mechanism_ontology_v1.json"
TAXONOMY_PATH = ROOT / "taxonomy" / "subfield_taxonomy_v1.json"

_SUBJECT_FALLBACKS: dict[str, list[dict[str, Any]]] = {
    "physics": [
        {"id": "nonlinear_constitutive_response", "description": "nonlinear constitutive or response law", "operations": ["add_term", "change_assumption"]},
        {"id": "coupled_field_or_force", "description": "coupling to an already declared field, force, or state", "operations": ["add_term"]},
        {"id": "finite_relaxation_or_threshold", "description": "finite response time or physical threshold", "operations": ["change_assumption"]},
    ],
    "biology": [
        {"id": "finite_capacity_or_resource", "description": "finite capacity, resource limitation, or saturation", "operations": ["add_term", "change_assumption"]},
        {"id": "regulatory_or_ecological_feedback", "description": "regulatory, ecological, or biochemical feedback", "operations": ["add_term"]},
        {"id": "environmental_modulation", "description": "observed environmental or condition-dependent modulation", "operations": ["change_assumption"]},
    ],
    "economy": [
        {"id": "constraint_or_bottleneck", "description": "budget, capacity, credit, or institutional constraint", "operations": ["add_term", "change_assumption"]},
        {"id": "strategic_or_expectations_feedback", "description": "strategic interaction or expectations feedback", "operations": ["add_term"]},
        {"id": "adjustment_or_regime_change", "description": "finite adjustment or regime transition", "operations": ["change_assumption"]},
    ],
    "ai": [
        {"id": "effective_data_limitation", "description": "finite useful data or data quality", "operations": ["add_term", "change_assumption"]},
        {"id": "capacity_or_compute_bottleneck", "description": "capacity, compute, or optimization bottleneck", "operations": ["add_term", "change_assumption"]},
        {"id": "scale_crossover", "description": "crossover between scaling regimes", "operations": ["add_term", "change_assumption"]},
    ],
}


def load_ontology(path: Path | None = None) -> dict[str, Any]:
    """Load and minimally validate the versioned ontology JSON."""
    source = Path(path or ONTOLOGY_PATH)
    data = json.loads(source.read_text(encoding="utf-8"))
    for key in ("scopes", "structural_roles", "operation_definitions"):
        if not isinstance(data.get(key), dict) or not data[key]:
            raise ValueError(f"ontology field '{key}' must be a non-empty object")
    return data


def _subject_entry(taxonomy: dict[str, Any], discipline: str) -> dict[str, Any]:
    subjects = taxonomy.get("subjects", {})
    if discipline in subjects:
        return subjects[discipline]
    normalized = (discipline or "").lower()
    for name, entry in subjects.items():
        if str(name).lower() == normalized:
            return entry
    return {}


def load_taxonomy_profile(
    discipline: str,
    subfield: str | None = None,
    taxonomy_path: Path | None = None,
    ontology_path: Path | None = None,
) -> dict[str, Any]:
    """Merge ontology defaults with a subfield's optional evolution_profile."""
    ontology = load_ontology(ontology_path)
    taxonomy_file = Path(taxonomy_path or TAXONOMY_PATH)
    taxonomy = json.loads(taxonomy_file.read_text(encoding="utf-8"))
    subject = _subject_entry(taxonomy, discipline)
    selected = None
    for item in subject.get("subfields", []):
        if item.get("name") == subfield:
            selected = item
            break
    profile = (selected or {}).get("evolution_profile", {})
    if not isinstance(profile, dict):
        profile = {}
    mechanisms = profile.get("domain_mechanisms", [])
    if not isinstance(mechanisms, list):
        mechanisms = []
    if not mechanisms:
        normalized = (discipline or "").lower()
        mechanisms = _SUBJECT_FALLBACKS.get(normalized, [])
    return {
        "allowed_structural_roles": profile.get(
            "allowed_structural_roles", ontology["default_allowed_roles"]
        ),
        "preferred_scopes": profile.get(
            "preferred_scopes", ontology["default_preferred_scopes"]
        ),
        "domain_mechanisms": mechanisms,
        "profile_source": "subfield" if profile else "subject_fallback",
        "ontology_schema_version": ontology.get("schema_version", "unknown"),
        "taxonomy_schema_version": taxonomy.get("schema_version", "unknown"),
    }


def mechanism_menu(profile: dict[str, Any]) -> str:
    """Render a compact, prompt-safe mechanism menu."""
    roles = ", ".join(profile.get("allowed_structural_roles", []))
    scopes = ", ".join(profile.get("preferred_scopes", []))
    lines = [f"Allowed structural roles: {roles}", f"Preferred scopes: {scopes}"]
    mechanisms = profile.get("domain_mechanisms", [])
    if mechanisms:
        lines.append("Subfield mechanisms (choose one by id):")
        for item in mechanisms:
            ops = ", ".join(item.get("operations", ["add_term", "change_assumption"]))
            lines.append(f"- {item.get('id')}: {item.get('description', '')} [{ops}]")
    else:
        lines.append("No subfield menu is recorded; select a mechanism natural to the scenario.")
    return "\n".join(lines)


def validate_contract_fields(contract: dict[str, Any], profile: dict[str, Any], declared: set[str]) -> None:
    """Validate fields common to both evolution operations."""
    required = ("operation", "scope_kind", "scope_symbols", "structural_role",
                "domain_mechanism", "assumption_before", "assumption_after",
                "before_fragment", "after_fragment", "parent_reduction",
                "observable_signature", "shortcut_blocked")
    missing = [key for key in required if key not in contract]
    if missing:
        raise ValueError("evolution_contract missing " + ", ".join(missing))
    if contract["operation"] not in {"add_term", "change_assumption"}:
        raise ValueError("evolution_contract.operation must be add_term or change_assumption")
    if contract["scope_kind"] not in load_ontology()["scopes"]:
        raise ValueError(f"unknown evolution scope_kind '{contract['scope_kind']}'")
    symbols = contract["scope_symbols"]
    if not isinstance(symbols, list) or not symbols or any(symbol not in declared for symbol in symbols):
        raise ValueError("evolution_contract.scope_symbols must be non-empty declared symbols")
    if contract["structural_role"] not in profile.get("allowed_structural_roles", []):
        raise ValueError(f"structural role '{contract['structural_role']}' is not allowed by profile")
    mechanism_id = contract.get("domain_mechanism_id")
    mechanisms = profile.get("domain_mechanisms", [])
    if mechanisms and not mechanism_id:
        raise ValueError("evolution_contract.domain_mechanism_id is required by the subfield profile")
    known_mechanisms = {item.get("id"): item for item in mechanisms}
    if mechanisms and mechanism_id not in known_mechanisms:
        raise ValueError(f"domain mechanism id '{mechanism_id}' is not in the subfield profile")
    if mechanisms and contract["operation"] not in known_mechanisms[mechanism_id].get("operations", []):
        raise ValueError(
            f"mechanism '{mechanism_id}' is not allowed for {contract['operation']}"
        )
    for key in required[5:]:
        if not str(contract.get(key) or "").strip():
            raise ValueError(f"evolution_contract.{key} must be non-empty")


def fallback_contract(eq: dict[str, Any], operation: str) -> dict[str, Any] | None:
    """Build metadata for legacy records that predate the contract schema."""
    audit = eq.get("add_term_audit") or eq.get("assumption_audit")
    if not isinstance(audit, dict):
        return None
    role = "contribution" if operation == "add_term" else "response_law"
    scope = "unary"
    symbols = [eq.get("target_symbol")] if eq.get("target_symbol") else []
    mechanism = audit.get("mechanism_claim") or audit.get("mechanism") or "legacy recorded mechanism"
    return {
        "operation": operation, "scope_kind": scope, "scope_symbols": symbols,
        "structural_role": role, "domain_mechanism_id": "legacy",
        "domain_mechanism": mechanism, "assumption_before": audit.get("released_assumption", "legacy").strip() if isinstance(audit.get("released_assumption", "legacy"), str) else "legacy",
        "assumption_after": eq.get("change_summary", "legacy successor"),
        "before_fragment": "legacy parent expression", "after_fragment": eq.get("expression", ""),
        "parent_reduction": audit.get("parent_reduction", "legacy record"),
        "observable_signature": audit.get("observable_signature", "legacy record"),
        "shortcut_blocked": "legacy record; not validated against the new contract",
    }
