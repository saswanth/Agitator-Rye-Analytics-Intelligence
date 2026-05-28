# Agitator Rye — Start Both Servers
# Run from the workspace root: .\start.ps1

$Root = $PSScriptRoot

Write-Host "`n== Agitator Rye ==" -ForegroundColor Cyan
Write-Host "Starting Backend (FastAPI) and Frontend (Vite)...`n" -ForegroundColor Gray

# Start Backend
$backendJob = Start-Job -ScriptBlock {
    param($r)
    Set-Location "$r\backend"
    & "C:\Users\SASWANTH\Anaconda3\envs\agents\python.exe" run.py
} -ArgumentList $Root

# Start Frontend
$frontendJob = Start-Job -ScriptBlock {
    param($r)
    Set-Location "$r\frontend"
    npm run dev
} -ArgumentList $Root

Write-Host "Backend API   → http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend UI   → http://localhost:5173" -ForegroundColor Green
Write-Host "API Docs      → http://localhost:8000/docs" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop both servers.`n" -ForegroundColor Yellow

try {
    while ($true) {
        Receive-Job $backendJob -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "[Backend] $_" -ForegroundColor DarkCyan }
        Receive-Job $frontendJob -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "[Frontend] $_" -ForegroundColor DarkMagenta }
        Start-Sleep -Milliseconds 500
    }
} finally {
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host "`nServers stopped." -ForegroundColor Yellow
}
