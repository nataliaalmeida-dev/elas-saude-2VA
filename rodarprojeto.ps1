# ==============================================================================
# Script de Inicialização - Elas Saúde
# Sistema: Windows (PowerShell)
# ==============================================================================

$OutputEncoding = [System.Text.UTF8Encoding]::new()

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Success($msg) { Write-Host "[SUCESSO] $msg" -ForegroundColor Green }
function Write-Warning($msg) { Write-Host "[AVISO] $msg" -ForegroundColor Yellow }
function Write-Error([string]$msg) { Write-Host "[ERRO] $msg" -ForegroundColor Red; exit }

Clear-Host
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    🚀 INICIALIZANDO O PROJETO ELAS SAÚDE (WINDOWS)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar se está no diretório correto
if (!(Test-Path "pyproject.toml")) {
    Write-Error "Arquivo pyproject.toml não encontrado. Execute este script na raiz do projeto."
}

# 2. Verificar/Instalar Docker
$dockerPaths = @(
    "$env:ProgramFiles\Docker\Docker\resources\bin",
    "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe"
)

function Find-Docker {
    if (Get-Command docker -ErrorAction SilentlyContinue) { return $true }
    foreach ($path in $dockerPaths) {
        if (Test-Path $path) {
            $binDir = if ($path.EndsWith(".exe")) { Split-Path $path } else { $path }
            $env:Path += ";$binDir"
            return $true
        }
    }
    return $false
}

if (!(Find-Docker)) {
    Write-Warning "Docker nÃ£o encontrado no PATH nem nos caminhos padrÃµes."
    Write-Info "Tentando instalar Docker Desktop via winget (isso pode demorar e exigir permissÃ£o)..."
    winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    
    Write-Warning "InstalaÃ§Ã£o solicitada. Por favor, reinicie o computador se o Docker nÃ£o aparecer em breve."
    Write-Info "Tentando localizar o executÃ¡vel recÃ©m-instalado..."
    Start-Sleep -Seconds 10
    if (!(Find-Docker)) {
        Write-Error "Docker Desktop foi instalado mas ainda nÃ£o foi detectado. Por favor, reinicie o Windows e rode este script novamente."
    }
}

# 3. Garantir que o Docker Desktop esteja rodando
Write-Info "Verificando se o serviÃ§o do Docker estÃ¡ ativo..."
$loopCount = 0
while (!(docker info -f '{{.ID}}' 2>$null)) {
    if ($loopCount -eq 0) {
        Write-Warning "Docker instalado mas nÃ£o estÃ¡ respondendo. Tentando abrir o Docker Desktop..."
        if (Test-Path "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe") {
            Start-Process "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
        } else {
            Write-Info "Por favor, abra o aplicativo 'Docker Desktop' manualmente agora."
        }
    }
    
    Write-Info "Aguardando o Docker iniciar (Tentativa $($loopCount + 1)/10)..."
    Start-Sleep -Seconds 10
    $loopCount++
    if ($loopCount -gt 10) {
        Write-Error "O Docker demorou muito para iniciar. Verifique se o Docker Desktop estÃ¡ aberto e tente novamente."
    }
}
Write-Success "Docker estÃ¡ rodando e pronto."

# 4. Verificar/Instalar UV
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Info "Instalando UV (Gerenciador Python)..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path += ";$env:USERPROFILE\.cargo\bin"
    if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Error "UV instalado mas nÃ£o detectado. Tente rodar o script novamente."
    }
}
Write-Success "UV estÃ¡ pronto."

# 4. Rodar o projeto
Write-Host "`n--- Iniciando Serviços ---" -ForegroundColor Cyan

Write-Info "Subindo Banco de Dados (Docker)..."
docker-compose up -d

Write-Info "Aguardando Banco de Dados inicializar (5s)..."
Start-Sleep -Seconds 5

Write-Info "Sincronizando ambiente e dependências (UV Sync)..."
uv sync

Write-Info "Iniciando aplicação com UV..."
uv run app.py
