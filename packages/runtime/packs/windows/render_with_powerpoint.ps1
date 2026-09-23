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

function Get-HResultHex {
    param([Parameter(Mandatory = $true)][System.Exception]$Exception)

    $current = $Exception
    $signed = $null
    for ($depth = 0; $depth -lt 16 -and $null -ne $current; $depth++) {
        try {
            $signed = [int64]$current.HResult
            if ($null -eq $current.InnerException) {
                break
            }
            $current = $current.InnerException
        }
        catch {
            break
        }
    }
    if ($null -eq $signed) {
        return $null
    }

    if ($signed -lt 0) {
        $signed += 4294967296
    }
    return ('0x{0:X8}' -f $signed)
}

function New-RendererFailure {
    param(
        [Parameter(Mandatory = $true)][string]$Operation,
        [Parameter(Mandatory = $true)][string]$Message,
        [System.Exception]$InnerException
    )

    $hresult = $null
    if ($null -ne $InnerException) {
        $hresult = Get-HResultHex -Exception $InnerException
    }
    $details = "PowerPoint renderer operation '$Operation' failed"
    if ($null -ne $hresult) {
        $details += " (HRESULT $hresult)"
    }
    if (-not [string]::IsNullOrWhiteSpace($Message)) {
        $details += ": $Message"
    }

    if ($null -eq $InnerException) {
        $failure = [System.InvalidOperationException]::new($details)
    }
    else {
        $failure = [System.InvalidOperationException]::new($details, $InnerException)
    }
    $failure.Data['RendererOperation'] = $Operation
    if ($null -ne $hresult) {
        $failure.Data['HResultHex'] = $hresult
    }
    return $failure
}

function Invoke-RendererOperation {
    param(
        [Parameter(Mandatory = $true)][string]$Operation,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )

    try {
        & $Action
    }
    catch {
        $message = $_.Exception.Message
        $failure = New-RendererFailure -Operation $Operation -Message $message -InnerException $_.Exception
        throw $failure
    }
}

function Invoke-RendererCleanup {
    param(
        [Parameter(Mandatory = $true)][string]$Operation,
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[string]]$Failures
    )

    try {
        & $Action | Out-Null
        return $true
    }
    catch {
        $hresult = Get-HResultHex -Exception $_.Exception
        $diagnostic = "Cleanup operation '$Operation' failed"
        if ($null -ne $hresult) {
            $diagnostic += " (HRESULT $hresult)"
        }
        $diagnostic += ": $($_.Exception.Message)"
        $Failures.Add($diagnostic) | Out-Null
        return $false
    }
}

function Get-OutputState {
    param([Parameter(Mandatory = $true)][string]$Path)

    $state = @{}
    foreach ($file in @(Get-ChildItem -LiteralPath $Path -File -ErrorAction Stop)) {
        $state[$file.FullName] = "$($file.Length)|$($file.LastWriteTimeUtc.Ticks)"
    }
    return $state
}

function Get-PresentationCount {
    param([Parameter(Mandatory = $true)]$Application)

    try {
        $presentations = $Application.Presentations
        if ($null -eq $presentations) {
            return [pscustomobject]@{
                Known = $false
                Count = $null
                Error = 'PowerPoint returned no Presentations collection.'
            }
        }

        $rawCount = $presentations.Count
        if ($null -eq $rawCount) {
            return [pscustomobject]@{
                Known = $false
                Count = $null
                Error = 'PowerPoint returned no presentation count.'
            }
        }

        try {
            $count = [int]$rawCount
        }
        catch {
            return [pscustomobject]@{
                Known = $false
                Count = $null
                Error = "PowerPoint returned an invalid presentation count: $rawCount"
            }
        }
        if ($count -lt 0) {
            return [pscustomobject]@{
                Known = $false
                Count = $null
                Error = "PowerPoint returned a negative presentation count: $count"
            }
        }
        return [pscustomobject]@{
            Known = $true
            Count = $count
            Error = $null
        }
    }
    catch {
        $hresult = Get-HResultHex -Exception $_.Exception
        $errorText = $_.Exception.Message
        if ($null -ne $hresult) {
            $errorText += " (HRESULT $hresult)"
        }
        return [pscustomobject]@{
            Known = $false
            Count = $null
            Error = $errorText
        }
    }
}

