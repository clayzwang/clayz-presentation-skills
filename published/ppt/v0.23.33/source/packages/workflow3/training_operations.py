"""Training operation limits and observations for both new and frozen runs."""
from pathlib import Path
import subprocess

from . import io

POLICY = "io.clayz.presentation.training-operational-counts/1.0"
DEFAULTS = {
    "capability_scans": (1,),
    "source_collection_rounds": (1,),
    "authoring_writes": (2, 4),
    "office_processes": (1,),
    "full_deck_renders": (2, 4),
    "repair_cycles": (1, 3),
    "fallback_restarts": (1,),
}
OPERATIONS = (*DEFAULTS, "technical_cycles")


def resolve_defaults(config):
    runtime = config["runtime"]
    budgets = runtime["budgets"]
    explicit = runtime.get("training_limits", {})
    if not isinstance(explicit, dict) or not explicit.keys() <= set(OPERATIONS):
        raise ValueError("training_limits requires known operation counts")
    if any(type(value) is not int or value < 1 for value in explicit.values()):
        raise ValueError("explicit training limits must be positive integers")
    for operation, defaults in DEFAULTS.items():
        key = "maximum_" + operation
        if budgets.get(key) in defaults:
            budgets.pop(key, None)
        if operation in explicit:
            budgets[key] = explicit[operation]
    workflow = config["workflow"]
    if workflow.get("maximum_technical_cycles") == 3:
        workflow.pop("maximum_technical_cycles")
    if "technical_cycles" in explicit:
        workflow["maximum_technical_cycles"] = explicit["technical_cycles"]
    if any(type(value) is not int or value < 1 for value in limits(config).values()):
        raise ValueError("training operation limits must be positive integers")
    runtime["training_operational_policy"] = POLICY


def limits(config):
    result = {
        operation: config["runtime"]["budgets"]["maximum_" + operation]
        for operation in DEFAULTS if "maximum_" + operation in config["runtime"]["budgets"]
    }
    maximum = config["workflow"].get("maximum_technical_cycles")
    if maximum is not None:
        result["technical_cycles"] = maximum
    return result


def adopt(root, reviewed_path):
    """Append the reviewed compatibility decision and retained observations once."""
    from . import run

    with io.locked(root):
        state = run.state(root)
        native = state["run"]
        if native["mode"] != "train" or "training" not in native:
            raise ValueError("a bound training run is required")
        config = io.read(io.resolve(root, native["config"]))
        if config["runtime"].get("training_operational_policy") == POLICY:
            raise ValueError("this run was initialized with the current defaults")
        raw = Path(reviewed_path).read_bytes()
        reviewed = io.read(reviewed_path)
        if (reviewed["contract"], reviewed["run_id"], reviewed["config_sha256"]) != (
                POLICY, native["run_id"], native["config"]["sha256"]):
            raise ValueError("compatibility review does not bind the frozen config and run")
        session = io.read(io.resolve(root, native["training"]["session"]))
        if reviewed["session_id"] != session["session_id"]:
            raise ValueError("compatibility review does not bind the current training session")
        existing = [event for event in io.events(root) if event["kind"] == "training-operational-policy"]
        if existing:
            if existing[0]["payload"]["review"]["sha256"] != io.digest(raw):
                raise ValueError("preserve the original compatibility decision")
            return existing[0]
        before = limits(config)
        resolve_defaults(config)
        after = limits(config)
        if set(reviewed["withdrawn_defaults"]) != before.keys() - after.keys():
            raise ValueError("review must identify exactly the inherited defaults being withdrawn")
        observations = {}
        for operation, paths in reviewed["retained_observations"].items():
            if operation not in OPERATIONS or not isinstance(paths, list) or len(paths) != len(set(paths)):
                raise ValueError("retain distinct existing observations per operation")
            observations[operation] = [io.snapshot(root, path) for path in paths]
        return io.append(root, "training-operational-policy", {
            "contract": POLICY, "review": io.snapshot(root, reviewed_path),
            "frozen_config": native["config"], "active_limits": after,
            "withdrawn_defaults": {key: value for key, value in before.items() if key not in after},
            "retained_observations": observations,
        })


def report(root, native):
    config = io.read(io.resolve(root, native["config"]))
    active = limits(config)
    counts = {operation: 0 for operation in OPERATIONS}
    current = config["runtime"].get("training_operational_policy") == POLICY
    for event in io.events(root):
        payload = event["payload"]
        if event["kind"] == "training-operational-policy":
            if payload["contract"] != POLICY or payload["frozen_config"] != native["config"]:
                raise ValueError("compatibility decision does not match the frozen config")
            io.resolve(root, payload["review"])
            active = payload["active_limits"]
            current = True
            for operation, refs in payload["retained_observations"].items():
                for ref in refs:
                    io.resolve(root, ref)
                counts[operation] += len(refs)
        if event["kind"] == "runtime-operation":
            counts[payload["operation"]] += 1
    return {
        "policy": POLICY if current else "legacy",
        "active_limits": active,
        "counts": counts if current else None,
    }


def permit(root, native, operation, observed=None):
    if operation not in OPERATIONS:
        raise ValueError("unknown operational count")
    if observed is None:
        observed = report(root, native)
    maximum = observed["active_limits"].get(operation)
    if maximum is not None and observed["counts"] is None:
        raise ValueError("the legacy count requires a reviewed history before admission")
    if maximum is not None and observed["counts"][operation] >= maximum:
        raise ValueError(f"{operation} reached the configured limit of {maximum}")


def native_run(root):
    from . import run

    native = run.state(root)["run"]
    if native["mode"] != "train" or "training" not in native:
        raise ValueError("a bound training run is required")
    return native


def observe(root, operation, evidence):
    """Record a completed or attempted operation with its actual evidence."""
    with io.locked(root):
        native_run(root)
        if operation not in OPERATIONS:
            raise ValueError("unknown operational count")
        ref = io.snapshot(root, evidence)
        for event in io.events(root):
            if event["kind"] == "runtime-operation" and (
                    event["payload"]["operation"], event["payload"]["evidence"]["original_path"]
            ) == (operation, ref["original_path"]):
                if event["payload"]["evidence"] != ref:
                    raise ValueError("previous observation bytes changed")
                return event
        return io.append(root, "runtime-operation", {"operation": operation, "evidence": ref})



def start_office(root, command, env, source, directory):
    with io.locked(root):
        native = native_run(root)
        counts = report(root, native)
        if counts["policy"] != POLICY:
            raise ValueError("review the frozen training operation defaults before continuing")
        permit(root, native, "office_processes", counts)
        permit(root, native, "full_deck_renders", counts)
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True)
        try:
            record = directory / "office-launch.json"
            io.write_new(record, {
                "started_at": io.now(), "launcher_pid": process.pid,
                "command": command, "source": io.snapshot(root, source),
            })
            io.append(root, "runtime-operation", {
                "operation": "office_processes", "evidence": io.snapshot(root, record),
            })
        except BaseException:
            process.terminate()
            process.communicate()
            raise
        return process
