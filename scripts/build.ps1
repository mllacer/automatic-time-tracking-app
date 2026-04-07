param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$cleanArgs = @()
if ($Clean.IsPresent) {
    $cleanArgs += "--clean"
}

pyinstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name "TimeTracker" `
    --paths "$root\src" `
    --hidden-import pythoncom `
    --hidden-import pywintypes `
    --hidden-import win32timezone `
    @cleanArgs `
    "$root\run_time_tracker.pyw"
