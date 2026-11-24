#!/usr/bin/env python3
"""Make an optional semantic reading view; never dereference source pointers."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.copy_graph.professional_view import project


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def bad_constant(value):
    raise ValueError("Nonfinite JSON number: " + value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = args.graph.read_bytes()
        graph = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                           parse_constant=bad_constant)
        view = project(graph)
        view["original_graph"] = {
            "path": str(args.graph.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(view, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.write("\n")
        print(json.dumps({"view": str(args.output.resolve()),
                          "original_graph": view["original_graph"],
                          "quality": "not-evaluated",
                          "referenced_source_files_read": False}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
