from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass
class EvalResult:
    name: str
    passed: bool
    score: float
    notes: str

def normalize(text: str) -> str:
    return text.lower().strip()

def classification_evaluator(output: dict[str, Any], case: dict[str, Any]) -> EvalResult:
    actual = output.get("classification")
    expected = case.get("expected_classification")
    passed = actual == expected
    return EvalResult("classification", passed, 1.0 if passed else 0.0, f"expected={expected}, actual={actual}")

def required_terms_evaluator(output: dict[str, Any], case: dict[str, Any]) -> EvalResult:
    answer = normalize(output.get("answer", ""))
    terms = case.get("required_terms", [])
    missing = [term for term in terms if normalize(term) not in answer]
    score = 1.0 if not terms else (len(terms) - len(missing)) / len(terms)
    return EvalResult("required_terms", not missing, score, f"missing={missing}")

def forbidden_terms_evaluator(output: dict[str, Any], case: dict[str, Any]) -> EvalResult:
    answer = normalize(output.get("answer", ""))
    terms = case.get("forbidden_terms", [])
    found = [term for term in terms if normalize(term) in answer]
    return EvalResult("forbidden_terms", not found, 1.0 if not found else 0.0, f"found={found}")

def evaluate_case(output: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    evals = [
        classification_evaluator(output, case),
        required_terms_evaluator(output, case),
        forbidden_terms_evaluator(output, case),
    ]
    score = 0.4 * evals[0].score + 0.4 * evals[1].score + 0.2 * evals[2].score
    return {
        "case_id": case["case_id"],
        "passed": all(e.passed for e in evals),
        "score": round(score, 3),
        "evaluators": [e.__dict__ for e in evals],
    }
