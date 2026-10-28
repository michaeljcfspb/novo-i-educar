<#
.SYNOPSIS
  Sobe o i-Educar local em um único servidor (Django serve a API e o React).

.EXAMPLE
  .\iniciar-local.ps1
  .\iniciar-local.ps1 -Porta 8080
#>
param(
  [int]$Porta = 8000,
  [switch]$SemSeed
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $raiz ".venv-backend\Scripts\python.exe"

if (-not (Test-Path $python)) {
  Write-Host "Ambiente virtual não encontrado. Criando..." -ForegroundColor Yellow
  python -m venv (Join-Path $raiz ".venv-backend")
  & (Join-Path $raiz ".venv-backend\Scripts\pip.exe") install -r (Join-Path $raiz "backend\requirements-dev.txt")
}

if (-not (Test-Path (Join-Path $raiz "frontend\dist\index.html"))) {
  Write-Host "Build do frontend ausente. Rode: cd frontend; npm install; npm run build" -ForegroundColor Yellow
}

$env:DB_ENGINE = "sqlite"
$env:DJANGO_DEBUG = "True"
$env:DJANGO_SECRET_KEY = "local-dev-nao-use-em-producao"
$ipsLocais = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -notlike "127.*" } |
  Select-Object -ExpandProperty IPAddress)
$hosts = @("localhost", "127.0.0.1", "0.0.0.0") + $ipsLocais
$env:DJANGO_ALLOWED_HOSTS = ($hosts -join ",")
$env:DJANGO_CSRF_TRUSTED_ORIGINS = (@($hosts | ForEach-Object { "http://$_`:${Porta}" }) -join ",")
$env:PYTHONUTF8 = "1"

Push-Location (Join-Path $raiz "backend")
try {
  & $python manage.py migrate --noinput
  if (-not $SemSeed) {
    $temUsuarios = & $python -c "import os,django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup(); from apps.accounts.models import User; print(User.objects.exists())"
    if ($temUsuarios.Trim() -eq "False") {
      Write-Host "Populando dados de demonstração..." -ForegroundColor Cyan
      & $python manage.py seed_demo
    }
  }
  Write-Host ""
  Write-Host "  i-Educar local:  http://localhost:$Porta" -ForegroundColor Green
  Write-Host "  Swagger:         http://localhost:$Porta/api/docs/" -ForegroundColor Green
  Write-Host "  Admin:           http://localhost:$Porta/admin/" -ForegroundColor Green
  Write-Host "  Login: admin@example.com / senha-forte-123" -ForegroundColor Green
  foreach ($ip in $ipsLocais) {
    Write-Host "  Na rede local:   http://${ip}:$Porta" -ForegroundColor DarkGreen
  }
  Write-Host "  (Ctrl+C encerra)" -ForegroundColor DarkGray
  Write-Host ""
  & $python manage.py runserver "0.0.0.0:$Porta" --noreload
}
finally {
  Pop-Location
}