function Release-RendererReference {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        $Reference,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[string]]$Failures
    )

    if ($null -eq $Reference) {
        return
    }

    Invoke-RendererCleanup -Operation "Release$Name" -Failures $Failures -Action {
        # Test doubles are ordinary PowerShell objects; production references are COM RCWs.
        if ([Runtime.InteropServices.Marshal]::IsComObject($Reference)) {
            [Runtime.InteropServices.Marshal]::FinalReleaseComObject($Reference) | Out-Null
        }
    } | Out-Null
}

$inputPath = (Resolve-Path -LiteralPath $InputPptx -ErrorAction Stop).Path
if ([IO.Path]::GetExtension($inputPath) -ne '.pptx') {
    throw 'InputPptx must be a .pptx file.'
}
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)

$application = $null
$presentation = $null
$applicationCreated = $false
$primaryError = $null
$cleanupFailures = [System.Collections.Generic.List[string]]::new()
$cleanupIncomplete = [System.Collections.Generic.List[string]]::new()
$ownershipUnclear = $false
$otherPresentationObserved = $false
$beforeOutputState = $null
$renderedFiles = @()

try {
    $existingPowerPoint = @(Invoke-RendererOperation -Operation 'Preflight' -Action {
        Get-Process -Name 'POWERPNT' -ErrorAction SilentlyContinue
    } | Where-Object { $null -ne $_ })
    if ($existingPowerPoint.Count -gt 0) {
        $processDetails = @(
            $existingPowerPoint | ForEach-Object {
                if ($null -ne $_.Id) {
                    "PID=$($_.Id)"
                }
                else {
                    'POWERPNT'
                }
            }
        ) -join ', '
        $refusal = New-RendererFailure -Operation 'Preflight' -Message (
            "an existing POWERPNT process was detected ($processDetails); COM creation did not start"
        )
        throw $refusal
    }

    [IO.Directory]::CreateDirectory($outputPath) | Out-Null
    $beforeOutputState = Get-OutputState -Path $outputPath

    $application = Invoke-RendererOperation -Operation 'CreateApplication' -Action {
        New-Object -ComObject PowerPoint.Application
    }
    if ($null -eq $application) {
        throw (New-RendererFailure -Operation 'CreateApplication' -Message 'PowerPoint returned no application object.')
    }
    $applicationCreated = $true

    $openResult = @(Invoke-RendererOperation -Operation 'Open' -Action {
        $application.Presentations.Open($inputPath, $true, $true, $false)
    })
    if ($openResult.Count -ne 1 -or $null -eq $openResult[0]) {
        throw (New-RendererFailure -Operation 'Open' -Message 'PowerPoint returned no presentation object.')
    }
    $presentation = $openResult[0]

    Invoke-RendererOperation -Operation 'Export' -Action {
        $presentation.Export($outputPath, 'PNG', $Width, $Height)
    } | Out-Null

    $renderedFiles = @(Invoke-RendererOperation -Operation 'OutputValidation' -Action {
        $allFiles = @(Get-ChildItem -LiteralPath $outputPath -File -ErrorAction Stop | Sort-Object Name)
        $newFiles = @(
            $allFiles | Where-Object {
                $oldState = $beforeOutputState[$_.FullName]
                $newState = "$($_.Length)|$($_.LastWriteTimeUtc.Ticks)"
                ($null -eq $oldState) -or ($oldState -ne $newState)
            }
        )
        if ($newFiles.Count -eq 0) {
            throw 'Export completed without creating or changing an output file.'
        }
        $emptyFiles = @($newFiles | Where-Object { $_.Length -le 0 })
        if ($emptyFiles.Count -gt 0) {
            throw "Export created empty output file(s): $((@($emptyFiles | ForEach-Object Name) -join ', '))"
        }
        $allFiles | Select-Object FullName, Length
    })
}
catch {
    $primaryError = $_
}
finally {
    if ($applicationCreated -and $null -ne $application) {
        $inventoryBeforeClose = Get-PresentationCount -Application $application
        if (-not $inventoryBeforeClose.Known) {
            $ownershipUnclear = $true
            $cleanupIncomplete.Add("could not determine presentation ownership before cleanup: $($inventoryBeforeClose.Error)") | Out-Null
        }
        elseif ($inventoryBeforeClose.Count -gt 1) {
            $otherPresentationObserved = $true
            $cleanupIncomplete.Add("PowerPoint had $($inventoryBeforeClose.Count) presentations before cleanup; the session may be shared") | Out-Null
        }
        elseif ($null -ne $presentation -and $inventoryBeforeClose.Count -lt 1) {
            $ownershipUnclear = $true
            $cleanupIncomplete.Add('PowerPoint reported no open presentation while this renderer still held one') | Out-Null
        }
    }

    if ($null -ne $presentation) {
        $closeSucceeded = Invoke-RendererCleanup -Operation 'ClosePresentation' -Failures $cleanupFailures -Action {
            $presentation.Close()
        }
        if (-not $closeSucceeded) {
            $ownershipUnclear = $true
        }
        Release-RendererReference -Name 'Presentation' -Reference $presentation -Failures $cleanupFailures
        $presentation = $null
    }

    $safeToQuit = $false
    if ($applicationCreated -and $null -ne $application) {
        $inventoryAfterClose = Get-PresentationCount -Application $application
        if (-not $inventoryAfterClose.Known) {
            $ownershipUnclear = $true
            $cleanupIncomplete.Add("could not determine presentation ownership before application cleanup: $($inventoryAfterClose.Error)") | Out-Null
        }
        elseif ($inventoryAfterClose.Count -gt 0) {
            $otherPresentationObserved = $true
            $cleanupIncomplete.Add("PowerPoint still has $($inventoryAfterClose.Count) presentation(s); application was left running") | Out-Null
        }
        elseif (-not $ownershipUnclear -and -not $otherPresentationObserved) {
            $safeToQuit = $true
        }
    }

    if ($applicationCreated -and $null -ne $application) {
        if ($safeToQuit) {
            Invoke-RendererCleanup -Operation 'QuitApplication' -Failures $cleanupFailures -Action {
                $application.Quit()
            } | Out-Null
        }
        else {
            $cleanupIncomplete.Add('application Quit was skipped because session ownership was not safe to establish') | Out-Null
        }
        Release-RendererReference -Name 'Application' -Reference $application -Failures $cleanupFailures
        $application = $null
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()

    if ($cleanupIncomplete.Count -gt 0) {
        [Console]::Error.WriteLine(
            "PowerPoint renderer cleanup incomplete: $($cleanupIncomplete -join '; ')"
        )
    }
}

if ($null -ne $primaryError) {
    if ($cleanupFailures.Count -gt 0) {
        $primaryException = $primaryError.Exception
        $cleanupText = $cleanupFailures -join '; '
        $combinedMessage = "$($primaryException.Message) Cleanup diagnostics: $cleanupText"
        $combined = [System.InvalidOperationException]::new($combinedMessage, $primaryException)
        if ($primaryException.Data.Contains('RendererOperation')) {
            $combined.Data['RendererOperation'] = $primaryException.Data['RendererOperation']
        }
        if ($primaryException.Data.Contains('HResultHex')) {
            $combined.Data['HResultHex'] = $primaryException.Data['HResultHex']
        }
        throw $combined
    }
    throw $primaryError
}

if ($cleanupFailures.Count -gt 0) {
    throw (New-RendererFailure -Operation 'Cleanup' -Message ($cleanupFailures -join '; '))
}

$renderedFiles
