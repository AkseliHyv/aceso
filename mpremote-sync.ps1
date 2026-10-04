<#
.SYNOPSIS
    Syncs local files to/from a MicroPython device using mpremote.

.EXAMPLE
    .\sync.ps1 push
    .\sync.ps1 push -Clean
    .\sync.ps1 push -Port COM3
    .\sync.ps1 pull
#>

param (
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("push", "pull")]
    [string]$Command,

    [Parameter(Mandatory=$false)]
    [string]$Port,

    [switch]$Clean
)

# Equivalent to 'set -e' (Stop on error)
$ErrorActionPreference = "Stop"

# Build the base mpremote command arguments
$mpremoteArgs = @()
if ($Port) {
    $mpremoteArgs += "connect", $Port
}

$localDir = Get-Location

switch ($Command) {
    "push" {
        Write-Host "Pushing contents of 'app' to remote:/" -ForegroundColor Cyan
        
        if ($Clean) {
            Write-Host "Wiping remote filesystem..." -ForegroundColor Yellow
            mpremote @mpremoteArgs rm -rv :
        }

        # Navigate into the app folder, copy everything, then go back
        Push-Location "./app"
        try {
            # In mpremote, '.' refers to the current local directory
            mpremote @mpremoteArgs cp -r . :
        }
        finally {
            Pop-Location
        }
    }

    "pull" {
        Write-Host "Pulling remote:/ → '$localDir\app'" -ForegroundColor Cyan
        
        # Ensure the app directory exists before pulling
        if (!(Test-Path "./app")) { New-Item -ItemType Directory -Path "./app" }
        
        mpremote @mpremoteArgs cp -r : ./app/
    }
}

Write-Host "Done." -ForegroundColor Green