# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Feedback, benchmark, migration, and release-readiness APIs."""

from .benchmark import BenchmarkError, run_retrieval_benchmark
from .learning import (
    ADMISSION_CONTRACT,
    FEEDBACK_REPORT_CONTRACT,
    LEARNING_CONTRACT,
    FeedbackError,
    build_learning_provider,
    learning_record_sha256,
    validate_learning_admission,
    validate_learning_record,
)
from .migration import MIGRATION_REPORT_CONTRACT, migrate_legacy_knowledge
from .readiness import READINESS_CONTRACT, ReadinessError, validate_release_readiness

__all__ = [
    "ADMISSION_CONTRACT",
    "BenchmarkError",
    "FEEDBACK_REPORT_CONTRACT",
    "FeedbackError",
    "LEARNING_CONTRACT",
    "MIGRATION_REPORT_CONTRACT",
    "READINESS_CONTRACT",
    "ReadinessError",
    "build_learning_provider",
    "learning_record_sha256",
    "migrate_legacy_knowledge",
    "run_retrieval_benchmark",
    "validate_learning_admission",
    "validate_learning_record",
    "validate_release_readiness",
]
