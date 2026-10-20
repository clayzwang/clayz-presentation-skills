#!/usr/bin/env python3
"""Save a new, read-only observation of selected rendered labels."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.layout.rendered_label_occupancy import observe, reference

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("request")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error("Output already exists; choose a new observation revision")
    request = json.loads(Path(args.request).read_text())
    result = observe(args.pdf, request)
    result["request"] = reference(args.request)
    with output.open("x") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "coverage": result["coverage"],
                      "possible_intersections": sum(len(p["possible_intersections"]) for p in result["pages"])}))
