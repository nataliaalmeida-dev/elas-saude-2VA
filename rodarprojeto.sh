#!/bin/bash

# ==============================================================================
# Script de Inicialização - Elas Saúde
# Sistema: Zorin OS / Ubuntu
# ==============================================================================

# Cores para saída
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Funções auxiliares
info() { echo -e "${BLUE}${BOLD}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}${BOLD}[SUCESSO]${NC} $1"; }
warn() { echo -e "${YELLOW}${BOLD}[AVISO]${NC} $1"; }
error() { echo -e "${RED}${BOLD}[ERRO]${NC} $1"; exit 1; }

echo -e "${BLUE}${BOLD}"
echo "=========================================================="
echo "    🚀 INICIALIZANDO O PROJETO ELAS SAÚDE"
echo "=========================================================="
echo -e "${NC}"

# 1. Verificar se está no diretório correto
if [ ! -f "pyproject.toml" ]; then
    error "Arquivo pyproject.toml não encontrado. Execute este script na raiz do projeto."
fi

# 2. Solicitar sudo logo no início
info "Solicitando permissões administrativas..."
sudo -v

# 3. Verificar/Instalar Docker
if ! command -v docker &> /dev/null; then
    info "Instalando Docker e Docker Compose..."
    sudo apt update && sudo apt install -y docker.io docker-compose
    sudo systemctl enable --now docker
    success "Docker instalado."
else
    success "Docker já está instalado."
fi

# 4. Verificar Permissões do Docker
if ! groups $USER | grep &>/dev/null "\bdocker\b"; then
    info "Adicionando seu usuário ao grupo docker..."
    sudo usermod -aG docker $USER
    warn "Você foi adicionado ao grupo docker. Para que isso tenha efeito pleno sem reiniciar, usaremos um sub-shell."
    USER_ADDED_TO_GROUP=true
else
    success "Permissões do Docker OK."
fi

# 5. Verificar/Instalar UV (Python Manager)
if ! command -v uv &> /dev/null; then
    info "Instalando UV (Gerenciador Python)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Adicionar ao PATH da sessão atual
    export PATH="$HOME/.cargo/bin:$PATH"
    success "UV instalado."
else
    success "UV já está instalado."
fi

# 6. Rodar o projeto
run_project() {
    echo -e "\n${BLUE}${BOLD}--- Iniciando Serviços ---${NC}"
    
    info "Subindo Banco de Dados (Docker)..."
    docker-compose up -d
    
    info "Aguardando Banco de Dados inicializar (5s)..."
    sleep 5
    
    info "Sincronizando ambiente e dependências (UV Sync)..."
    uv sync
    
    info "Iniciando aplicação com UV..."
    uv run app.py
}

# Execução principal
if [ "$USER_ADDED_TO_GROUP" = true ]; then
    # Se acabamos de adicionar ao grupo, precisamos do sg para rodar sem logout
    exec sg docker -c "$(declare -f info success warn error run_project); run_project"
else
    run_project
fi
