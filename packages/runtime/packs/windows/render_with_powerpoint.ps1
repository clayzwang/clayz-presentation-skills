# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InputPptx,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [ValidateRange(320, 7680)][int]$Width = 1920,
    [ValidateRange(180, 4320)][int]$Height = 1080
)

$ErrorActionPreference = 'Stop'
$inputPath = (Resolve-Path -LiteralPath $InputPptx).Path
if ([IO.Path]::GetExtension($inputPath) -ne '.pptx') {
    throw 'InputPptx must be a .pptx file.'
}
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($outputPath) | Out-Null

$application = $null
$presentation = $null
try {
    $application = New-Object -ComObject PowerPoint.Application
    $application.Visible = 0
    $presentation = $application.Presentations.Open($inputPath, $true, $true, $false)
    $presentation.Export($outputPath, 'PNG', $Width, $Height)
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null
    }
    if ($null -ne $application) {
        $application.Quit()
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($application) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Get-ChildItem -LiteralPath $outputPath -File | Sort-Object Name | Select-Object FullName, Length
