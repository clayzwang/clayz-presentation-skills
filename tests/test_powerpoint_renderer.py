from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "packages" / "runtime" / "packs" / "windows" / "render_with_powerpoint.ps1"
POWERSHELL = Path(r"C:\Program Files\PowerShell\7\pwsh.exe")


def _ps_quote(value: str | Path) -> str:
    """Quote a trusted test path for a single quoted PowerShell string."""

    return "'" + str(value).replace("'", "''") + "'"


def _driver(mode: str, existing_process: bool, output_directory: Path, input_file: Path) -> str:
    """Build an executable PowerShell driver with controllable COM/process doubles."""

    mode_literal = _ps_quote(mode)
    output_literal = _ps_quote(output_directory)
    renderer_literal = _ps_quote(RENDERER)
    input_literal = _ps_quote(input_file)
    existing_literal = "$true" if existing_process else "$false"
    return f"""
$ErrorActionPreference = 'Stop'
$state = [pscustomobject]@{{
    Log = [System.Collections.Generic.List[string]]::new()
    Mode = {mode_literal}
    Existing = {existing_literal}
}}

$presentations = [pscustomobject]@{{ Count = 0; State = $state }}
$presentations | Add-Member -MemberType ScriptMethod -Name Open -Value {{
    param($file, $readOnly, $untitled, $withWindow)
    [void]$this.State.Log.Add(("Open:{{0}}|{{1}}|{{2}}|{{3}}" -f $file, $readOnly, $untitled, $withWindow))
    if ($this.State.Mode -eq 'open-fail') {{
        throw [System.Runtime.InteropServices.COMException]::new('synthetic Open failure', [int]-2147467259)
    }}
    $presentation = [pscustomobject]@{{ State = $this.State; Collection = $this }}
    $presentation | Add-Member -MemberType ScriptMethod -Name Export -Value {{
        param($path, $format, $width, $height)
        [void]$this.State.Log.Add(("Export:{{0}}|{{1}}|{{2}}|{{3}}" -f $path, $format, $width, $height))
        if ($this.State.Mode -in @('export-fail', 'export-close-fail')) {{
            throw [System.Runtime.InteropServices.COMException]::new('synthetic Export failure', [int]-2147467259)
        }}
        if ($this.State.Mode -eq 'join-during-export') {{ $this.Collection.Count = 2 }}
        [IO.Directory]::CreateDirectory($path) | Out-Null
        if ($this.State.Mode -in @('no-output', 'old-only')) {{ return }}
        if ($this.State.Mode -eq 'empty-output') {{
            [IO.File]::WriteAllBytes((Join-Path $path 'slide1.png'), [byte[]]@())
            return
        }}
        [IO.File]::WriteAllBytes((Join-Path $path 'slide1.png'), [byte[]](1, 2, 3))
    }} | Out-Null
    $presentation | Add-Member -MemberType ScriptMethod -Name Close -Value {{
        [void]$this.State.Log.Add('ClosePresentation')
        if ($this.State.Mode -in @('close-fail', 'export-close-fail')) {{
            throw [System.Runtime.InteropServices.COMException]::new('synthetic Close failure', [int]-2147467259)
        }}
        if ($this.Collection.Count -is [int] -and $this.Collection.Count -gt 1) {{
            $this.Collection.Count = $this.Collection.Count - 1
        }}
        else {{ $this.Collection.Count = 0 }}
    }} | Out-Null
    if ($this.State.Mode -eq 'shared') {{ $this.Count = 2 }}
    elseif ($this.State.Mode -eq 'ownership-unknown') {{ $this.Count = 'unknown' }}
    else {{ $this.Count = 1 }}
    return $presentation
}} | Out-Null

$application = [pscustomobject]@{{ Presentations = $presentations; State = $state }}
$application | Add-Member -MemberType ScriptMethod -Name Quit -Value {{
    [void]$this.State.Log.Add('QuitApplication')
    if ($this.State.Mode -eq 'quit-fail') {{
        throw [System.Runtime.InteropServices.COMException]::new('synthetic Quit failure', [int]-2147467259)
    }}
}} | Out-Null
$fakeApplication = $application

function global:New-Object {{
    param([string]$ComObject)
    [void]$state.Log.Add(("New-Object:{{0}}" -f $ComObject))
    return $fakeApplication
}}
function global:Get-Process {{
    param([string]$Name, [object]$ErrorAction)
    if ($state.Existing) {{ [pscustomobject]@{{ Id = 777; ProcessName = 'POWERPNT' }} }}
}}

$status = 0
$errorText = ''
try {{
    & {renderer_literal} -InputPptx {input_literal} -OutputDirectory {output_literal} -Width 1920 -Height 1080 | Out-Null
}}
catch {{
    $status = 1
    $errorText = $_.Exception.ToString()
}}
$outputFiles = @(
    Get-ChildItem -LiteralPath {output_literal} -File -ErrorAction SilentlyContinue |
        ForEach-Object {{ [pscustomobject]@{{ Name = $_.Name; Length = $_.Length }} }}
)
$result = [pscustomobject]@{{
    Status = $status
    Error = $errorText
    Log = @($state.Log)
    OutputFiles = $outputFiles
}}
Write-Output ('RESULT=' + ($result | ConvertTo-Json -Compress -Depth 5))
exit $status
"""


