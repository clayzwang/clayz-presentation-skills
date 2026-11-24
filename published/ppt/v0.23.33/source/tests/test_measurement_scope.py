"""Synthetic editorial comparisons use declared coverage rather than labels."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.copy_graph.measurement_scope import compare


def test_shared_label_keeps_the_missing_coverage_unknown():
    a = {"label": "annual amount", "population": "regional firms",
         "start": "2025-01-01", "end": "2025-12-31"}
    b = {"label": "annual amount", "population": "regional firms", "start": "2025-01-01"}
    observation = compare(a, b, ("label", "population", "start", "end"))
    assert observation == {
        "matching": ["label", "population", "start"], "different": [],
        "unknown": ["end"], "establishes_same_scope": False,
    }


def test_known_difference_and_unknown_dimension_are_both_retained():
    a = {"unit": "items", "population": "all branches", "settlement": "estimated"}
    b = {"unit": "items", "population": "open branches"}
    observation = compare(a, b, ("unit", "population", "settlement"))
    assert observation == {
        "matching": ["unit"], "different": ["population"], "unknown": ["settlement"],
        "establishes_same_scope": False,
    }


def test_a_known_pair_can_be_compared():
    basis = {"unit": "hours", "coverage": "installs before cutoff", "cutoff": "2025-05-31"}
    assert compare(basis, dict(basis), tuple(basis))["establishes_same_scope"]
