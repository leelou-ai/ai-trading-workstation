param(
    [switch]$Build
)

$ContainerName = "finally-app"
$ImageName = "finally"
$Port = 8000

# Check Docker is available and running
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
    exit 1
}
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker daemon is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Check for .env file
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "No .env file found. Copying from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "Please edit .env and add your OPENROUTER_API_KEY" -ForegroundColor Yellow
    } else {
        "OPENROUTER_API_KEY=" | Out-File -FilePath ".env" -Encoding UTF8
    }
}

# Stop existing container if running
$existing = docker ps -q -f "name=$ContainerName" 2>$null
if ($existing) {
    Write-Host "Stopping existing container..." -ForegroundColor Yellow
    docker stop $ContainerName | Out-Null
}
$existingAll = docker ps -aq -f "name=$ContainerName" 2>$null
if ($existingAll) {
    docker rm $ContainerName | Out-Null
}

# Build image if needed
$imageExists = docker images -q $ImageName 2>$null
if ($Build -or -not $imageExists) {
    Write-Host "Building Docker image..." -ForegroundColor Cyan
    docker build -t $ImageName .
}

# Run container
Write-Host "Starting FinAlly..." -ForegroundColor Green
docker run -d `
    --name $ContainerName `
    -p "${Port}:8000" `
    -v "finally-data:/app/db" `
    --env-file .env `
    $ImageName

Write-Host ""
Write-Host "FinAlly is running\!" -ForegroundColor Green
Write-Host "   Open: http://localhost:$Port"
Write-Host ""
Write-Host "   To stop:      .\scripts\stop_windows.ps1"
Write-Host "   To view logs: docker logs -f $ContainerName"
