"""Read-only early diagnostic using the unchanged native output-capture rules.

No production run/session is created or changed. All seven human/visual checks
are explicitly not-observed; native text/cache conformity is not quality.
Temporary content-addressed byte copies are removed after the diagnostic.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.workflow3 import io, technical


def file_ref(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve prior diagnostics; choose a new output file")
    graph_ref, pptx_ref = file_ref(args.graph), file_ref(args.pptx)
    graph = io.read(args.graph)
    qa = {"contract": technical.CONTRACT, "checks": {
        key: {"status": "not-observed", "explanation":
              "Not evaluated by this machine-only native text/cache diagnostic.",
              "evidence": []} for key in technical.REQUIRED}}
    result = {"contract": "local.native-visible-copy-diagnostic/1",
              "observed_at": datetime.now(timezone.utc).isoformat(),
              "graph": graph_ref, "pptx": pptx_ref,
              "unchanged_checker": file_ref(Path(technical.__file__)),
              "quality_checks": qa["checks"],
              "scope": "Same native text/cache and slide-count rules; no quality verdict, render, authoring, environment scan or production-state mutation.",
              "limitations": ["Whitespace is the only text normalization.",
                  "Chart cache presence does not prove that a value label is visible.",
                  "No semantic, pixel, font, overflow, native editing or application acceptance.",
                  "The unchanged checker reports at most eight missing-token examples."]}
    with tempfile.TemporaryDirectory(prefix="ppt-native-diagnostic-") as directory:
        root = Path(directory)
        files = {"pptx": io.snapshot(root, args.pptx)}
        dependency = {"details": {"pages": graph["pages"],
                                   "copy_graph": io.snapshot(root, args.graph)}}
        try:
            captured = technical.capture(root, qa, files, dependency)
            result.update(native_text_check="matched", native_error=None,
                          written_slides=len(captured["native_inventory"]))
            code = 0
        except ValueError as error:
            result.update(native_text_check="mismatch", native_error=str(error))
            code = 2
    if file_ref(args.graph) != graph_ref or file_ref(args.pptx) != pptx_ref:
        raise ValueError("Input changed during read-only diagnostic")
    io.write_new(args.output, result)
    print(json.dumps({"result": file_ref(args.output),
                      "native_text_check": result["native_text_check"],
                      "quality": "not-evaluated"}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
