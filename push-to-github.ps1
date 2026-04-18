# PWR Railway Deploy - Git Push Script
# This script pushes the deployment configuration to GitHub

$RepoPath = "C:\Users\rdpuser\pwr"
$ErrorActionPreference = "Continue"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PWR Railway Deploy - GitHub Push" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $RepoPath)) {
    Write-Host "❌ Repo path not found: $RepoPath" -ForegroundColor Red
    exit 1
}

cd $RepoPath
Write-Host "✅ Changed to: $RepoPath" -ForegroundColor Green
Write-Host ""

# Try to push
Write-Host "📤 Attempting to push to GitHub..." -ForegroundColor Yellow
$pushOutput = git push origin main 2>&1
$pushExitCode = $LASTEXITCODE

if ($pushExitCode -eq 0) {
    Write-Host "✅ Push successful!" -ForegroundColor Green
    Write-Host $pushOutput
    exit 0
} else {
    Write-Host "⚠️  Push failed. Checking authentication..." -ForegroundColor Yellow
    Write-Host $pushOutput
    Write-Host ""

    # Prompt for GitHub token
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host "  GitHub Authentication Required" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please enter your GitHub Personal Access Token." -ForegroundColor Cyan
    Write-Host "Token: Press Ctrl+V to paste, then Enter" -ForegroundColor Gray
    Write-Host ""

    $token = Read-Host "GitHub Token (will not be displayed)"

    if ([string]::IsNullOrEmpty($token)) {
        Write-Host "❌ No token provided. Cannot proceed." -ForegroundColor Red
        exit 1
    }

    # Configure git with token
    Write-Host ""
    Write-Host "🔐 Configuring git with token..." -ForegroundColor Yellow
    git config --global credential.helper store

    # Try push with token in URL
    $url = "https://qtorb:${token}@github.com/qtorb/pwr.git"
    git remote set-url origin $url

    Write-Host "📤 Retrying push..." -ForegroundColor Yellow
    $retryOutput = git push origin main 2>&1
    $retryExitCode = $LASTEXITCODE

    # Reset remote to normal URL (without token)
    git remote set-url origin "https://github.com/qtorb/pwr.git"

    if ($retryExitCode -eq 0) {
        Write-Host "✅ Push successful!" -ForegroundColor Green
        Write-Host $retryOutput
        Write-Host ""
        Write-Host "🎉 Files pushed to GitHub successfully!" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "❌ Push failed even with token." -ForegroundColor Red
        Write-Host $retryOutput
        exit 1
    }
}
