# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Public API for the index-native retrieval foundation."""

from .runtime import (
    CAPABILITY_RESOLUTION_CONTRACT,
    INDEX_CONTRACT,
    RECEIPT_CONTRACT,
    REQUEST_CONTRACT,
    CompositeIndex,
    IndexProvider,
    IndexRuntimeError,
    mandatory_core,
    read_json,
    resolve_capabilities,
    tokenize,
    validate_record,
    validate_request,
    write_json,
)

__all__ = [
    "CAPABILITY_RESOLUTION_CONTRACT",
    "INDEX_CONTRACT",
    "RECEIPT_CONTRACT",
    "REQUEST_CONTRACT",
    "CompositeIndex",
    "IndexProvider",
    "IndexRuntimeError",
    "mandatory_core",
    "read_json",
    "resolve_capabilities",
    "tokenize",
    "validate_record",
    "validate_request",
    "write_json",
]
