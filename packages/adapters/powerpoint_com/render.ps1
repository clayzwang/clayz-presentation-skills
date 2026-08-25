# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Manifest,
    [Parameter(Mandatory = $true)][string]$OutputPptx,
    [string]$RenderDirectory
)

$ErrorActionPreference = 'Stop'

function Convert-HexColor([string]$Value) {
    $clean = $Value.TrimStart('#')
    if ($clean.Length -ne 6) { throw "Invalid color: $Value" }
    $r = [Convert]::ToInt32($clean.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($clean.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($clean.Substring(4, 2), 16)
    return $r + ($g * 256) + ($b * 65536)
}

function Inches([object]$Value) { return [single]([double]$Value * 72.0) }

function Set-ObjectName([object]$Shape, [object]$Spec) {
    if ($null -ne $Spec.copy_id -and "$($Spec.copy_id)" -ne '') {
        $Shape.Name = "COPY::$($Spec.copy_id)::$($Spec.object_id)"
    }
    else { $Shape.Name = "$($Spec.object_id)" }
}

function Apply-FillAndLine([object]$Shape, [object]$Options) {
    if ($null -ne $Options.fill -and $null -ne $Options.fill.color) {
        $Shape.Fill.Visible = -1
        $Shape.Fill.Solid()
        $Shape.Fill.ForeColor.RGB = Convert-HexColor "$($Options.fill.color)"
        if ($null -ne $Options.fill.transparency) { $Shape.Fill.Transparency = [single]([double]$Options.fill.transparency / 100.0) }
    }
    else { $Shape.Fill.Visible = 0 }
    if ($null -ne $Options.line -and $null -ne $Options.line.color) {
        $Shape.Line.Visible = -1
        $Shape.Line.ForeColor.RGB = Convert-HexColor "$($Options.line.color)"
        if ($null -ne $Options.line.width) { $Shape.Line.Weight = [single]$Options.line.width }
    }
    else { $Shape.Line.Visible = 0 }
}

function Apply-Text([object]$Shape, [string]$Text, [object]$Options) {
    $range = $Shape.TextFrame.TextRange
    $range.Text = $Text
    $range.Font.Name = if ($null -ne $Options.fontFace) { "$($Options.fontFace)" } else { 'Aptos' }
    if ($null -ne $Options.fontSize) { $range.Font.Size = [single]$Options.fontSize }
    $range.Font.Bold = if ($Options.bold) { -1 } else { 0 }
    $range.Font.Italic = if ($Options.italic) { -1 } else { 0 }
    if ($null -ne $Options.color) { $range.Font.Color.RGB = Convert-HexColor "$($Options.color)" }
    $range.ParagraphFormat.Alignment = switch ("$($Options.align)".ToLowerInvariant()) {
        'center' { 2 }
        'right' { 3 }
        'justify' { 4 }
        default { 1 }
    }
    $margin = if ($null -ne $Options.margin) { Inches $Options.margin } else { 0 }
    $Shape.TextFrame.MarginLeft = $margin
    $Shape.TextFrame.MarginRight = $margin
    $Shape.TextFrame.MarginTop = $margin
    $Shape.TextFrame.MarginBottom = $margin
    $Shape.TextFrame.WordWrap = if ($Options.breakLine -eq $false) { 0 } else { -1 }
    $Shape.TextFrame.VerticalAnchor = switch ("$($Options.valign)".ToLowerInvariant()) {
        'mid' { 3 }
        'middle' { 3 }
        'bottom' { 4 }
        default { 1 }
    }
}

function Add-ManifestObject([object]$Slide, [object]$Spec, [string]$ManifestDirectory) {
    $o = $Spec.options
    $x = Inches $o.x; $y = Inches $o.y; $w = Inches $o.w; $h = Inches $o.h
    $shape = $null
    switch ("$($Spec.type)") {
        'text' {
            $shape = $Slide.Shapes.AddTextbox(1, $x, $y, $w, $h)
            Apply-Text $shape "$($Spec.text)" $o
        }
        'shape' {
            $shapeType = switch ("$($Spec.shape)".Replace('-', '').ToLowerInvariant()) {
                'roundrect' { 5 }
                'ellipse' { 9 }
                'oval' { 9 }
                'chevron' { 52 }
                'hexagon' { 10 }
                'diamond' { 4 }
                'triangle' { 7 }
                default { 1 }
            }
            $shape = $Slide.Shapes.AddShape($shapeType, $x, $y, $w, $h)
            Apply-FillAndLine $shape $o
        }
        'line' {
            $shape = $Slide.Shapes.AddLine($x, $y, $x + $w, $y + $h)
            Apply-FillAndLine $shape $o
        }
        { $_ -in @('image', 'svg') } {
            $asset = "$($Spec.path)"
            if (-not [IO.Path]::IsPathRooted($asset)) { $asset = Join-Path $ManifestDirectory $asset }
            $asset = (Resolve-Path -LiteralPath $asset).Path
            $shape = $Slide.Shapes.AddPicture($asset, 0, -1, $x, $y, $w, $h)
        }
        'table' {
            if ($null -eq $Spec.rows -or $Spec.rows.Count -eq 0) { throw "$($Spec.object_id): rows are required" }
            $columnCount = ($Spec.rows | ForEach-Object { $_.Count } | Measure-Object -Maximum).Maximum
            $shape = $Slide.Shapes.AddTable($Spec.rows.Count, $columnCount, $x, $y, $w, $h)
            for ($row = 0; $row -lt $Spec.rows.Count; $row++) {
                for ($column = 0; $column -lt $Spec.rows[$row].Count; $column++) {
                    $cell = $shape.Table.Cell($row + 1, $column + 1).Shape
                    Apply-Text $cell "$($Spec.rows[$row][$column])" $o
                }
            }
        }
        'chart' { throw "$($Spec.object_id): chart requires python-pptx or Artifact Tool route" }
        default { throw "$($Spec.object_id): unsupported object type $($Spec.type)" }
    }
    Set-ObjectName $shape $Spec
}

$manifestPath = (Resolve-Path -LiteralPath $Manifest).Path
$manifestDirectory = Split-Path -Parent $manifestPath
$specification = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -Depth 100
if ($specification.contract -ne 'io.clayz.presentation.render-manifest/1.0') { throw 'Unsupported render-manifest contract.' }
$outputPath = [IO.Path]::GetFullPath($OutputPptx)
[IO.Directory]::CreateDirectory((Split-Path -Parent $outputPath)) | Out-Null

$application = $null
$presentation = $null
try {
    $application = New-Object -ComObject PowerPoint.Application
    $application.Visible = 0
    $presentation = $application.Presentations.Add()
    $presentation.PageSetup.SlideWidth = Inches 13.333333
    $presentation.PageSetup.SlideHeight = Inches 7.5
    foreach ($slideSpec in $specification.slides) {
        $slide = $presentation.Slides.Add($presentation.Slides.Count + 1, 12)
        $slide.FollowMasterBackground = 0
        $slide.Background.Fill.Solid()
        $slide.Background.Fill.ForeColor.RGB = Convert-HexColor "$($slideSpec.background)"
        foreach ($objectSpec in $slideSpec.objects) { Add-ManifestObject $slide $objectSpec $manifestDirectory }
        if ($null -ne $slideSpec.speaker_notes -and $slideSpec.speaker_notes.Count -gt 0) {
            try { $slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = ($slideSpec.speaker_notes -join "`r`n") } catch { }
        }
    }
    $presentation.SaveAs($outputPath, 24)
    if ($RenderDirectory) {
        $renderPath = [IO.Path]::GetFullPath($RenderDirectory)
        [IO.Directory]::CreateDirectory($renderPath) | Out-Null
        $presentation.Export($renderPath, 'PNG', 1920, 1080)
    }
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

Write-Output "wrote $outputPath"