def _run_case(
    mode: str = "normal", existing_process: bool = False
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], str, str]:
    with tempfile.TemporaryDirectory(prefix="clayz-powerpoint-renderer-") as temporary:
        temporary_root = Path(temporary)
        output_directory = temporary_root / "rendered"
        input_file = temporary_root / "placeholder.pptx"
        input_file.write_bytes(b"synthetic pptx placeholder for renderer lifecycle tests\n")
        if mode == "old-only":
            output_directory.mkdir()
            (output_directory / "old.png").write_bytes(b"old output")
        before_hash = hashlib.sha256(input_file.read_bytes()).hexdigest()
        script = _driver(mode, existing_process, output_directory, input_file)
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        environment = os.environ.copy()
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [
                str(POWERSHELL),
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                encoded,
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        after_hash = hashlib.sha256(input_file.read_bytes()).hexdigest()
    result_lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT=")]
    if not result_lines:
        raise AssertionError(
            f"mock PowerPoint driver did not return a result; rc={completed.returncode}\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed, json.loads(result_lines[-1][len("RESULT=") :]), before_hash, after_hash


class PowerPointRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not POWERSHELL.is_file():
            raise unittest.SkipTest(f"PowerShell 7 is unavailable: {POWERSHELL}")

    def test_normal_path_is_read_only_sized_and_closes_only_its_presentation(self) -> None:
        completed, result, before, after = _run_case()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["Status"], 0)
        log = result["Log"]
        self.assertEqual(log[0], "New-Object:PowerPoint.Application")
        self.assertRegex(log[1], r"Open:.*\|True\|True\|False$")
        self.assertRegex(log[2], r"Export:.*\|PNG\|1920\|1080$")
        self.assertEqual(log[3:], ["ClosePresentation", "QuitApplication"])
        self.assertEqual(result["OutputFiles"], [{"Name": "slide1.png", "Length": 3}])
        self.assertEqual(len(before), 64)
        self.assertEqual(before, after)

        source = RENDERER.read_text(encoding="utf-8")
        self.assertNotIn(".Visible", source)
        self.assertNotIn("Visible =", source)

    def test_existing_powerpoint_is_rejected_before_com_creation(self) -> None:
        completed, result, _, _ = _run_case(existing_process=True)

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["Status"], 1)
        self.assertEqual(result["Log"], [])
        self.assertIn("operation 'Preflight'", result["Error"])
        self.assertIn("existing POWERPNT process", result["Error"])
        self.assertIn("COM creation did not start", result["Error"])

    def test_open_failure_preserves_operation_and_hresult_and_quits_empty_application(self) -> None:
        completed, result, _, _ = _run_case(mode="open-fail")

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["Status"], 1)
        self.assertEqual(result["Log"][0:2], ["New-Object:PowerPoint.Application", result["Log"][1]])
        self.assertIn("Open:", result["Log"][1])
        self.assertEqual(result["Log"][2:], ["QuitApplication"])
        self.assertIn("operation 'Open'", result["Error"])
        self.assertIn("0x80004005", result["Error"])

    def test_export_failure_closes_presentation_and_quits_application(self) -> None:
        completed, result, _, _ = _run_case(mode="export-fail")

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["Status"], 1)
        self.assertEqual(result["Log"][3:], ["ClosePresentation", "QuitApplication"])
        self.assertIn("operation 'Export'", result["Error"])
        self.assertIn("0x80004005", result["Error"])

    def test_cleanup_failures_are_nonzero_and_do_not_hide_primary_operation(self) -> None:
        close_completed, close_result, _, _ = _run_case(mode="close-fail")
        self.assertNotEqual(close_completed.returncode, 0)
        self.assertIn("ClosePresentation", close_result["Error"])
        self.assertIn("0x80004005", close_result["Error"])
        self.assertNotIn("QuitApplication", close_result["Log"])

        quit_completed, quit_result, _, _ = _run_case(mode="quit-fail")
        self.assertNotEqual(quit_completed.returncode, 0)
        self.assertEqual(quit_result["Log"][3:], ["ClosePresentation", "QuitApplication"])
        self.assertIn("QuitApplication", quit_result["Error"])
        self.assertIn("0x80004005", quit_result["Error"])

        combined_completed, combined_result, _, _ = _run_case(mode="export-close-fail")
        self.assertNotEqual(combined_completed.returncode, 0)
        combined_error = combined_result["Error"]
        self.assertIn("operation 'Export'", combined_error)
        self.assertIn("ClosePresentation", combined_error)
        self.assertLess(combined_error.index("operation 'Export'"), combined_error.index("ClosePresentation"))
        self.assertNotIn("QuitApplication", combined_result["Log"])

    def test_shared_or_ambiguous_session_closes_its_presentation_but_never_quits_application(self) -> None:
        for mode in ("shared", "join-during-export", "ownership-unknown"):
            with self.subTest(mode=mode):
                completed, result, _, _ = _run_case(mode=mode)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(result["Status"], 0)
                self.assertIn("ClosePresentation", result["Log"])
                self.assertNotIn("QuitApplication", result["Log"])
                self.assertIn("cleanup incomplete", completed.stderr.lower())
                self.assertEqual(result["OutputFiles"], [{"Name": "slide1.png", "Length": 3}])

    def test_output_validation_rejects_missing_empty_and_unchanged_exports(self) -> None:
        for mode in ("no-output", "empty-output", "old-only"):
            with self.subTest(mode=mode):
                completed, result, before, after = _run_case(mode=mode)
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(result["Status"], 1)
                self.assertIn("operation 'OutputValidation'", result["Error"])
                self.assertEqual(before, after)
                self.assertEqual(result["Log"][3:], ["ClosePresentation", "QuitApplication"])
                if mode == "empty-output":
                    self.assertIn("empty output", result["Error"])
                else:
                    self.assertIn("without creating or changing", result["Error"])
                if mode == "old-only":
                    self.assertEqual(result["OutputFiles"], [{"Name": "old.png", "Length": 10}])


if __name__ == "__main__":
    unittest.main()
