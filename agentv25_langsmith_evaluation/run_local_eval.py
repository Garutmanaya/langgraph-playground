from __future__ import annotations

import json
from pathlib import Path
from .agent_graph import run
from .evaluators import evaluate_case

CASES_PATH = Path(__file__).resolve().parent / "eval_cases.jsonl"

def load_cases():
    return [json.loads(line) for line in CASES_PATH.read_text().splitlines() if line.strip()]

def main():
    results = []
    for case in load_cases():
        output = run(case["input"])
        result = evaluate_case(output, case)
        results.append((case, output, result))

    print("\nEvaluation Results")
    print("=" * 100)
    for case, output, result in results:
        print(f"{case['case_id']:10} passed={str(result['passed']):5} score={result['score']:.3f} classification={output['classification']}")
        for ev in result["evaluators"]:
            print(f"  - {ev['name']}: passed={ev['passed']} score={ev['score']} notes={ev['notes']}")

    overall = sum(r["score"] for _, _, r in results) / len(results)
    pass_rate = sum(1 for _, _, r in results if r["passed"]) / len(results)
    print("\nSummary")
    print("=" * 100)
    print(f"Overall score: {overall:.3f}")
    print(f"Pass rate: {pass_rate:.1%}")

    if pass_rate < 1.0:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
