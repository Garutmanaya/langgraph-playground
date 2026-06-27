from __future__ import annotations

import json
import os
from pathlib import Path
from langsmith import Client

CASES_PATH = Path(__file__).resolve().parent / "eval_cases.jsonl"
DATASET_NAME = os.getenv("LANGSMITH_DATASET_NAME", "agentv25-epp-eval")

def main():
    client = Client()
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Agent v25 EPP regression evaluation dataset.",
    )

    cases = [json.loads(line) for line in CASES_PATH.read_text().splitlines() if line.strip()]
    for case in cases:
        client.create_example(
            dataset_id=dataset.id,
            inputs={"input": case["input"]},
            outputs={
                "expected_classification": case["expected_classification"],
                "required_terms": case["required_terms"],
                "forbidden_terms": case["forbidden_terms"],
                "notes": case["notes"],
            },
            metadata={"case_id": case["case_id"]},
        )

    print(f"Created LangSmith dataset: {DATASET_NAME}")
    print(f"Examples: {len(cases)}")

if __name__ == "__main__":
    main()
