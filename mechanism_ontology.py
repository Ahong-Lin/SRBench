"""Shared vocabulary for open scientific mechanism evolution.

The ontology supplies reusable *embedding patterns* (how a mechanism enters an
equation).  A taxonomy profile is deliberately advisory: it gives an LLM useful
domain examples, but is not a whitelist of the mechanisms a new scenario may
contain.  Mathematical closure and declared-variable checks remain hard gates.
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
    for key in ("scopes", "structural_roles", "embedding_patterns", "operation_definitions"):
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
    """Render a compact, prompt-safe advisory mechanism menu."""
    roles = ", ".join(profile.get("allowed_structural_roles", []))
    scopes = ", ".join(profile.get("preferred_scopes", []))
    lines = [
        f"Suggested structural roles: {roles}",
        f"Preferred scopes: {scopes}",
        "These are examples and not a whitelist. A scenario-natural mechanism may be recorded as provisional.",
    ]
    mechanisms = profile.get("domain_mechanisms", [])
    if mechanisms:
        lines.append("Subfield mechanism examples (use an id when it fits; otherwise describe a new mechanism):")
        for item in mechanisms:
            ops = ", ".join(item.get("operations", ["add_term", "change_assumption"]))
            lines.append(f"- {item.get('id')}: {item.get('description', '')} [{ops}]")
    else:
        lines.append("No subfield menu is recorded; select a mechanism natural to the scenario.")
    return "\n".join(lines)


def embedding_patterns(ontology_path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Return the cross-domain, versioned embedding-pattern registry."""
    patterns = load_ontology(ontology_path).get("embedding_patterns", {})
    if not isinstance(patterns, dict) or not patterns:
        raise ValueError("ontology.embedding_patterns must be a non-empty object")
    return patterns


def compatible_embedding_patterns(
    operation: str,
    model_family: str,
    active_quantity_count: int,
    assumption_mode: str = "extended",
    ontology_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Filter patterns that can be used by the current equation structure."""
    compatible: list[dict[str, Any]] = []
    for pattern_id, raw in embedding_patterns(ontology_path).items():
        pattern = dict(raw)
        if operation not in pattern.get("operations", []):
            continue
        if model_family not in pattern.get("model_families", []):
            continue
        if active_quantity_count < int(pattern.get("minimum_active_quantities", 1)):
            continue
        if pattern.get("requires_extended_assumption_mode") and assumption_mode != "extended":
            continue
        pattern["id"] = pattern_id
        compatible.append(pattern)
    if not compatible:
        raise ValueError(
            f"no compatible embedding pattern for operation={operation}, "
            f"model_family={model_family}, active_quantity_count={active_quantity_count}"
        )
    return compatible


def validate_contract_fields(contract: dict[str, Any], profile: dict[str, Any], declared: set[str]) -> None:
    """Validate fields common to both evolution operations."""
    required = ("operation", "scope_kind", "scope_symbols", "structural_role",
                "domain_mechanism", "scientific_mechanism", "embedding_pattern",
                "difficulty_rationale", "assumption_before", "assumption_after",
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
    ontology = load_ontology()
    if contract["structural_role"] not in ontology["structural_roles"]:
        raise ValueError(f"unknown global structural role '{contract['structural_role']}'")
    if contract["embedding_pattern"] not in ontology["embedding_patterns"]:
        raise ValueError(f"unknown embedding pattern '{contract['embedding_pattern']}'")
    # ``domain_mechanism_id`` is optional.  Known IDs are helpful metadata, but
    # an absent or novel ID must not reject a scientifically coherent proposal.
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
        "domain_mechanism": mechanism, "scientific_mechanism": mechanism,
        "embedding_pattern": "additive_contribution" if operation == "add_term" else "state_dependent_coefficient",
        "difficulty_rationale": "legacy record; embedding was not classified at generation time",
        "assumption_before": audit.get("released_assumption", "legacy").strip() if isinstance(audit.get("released_assumption", "legacy"), str) else "legacy",
        "assumption_after": eq.get("change_summary", "legacy successor"),
        "before_fragment": "legacy parent expression", "after_fragment": eq.get("expression", ""),
        "parent_reduction": audit.get("parent_reduction", "legacy record"),
        "observable_signature": audit.get("observable_signature", "legacy record"),
        "shortcut_blocked": "legacy record; not validated against the new contract",
    }
