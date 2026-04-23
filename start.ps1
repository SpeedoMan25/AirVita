# AirVita — Windows Start Script
# Detects your LAN IP, passes it to the backend container, and opens the browser.

$IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback|vEthernet|WSL|Docker' -and $_.IPAddress -notlike '169.*' } | Select-Object -First 1).IPAddress

if (-not $IP) {
    $IP = "127.0.0.1"
}

Write-Host ""
Write-Host "Starting AirVita..." -ForegroundColor Cyan
$url = "https://${IP}:5173"
Write-Host "Dashboard will open at: $url" -ForegroundColor Green
Write-Host ""

# Set HOST_IP so docker-compose passes it to the backend container
$env:HOST_IP = $IP

# Open browser after a short delay
Start-Job -ScriptBlock {
    param($targetUrl)
    Start-Sleep -Seconds 8
    Start-Process $targetUrl
} -ArgumentList $url | Out-Null

# Start Docker
docker-compose up --build
