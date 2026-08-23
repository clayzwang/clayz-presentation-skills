# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Stable constants for the index-native retrieval contracts."""

INDEX_CONTRACT = "io.clayz.presentation.index-record/1.0"
REQUEST_CONTRACT = "io.clayz.presentation.retrieval-request/1.0"
RECEIPT_CONTRACT = "io.clayz.presentation.retrieval-receipt/1.0"

RECORD_TYPES = {
    "capability",
    "knowledge",
    "layout-contract",
    "visual-variant",
    "composition-pattern",
    "reference",
    "sequence",
    "failure-pattern",
    "compatibility-note",
    "learning",
}
STAGES = {"logic", "copy", "art-direction", "output", "supervisor", "shared"}
RIGHTS_CONTEXTS = {"private-runtime", "public-open-source"}
REDISTRIBUTION = {"allowed", "metadata-only", "local-private", "forbidden"}
MATERIALIZATION = {"allowed", "local-only", "forbidden"}
QUALITY_STATES = {"observation", "admitted", "rejected", "deprecated"}
HIGH_RISK_BRAND_ASSET_CLASSES = {"template", "master", "font", "brand-kit"}


class IndexRuntimeError(ValueError):
    """Raised when an index contract or retrieval operation is invalid."""
