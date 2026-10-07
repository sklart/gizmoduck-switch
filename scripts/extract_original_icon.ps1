<#
.SYNOPSIS
Extract the embedded icon from the user-supplied Gizmoduck Windows executable.

.DESCRIPTION
The icon is generated locally for the NRO metadata and is intentionally ignored
by Git: the game artwork is not redistributed with the Switch wrapper.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Executable,
    [string] $Output = "assets/icon.jpg"
)

$inputPath = (Resolve-Path -LiteralPath $Executable -ErrorAction Stop).Path
$outputPath = [System.IO.Path]::GetFullPath($Output)
$outputDirectory = Split-Path -Parent $outputPath
[System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null

Add-Type -AssemblyName System.Drawing
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon($inputPath)
if ($null -eq $icon) {
    throw "The executable does not contain an extractable application icon: $inputPath"
}

try {
    $bitmap = $icon.ToBitmap()
    try {
        $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    }
    finally {
        $bitmap.Dispose()
    }
}
finally {
    $icon.Dispose()
}

Write-Host "Created $outputPath from $inputPath"
