Write-Host "Checking dependencies..." -ForegroundColor Gray

# Python check
if (-not (python --version 2>$null)) {
    Write-Host "❌ Python not found. Please install Python 3.9+." -ForegroundColor Red
    exit
}

# Node check
if (-not (npm -v 2>$null)) {
    Write-Host "❌ Node.js/npm not found. Please install Node.js." -ForegroundColor Red
    exit
}

# Backend dependencies check
if (-not (python -m uvicorn --version 2>$null)) {
    Write-Host "⚠️  Backend dependencies missing. Installing..." -ForegroundColor Yellow
    python -m pip install -r backend/requirements.txt
}

# Frontend dependencies check
if (-not (Test-Path "frontend/node_modules")) {
    Write-Host "⚠️  Frontend dependencies missing. Installing..." -ForegroundColor Yellow
    cd frontend; npm install; cd ..
}

$comPort = Read-Host "Enter your Pico COM port (e.g., COM3, COM6) [Press Enter for COM6, or type 'MOCK' for simulation]"
if (-not $comPort) {
    $comPort = "COM6"
}

$useMock = "false"
if ($comPort.ToUpper() -eq "MOCK") {
    $useMock = "true"
    $comPort = "NONE"
}

Write-Host ""
Write-Host "Starting AirVita Native on Windows..." -ForegroundColor Cyan
if ($useMock -eq "true") {
    Write-Host "Using Mode: MOCK (Simulation)" -ForegroundColor Yellow
} else {
    Write-Host "Using Serial Port: $comPort" -ForegroundColor Yellow
}

# Start Backend in a new window
Write-Host "Launching Backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; `$env:PYTHONUTF8='1'; `$env:SERIAL_PORT='$comPort'; `$env:MOCK_SERIAL='$useMock'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

# Start Frontend in a new window
Write-Host "Launching Frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "Done! The dashboard will be live at https://localhost:5173 once the servers spin up." -ForegroundColor Green
Write-Host "NOTE: Make sure your Pico is running pico\main.py, not the text dashboard." -ForegroundColor Gray
