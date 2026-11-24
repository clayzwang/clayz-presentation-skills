"""Exercise training defaults and the exact revision entry without production material."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.workflow3 import CONTRACT, io, run, training_operations as ops


def load_script(module, filename):
    spec = importlib.util.spec_from_file_location(module, ROOT / "scripts" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def frozen_run(root, current=False, explicit=None):
    config = io.read(ROOT / "config/default.json")
    config["workflow"]["reader_review"]["required"] = False
    config["workflow"]["mode_system"] = {"contract": CONTRACT, "mode": "train",
        "production_stages": ["logic", "copy", "art", "output"], "reader_return_limit": 1}
    config["runtime"]["budgets"].update(maximum_authoring_writes=4, maximum_repair_cycles=3,
                                        maximum_full_deck_renders=4)
    if explicit:
        config["runtime"]["training_limits"] = explicit
    if current:
        ops.resolve_defaults(config)
    file = io.write_new(root / "task-config.json", config)
    conf = io.snapshot(root, file)
    artifact = io.snapshot_json(root, {"fixture": True})
    (root / "events").mkdir()
    runinfo = {"contract": CONTRACT, "mode": "train", "run_id": "test-run", "config": conf,
               "task_request": artifact, "rules": artifact, "challenge": artifact}
    runfile = io.write_new(root / "run.json", runinfo)
    session = io.write_new(root / "session.json", {
        "contract": "io.clayz.presentation.training-session/1.0", "session_id": "test-session",
        "production_run_id": "test-run", "production_run": {"sha256": io.digest(runfile.read_bytes())},
        "goals": [{"goal": {"text": "fixture"}}]})
    package = io.write_new(root / "package.json", {"contract": "io.clayz.presentation.training-package/1.0"})
    run.bind_training(root, package, session)
    return runinfo


def compatibility(root, evidence, native):
    return io.write_new(root / "review.json", {
        "contract": ops.POLICY, "run_id": "test-run", "session_id": "test-session",
        "config_sha256": native["config"]["sha256"], "withdrawn_defaults": list(ops.OPERATIONS),
        "retained_observations": evidence,
    })


def invoke(script, *arguments):
    return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / script), *map(str, arguments)],
                          text=True, capture_output=True)


def test_defaults_explicit_counts_and_route_lock(tmp_path):
    root = tmp_path / "new"
    frozen_run(root, current=True)
    config = io.read(root / "task-config.json")
    assert config["runtime"]["budgets"] == {"maximum_route_switches": 0}
    assert "maximum_technical_cycles" not in config["workflow"]
    validator = load_script("validation", "validate_config.py")
    assert validator.validate(config) == []
    assert validator.validate(io.read(ROOT / "config/default.json")) == []
    explicit = tmp_path / "explicit"
    native = frozen_run(explicit, current=True, explicit={"office_processes": 1, "technical_cycles": 19})
    assert ops.report(explicit, native)["active_limits"] == {"office_processes": 1, "technical_cycles": 19}
    witness = io.write_new(explicit / "actual.json", {"fixture": True})
    ops.permit(explicit, native, "office_processes")
    ops.observe(explicit, "office_processes", witness)
    with pytest.raises(ValueError, match="configured limit of 1"):
        ops.permit(explicit, native, "office_processes")
    with pytest.raises(ValueError, match="unknown operational count"):
        ops.permit(explicit, native, "route_switches")


def test_existing_round_adoption_preserves_history_and_limits(tmp_path):
    native = frozen_run(tmp_path, explicit={"authoring_writes": 4})
    old = (tmp_path / "task-config.json").read_bytes()
    chain = io.events(tmp_path)
    existing = [str(io.write_new(tmp_path / f"launch-{i}.json", {"launcher": i})) for i in (1, 2)]
    bad = compatibility(tmp_path, {"office_processes": existing}, native)
    with pytest.raises(ValueError, match="identify exactly"):
        ops.adopt(tmp_path, bad)
    reviewed = io.read(bad)
    reviewed["withdrawn_defaults"].remove("authoring_writes")
    good = io.write_new(tmp_path / "specific.json", reviewed)
    adopted = ops.adopt(tmp_path, good)
    assert ops.adopt(tmp_path, good) == adopted
    assert io.events(tmp_path) == chain + [adopted]
    assert (tmp_path / "task-config.json").read_bytes() == old
    assert ops.report(tmp_path, native)["active_limits"] == {"authoring_writes": 4}
    assert ops.report(tmp_path, native)["counts"]["office_processes"] == 2
    for i in range(6):
        ops.permit(tmp_path, native, "office_processes")
        evidence = io.write_new(tmp_path / f"next-{i}.json", {"launcher": i})
        event = ops.observe(tmp_path, "office_processes", evidence)
        assert ops.observe(tmp_path, "office_processes", evidence) == event
    assert ops.report(tmp_path, native)["counts"]["office_processes"] == 8
    assert run.state(tmp_path)["returns"] == {"content": 0, "layout": 0, "final": 0}


def test_review_checks_session_and_frozen_config(tmp_path):
    native = frozen_run(tmp_path)
    review = compatibility(tmp_path, {}, native)
    forged = {**io.read(review), "session_id": "different"}
    with pytest.raises(ValueError, match="current training session"):
        ops.adopt(tmp_path, io.write_new(tmp_path / "different-session.json", forged))
    forged = {**io.read(review), "config_sha256": "0" * 64}
    with pytest.raises(ValueError, match="frozen config"):
        ops.adopt(tmp_path, io.write_new(tmp_path / "different-bytes.json", forged))
    assert len(io.events(tmp_path)) == 1


def test_effective_ledger_continues_beyond_legacy_limit(tmp_path):
    native = frozen_run(tmp_path)
    review = compatibility(tmp_path, {}, native)
    ledger = load_script("ledger", "execution_ledger.py")
    frozen = tmp_path / "task-config.json"
    assert ledger.configured_maximum_cycles(frozen) == 3
    rejected = ledger.initialize(native["run_id"], ledger.configured_maximum_cycles(frozen))
    kwargs = dict(cycle=4, stage="output", tool="validation", status="succeeded",
                  inputs=[frozen], outputs=[], evidence_refs=[], error_code=None, message="actual fixture")
    with pytest.raises(ledger.LedgerError, match="1 to 3"):
        ledger.append_event(rejected, **kwargs)
    ops.adopt(tmp_path, review)
    dest = tmp_path / "ledger.json"
    initialized = invoke("execution_ledger.py", "init", dest, "--run-id", native["run_id"],
                         "--training-run", tmp_path)
    assert initialized.returncode == 0, initialized.stderr
    revised = ledger.read(dest)
    assert ledger.append_event(revised, **kwargs)["cycle"] == 4
    assert (tmp_path / "task-config.json").is_file()


def test_explicit_five_round_limit_and_earlier_success():
    from packages.workflow3.iteration_decision import next_action

    policy = {"maximum_rounds": 5}
    check = {"round": "R01", "session_closed": True, "independent_judgments_read_back": True,
             "complete_tool_and_knowledge_verified": True, "regression_read_back": True,
             "goals": "met"}
    assert next_action(policy, ["R01"], check) == "stop-goals-met"
    assert next_action(policy, ["R01"], {**check, "regression_read_back": False}) == "await-current-round"
    assert next_action(policy, ["R01"], {**check, "goals": "unknown"}) == "await-goal-verdict"
    assert next_action(policy, ["R01"], {**check, "goals": "not-met"}) == "consider-next-round"
    first_five = [f"R{i:02d}" for i in range(1, 6)]
    assert next_action(policy, first_five, {**check, "round": "R05", "goals": "not-met"}) == "stop-round-limit"
    with pytest.raises(ValueError, match="authorized sequence"):
        next_action(policy, [*first_five, "R06"], check)
    with pytest.raises(ValueError, match="authorized sequence"):
        next_action(policy, ["R01", "R01"], check)
