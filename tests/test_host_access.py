# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Regression coverage for host access resolution.

The observation is deliberately a report from already observed tools and file
reads.  These tests keep the resolver honest about that boundary: permission
claims do not create a connection, a locator does not become a file read, and
an advertised write operation is not a verified write.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "cloud_learning_cli.py"
REPORT_CONTRACT = "io.clayz.presentation.host-access-report/1.0"
OBSERVATION_CONTRACT = "io.clayz.presentation.host-access-observation/1.0"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resource(report: dict, resource_id: str) -> dict:
    """Return one resource row while accepting list or keyed-map reports."""

    rows = report["resources"]
    if isinstance(rows, dict):
        return rows[resource_id]
    for row in rows:
        if row.get("resource_id") == resource_id:
            return row
    raise AssertionError(f"resource row not found: {resource_id}")


class HostAccessResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="clayz-host-access-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def observation(
        self,
        *,
        session_id: str = "host-access-session",
        tools: list[dict] | None = None,
        resources: list[dict] | None = None,
        attempts: list[dict] | None = None,
        **extra: object,
    ) -> dict:
        return {
            "contract": OBSERVATION_CONTRACT,
            "session_id": session_id,
            "tools": [] if tools is None else tools,
            "resources": [] if resources is None else resources,
            "attempts": [] if attempts is None else attempts,
            **extra,
        }

    @staticmethod
    def tool(tool_id: str, kind: str = "native-library", operations: tuple[str, ...] = ("locate", "read")) -> dict:
        return {"tool_id": tool_id, "kind": kind, "operations": list(operations)}

    @staticmethod
    def resource(
        resource_id: str,
        *,
        logical_uri: str = "library://owner/guide.md",
        host_locator: str = "PPT/_extension/confirmed-learning/guide.md",
        required: bool = True,
        expected_sha256: str | None = None,
        explicit_attachment_ref: str | None = None,
        selected_reference: str | None = None,
    ) -> dict:
        row = {
            "resource_id": resource_id,
            "logical_uri": logical_uri,
            "host_locator": host_locator,
            "required": required,
        }
        if expected_sha256 is not None:
            row["expected_sha256"] = expected_sha256
        if explicit_attachment_ref is not None:
            row["explicit_attachment_ref"] = explicit_attachment_ref
        if selected_reference is not None:
            row["selected_reference"] = selected_reference
        return row

    @staticmethod
    def attempt(
        resource_id: str,
        tool_id: str,
        operation: str,
        *,
        status: str = "ok",
        matches: list[dict] | None = None,
        reference: str | None = None,
        materialized_path: Path | None = None,
    ) -> dict:
        row = {
            "resource_id": resource_id,
            "tool_id": tool_id,
            "operation": operation,
            "status": status,
        }
        if matches is not None:
            row["matches"] = matches
        if reference is not None:
            row["reference"] = reference
        if materialized_path is not None:
            row["materialized_path"] = str(materialized_path)
        return row

    def source(self, name: str = "guide.md", content: bytes = b"confirmed host material\n") -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def resolve_cli(self, observation: dict, previous_report: dict | None = None) -> dict:
        observation_path = self.root / "observation.json"
        observation_path.write_text(json.dumps(observation, ensure_ascii=False), encoding="utf-8")
        args: list[object] = [
            "resolve-access",
            "--observation",
            observation_path,
        ]
        if previous_report is not None:
            previous_path = self.root / "previous-report.json"
            previous_path.write_text(json.dumps(previous_report, ensure_ascii=False), encoding="utf-8")
            args.extend(["--previous-report", previous_path])
        output_path = self.root / "report.json"
        args.extend(["--output", output_path])
        environment = dict(
            os.environ,
            PYTHONUTF8="1",
            PYTHONDONTWRITEBYTECODE="1",
        )
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), *map(str, args)],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=40,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report, json.loads(output_path.read_text(encoding="utf-8")))
        return report

    def resolve_direct(self, observation: dict, previous_report: dict | None = None) -> dict:
        # Import lazily so malformed-input tests can still be collected before
        # the resolver implementation is added to the CLI module.
        from scripts.cloud_learning_cli import resolve_access

        return resolve_access(observation, previous_report=previous_report)

    def assert_report_shape(self, report: dict) -> None:
        self.assertEqual(report["contract"], REPORT_CONTRACT)
        self.assertIn(report["status"], {"ready", "partial", "blocked", "no-resources"})
        self.assertIsInstance(report["resources"], (list, dict))
        self.assertIsInstance(report["required_unresolved"], list)
        self.assertIsInstance(report["read_capability_exposed"], bool)
        self.assertIsInstance(report["write_capability_exposed"], bool)
        self.assertIs(report["write_verified"], False)
        self.assertIsInstance(report["retry_discovery"], bool)
        self.assertIsInstance(report["input_fingerprint"], str)
        self.assertRegex(report["input_fingerprint"], SHA256)
        self.assertIs(report["host_api_called"], False)

    def test_empty_resource_set_is_explicit_and_read_only(self) -> None:
        report = self.resolve_cli(self.observation())

        self.assert_report_shape(report)
        self.assertEqual(report["status"], "no-resources")
        self.assertEqual(report["resources"], [])
        self.assertEqual(report["required_unresolved"], [])
        self.assertFalse(report["read_capability_exposed"])
        self.assertFalse(report["write_capability_exposed"])

    def test_authorization_claim_cannot_create_unknown_library_access(self) -> None:
        observation = self.observation(
            tools=[],
            resources=[
                self.resource(
                    "unknown-library",
                    logical_uri="library://openai/unknown-guide.md",
                    host_locator="PPT/_extension/confirmed-learning/unknown-guide.md",
                )
            ],
            authorization_granted=True,
            permission_lookups=[{"resource_id": "unknown-library", "granted": True}],
        )
        report = self.resolve_direct(observation)

        self.assert_report_shape(report)
        row = _resource(report, "unknown-library")
        self.assertNotIn(row["state"], {"connection-installed", "files-readable", "readable-native"})
        self.assertIn(report["status"], {"blocked", "partial"})
        self.assertIn("unknown-library", report["required_unresolved"])
        self.assertFalse(report["read_capability_exposed"])
        self.assertFalse(report["host_api_called"])

    def test_repeated_authorization_in_one_session_does_not_retry_or_change_fingerprint(self) -> None:
        observation = self.observation(
            resources=[self.resource("unknown-library", logical_uri="library://openai/unknown-guide.md")],
            authorization_granted=True,
        )
        first = self.resolve_direct(observation)
        repeated = self.resolve_direct(copy.deepcopy(observation), previous_report=first)

        self.assertEqual(first["input_fingerprint"], repeated["input_fingerprint"])
        self.assertFalse(repeated["retry_discovery"])
        self.assertFalse(repeated["host_api_called"])

    def test_declared_tool_without_an_observed_file_reference_stays_unresolved(self) -> None:
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide")],
        )
        report = self.resolve_direct(observation)

        self.assert_report_shape(report)
        self.assertIn("unresolved", _resource(report, "guide")["state"])
        self.assertIn("guide", report["required_unresolved"])
        self.assertTrue(report["read_capability_exposed"])

    def test_filename_match_with_wrong_locator_is_refused(self) -> None:
        source = self.source()
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide", selected_reference="ref-guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[{"reference": "ref-guide", "locator": "PPT/_extension/confirmed-learning/other.md"}],
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    reference="ref-guide",
                    materialized_path=source,
                ),
            ],
        )
        report = self.resolve_direct(observation)

        self.assertNotIn(_resource(report, "guide")["state"], {"readable-native", "readable-attachment"})
        self.assertIn("guide", report["required_unresolved"])
        self.assertTrue(report["read_capability_exposed"])

    def test_ambiguous_duplicate_matches_are_blocked(self) -> None:
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[
                        {"reference": "ref-one", "locator": "PPT/_extension/confirmed-learning/guide.md"},
                        {"reference": "ref-two", "locator": "PPT/_extension/confirmed-learning/guide.md"},
                    ],
                )
            ],
        )
        report = self.resolve_direct(observation)

        self.assertEqual(report["status"], "blocked")
        self.assertIn("ambiguous", _resource(report, "guide")["state"])
        self.assertIn("guide", report["required_unresolved"])
        self.assertTrue(report["read_capability_exposed"])

    def test_located_reference_and_matching_native_read_verify_sha256(self) -> None:
        source = self.source(content=b"native library bytes\n")
        expected = _sha256(source)
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide", expected_sha256=expected, selected_reference="ref-guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[{"reference": "ref-guide", "locator": "PPT/_extension/confirmed-learning/guide.md"}],
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    reference="ref-guide",
                    materialized_path=source,
                ),
            ],
        )
        report = self.resolve_direct(observation)

        self.assert_report_shape(report)
        row = _resource(report, "guide")
        self.assertEqual(report["status"], "ready")
        self.assertEqual(row["state"], "readable-native")
        self.assertFalse(report["write_verified"])
        self.assertTrue(report["read_capability_exposed"])
        self.assertFalse(report["host_api_called"])

    def test_configured_non_ppt_locator_can_resolve_a_native_file(self) -> None:
        source = self.source(content=b"owner library bytes\n")
        locator = "OwnerLibrary/references/guide.md"
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[
                self.resource(
                    "guide",
                    host_locator=locator,
                    expected_sha256=_sha256(source),
                    selected_reference="ref-guide",
                )
            ],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[{"reference": "ref-guide", "locator": locator}],
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    reference="ref-guide",
                    materialized_path=source,
                ),
            ],
        )
        report = self.resolve_direct(observation)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(_resource(report, "guide")["state"], "readable-native")

    def test_selected_reference_in_different_folder_cannot_fall_back_to_matching_filename(self) -> None:
        source = self.source(content=b"wrong reference bytes\n")
        requested_locator = "PPT/_extension/confirmed-learning/guide.md"
        other_locator = "OwnerLibrary/archive/guide.md"
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide", selected_reference="ref-b")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[
                        {"reference": "ref-a", "locator": requested_locator},
                        {"reference": "ref-b", "locator": other_locator},
                    ],
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    reference="ref-a",
                    materialized_path=source,
                ),
            ],
        )
        try:
            report = self.resolve_direct(observation)
        except ValueError:
            return

        self.assertNotEqual(report["status"], "ready")
        self.assertNotIn(_resource(report, "guide")["state"], {"readable-native", "readable-attachment"})
        self.assertIn("guide", report["required_unresolved"])

    def test_read_reference_mismatch_cannot_become_readable(self) -> None:
        source = self.source()
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide", selected_reference="ref-guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[{"reference": "ref-guide", "locator": "PPT/_extension/confirmed-learning/guide.md"}],
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    reference="ref-other",
                    materialized_path=source,
                ),
            ],
        )
        report = self.resolve_direct(observation)

        self.assertNotIn(_resource(report, "guide")["state"], {"readable-native", "readable-attachment"})
        self.assertIn("guide", report["required_unresolved"])
        self.assertTrue(report["read_capability_exposed"])

    def test_denied_and_error_reads_keep_the_bound_reference(self) -> None:
        for failure_status in ("denied", "error"):
            with self.subTest(status=failure_status):
                observation = self.observation(
                    tools=[self.tool("library-reader")],
                    resources=[self.resource("guide", selected_reference="ref-guide")],
                    attempts=[
                        self.attempt(
                            "guide",
                            "library-reader",
                            "locate",
                            matches=[
                                {
                                    "reference": "ref-guide",
                                    "locator": "PPT/_extension/confirmed-learning/guide.md",
                                }
                            ],
                        ),
                        self.attempt(
                            "guide",
                            "library-reader",
                            "read",
                            status=failure_status,
                            reference="ref-guide",
                        ),
                    ],
                )
                report = self.resolve_direct(observation)

                row = _resource(report, "guide")
                self.assertEqual(row["reference"], "ref-guide")
                self.assertNotIn(row["state"], {"readable-native", "readable-attachment"})
                self.assertIn("guide", report["required_unresolved"])
                self.assertTrue(report["read_capability_exposed"])

        source = self.source(content=b"latest attempt wins\n")
        earlier_success_later_denied = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide", selected_reference="ref-guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[
                        {
                            "reference": "ref-guide",
                            "locator": "PPT/_extension/confirmed-learning/guide.md",
                        }
                    ],
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    status="ok",
                    reference="ref-guide",
                    materialized_path=source,
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    status="denied",
                    reference="ref-guide",
                ),
            ],
        )
        denied_report = self.resolve_direct(earlier_success_later_denied)
        denied_row = _resource(denied_report, "guide")
        self.assertEqual(denied_row["reference"], "ref-guide")
        self.assertEqual(denied_row["state"], "read-denied")
        self.assertIn("guide", denied_report["required_unresolved"])

        earlier_denied_later_success = copy.deepcopy(earlier_success_later_denied)
        earlier_denied_later_success["attempts"][-2], earlier_denied_later_success["attempts"][-1] = (
            earlier_denied_later_success["attempts"][-1],
            earlier_denied_later_success["attempts"][-2],
        )
        readable_report = self.resolve_direct(earlier_denied_later_success)
        readable_row = _resource(readable_report, "guide")
        self.assertEqual(readable_row["reference"], "ref-guide")
        self.assertEqual(readable_row["state"], "readable-native")
        self.assertNotIn("guide", readable_report["required_unresolved"])

    def test_hash_mismatch_cannot_become_readable(self) -> None:
        source = self.source()
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide", expected_sha256="0" * 64, selected_reference="ref-guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[{"reference": "ref-guide", "locator": "PPT/_extension/confirmed-learning/guide.md"}],
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    reference="ref-guide",
                    materialized_path=source,
                ),
            ],
        )
        report = self.resolve_direct(observation)

        self.assertNotIn(_resource(report, "guide")["state"], {"readable-native", "readable-attachment"})
        self.assertIn("guide", report["required_unresolved"])
        self.assertTrue(report["read_capability_exposed"])

    def test_explicit_current_chat_attachment_is_readable_but_not_native_library(self) -> None:
        source = self.source("attachment.txt", b"current chat attachment\n")
        observation = self.observation(
            tools=[self.tool("chat-file-reader", kind="current-chat-file")],
            resources=[
                self.resource(
                    "attachment",
                    logical_uri="library://owner/attachment.txt",
                    host_locator="PPT/_extension/confirmed-learning/attachment.txt",
                    explicit_attachment_ref="attachment-ref",
                )
            ],
            attempts=[
                self.attempt(
                    "attachment",
                    "chat-file-reader",
                    "locate",
                    matches=[{"reference": "attachment-ref", "locator": "PPT/_extension/confirmed-learning/attachment.txt"}],
                ),
                self.attempt(
                    "attachment",
                    "chat-file-reader",
                    "read",
                    reference="attachment-ref",
                    materialized_path=source,
                ),
            ],
        )
        report = self.resolve_direct(observation)

        row = _resource(report, "attachment")
        self.assertEqual(report["status"], "ready")
        self.assertEqual(row["state"], "readable-attachment")
        self.assertNotEqual(row["state"], "readable-native")
        self.assertFalse(row.get("library_access_verified", True))
        self.assertFalse(report.get("library_access_verified", True))
        self.assertTrue(report["read_capability_exposed"])
        self.assertFalse(report["write_verified"])

    def test_declared_write_operation_does_not_verify_a_write(self) -> None:
        source = self.source(content=b"read-only verification bytes\n")
        before = source.read_bytes()
        observation = self.observation(
            tools=[self.tool("library-reader-writer", operations=("locate", "read", "write"))],
            resources=[self.resource("guide", expected_sha256=_sha256(source), selected_reference="ref-guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader-writer",
                    "locate",
                    matches=[{"reference": "ref-guide", "locator": "PPT/_extension/confirmed-learning/guide.md"}],
                ),
                self.attempt(
                    "guide",
                    "library-reader-writer",
                    "read",
                    reference="ref-guide",
                    materialized_path=source,
                ),
            ],
        )
        report = self.resolve_direct(observation)

        self.assertTrue(report["read_capability_exposed"])
        self.assertIs(report["write_verified"], False)
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse(report["host_api_called"])

    def test_non_library_tools_do_not_expose_native_library_capabilities(self) -> None:
        other_report = self.resolve_direct(
            self.observation(
                tools=[self.tool("permission-service", kind="other", operations=("read", "write"))],
                resources=[self.resource("guide")],
            )
        )
        self.assertFalse(other_report["read_capability_exposed"])
        self.assertFalse(other_report["write_capability_exposed"])
        self.assertFalse(other_report["write_verified"])

        attachment_report = self.resolve_direct(
            self.observation(
                tools=[self.tool("chat-file", kind="current-chat-file", operations=("read", "write"))],
                resources=[
                    self.resource(
                        "guide",
                        explicit_attachment_ref="attachment-ref",
                    )
                ],
            )
        )
        self.assertTrue(attachment_report["read_capability_exposed"])
        self.assertFalse(attachment_report["write_capability_exposed"])
        self.assertFalse(attachment_report["write_verified"])

    def test_new_observed_tool_or_session_allows_a_discovery_retry(self) -> None:
        unknown = self.observation(
            resources=[self.resource("guide", logical_uri="library://openai/guide.md")],
            authorization_granted=True,
        )
        first = self.resolve_direct(unknown)

        with_tool = copy.deepcopy(unknown)
        with_tool["tools"] = [self.tool("new-library-reader")]
        with_tool["attempts"] = [
            self.attempt(
                "guide",
                "new-library-reader",
                "locate",
                matches=[{"reference": "ref-guide", "locator": "PPT/_extension/confirmed-learning/guide.md"}],
            )
        ]
        tool_retry = self.resolve_direct(with_tool, previous_report=first)
        self.assertTrue(tool_retry["retry_discovery"])

        new_session = copy.deepcopy(unknown)
        new_session["session_id"] = "host-access-new-session"
        session_retry = self.resolve_direct(new_session, previous_report=first)
        self.assertTrue(session_retry["retry_discovery"])

    def test_malformed_ids_and_undeclared_operations_are_rejected(self) -> None:
        from scripts.cloud_learning_cli import CloudLearningError

        bad_id = self.observation(resources=[self.resource("bad id")])
        with self.assertRaises(CloudLearningError):
            self.resolve_direct(bad_id)

        undeclared = self.observation(
            tools=[self.tool("locator-only", operations=("locate",))],
            resources=[self.resource("guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "locator-only",
                    "read",
                    reference="ref-guide",
                    materialized_path=self.source(),
                )
            ],
        )
        with self.assertRaises(CloudLearningError):
            self.resolve_direct(undeclared)

    def test_resolver_reads_only_observed_materialized_file_and_leaves_package_untouched(self) -> None:
        source = self.source(content=b"do not mutate this observed file\n")
        before_bytes = source.read_bytes()
        before_files = {
            path.relative_to(ROOT): path.read_bytes()
            for path in ROOT.rglob("*")
            if path.is_file()
        }
        observation = self.observation(
            tools=[self.tool("library-reader")],
            resources=[self.resource("guide", expected_sha256=_sha256(source), selected_reference="ref-guide")],
            attempts=[
                self.attempt(
                    "guide",
                    "library-reader",
                    "locate",
                    matches=[{"reference": "ref-guide", "locator": "PPT/_extension/confirmed-learning/guide.md"}],
                ),
                self.attempt(
                    "guide",
                    "library-reader",
                    "read",
                    reference="ref-guide",
                    materialized_path=source,
                ),
            ],
        )
        report = self.resolve_cli(observation)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(source.read_bytes(), before_bytes)
        after_files = {
            path.relative_to(ROOT): path.read_bytes()
            for path in ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after_files, before_files)
        self.assertFalse(report["host_api_called"])


if __name__ == "__main__":
    unittest.main()
