# AirVita — Windows Native Start Script
# Runs the backend and frontend locally (outside of Docker) to allow direct USB COM port access.

$comPort = Read-Host "Enter your Pico COM port (e.g., COM3, COM6) [Press Enter for COM6]"
if (-not $comPort) {
    $comPort = "COM6"
}

Write-Host ""
Write-Host "Starting AirVita Native on Windows..." -ForegroundColor Cyan
Write-Host "Using Serial Port: $comPort" -ForegroundColor Yellow

# Start Backend in a new window
Write-Host "Launching Backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; `$env:PYTHONUTF8='1'; `$env:SERIAL_PORT='$comPort'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

# Start Frontend in a new window
Write-Host "Launching Frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "Done! The dashboard will be live at https://localhost:5173 once the servers spin up." -ForegroundColor Green
Write-Host "NOTE: Make sure your Pico is running pico\main.py, not the text dashboard." -ForegroundColor Gray
