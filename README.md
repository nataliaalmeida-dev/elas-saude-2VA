# Elas Saúde - Projeto Completo

Este é o sistema de agendamento e gestão para "Elas Saúde".

## Pré-requisitos

Antes de começar, você precisará ter instalado em sua máquina:

- [Python 3.14+](https://www.python.org/)
- [UV](https://github.com/astral-sh/uv) (Gerenciador de pacotes rápido para Python)
- [Docker](https://www.docker.com/) e Docker Compose (para o banco de dados)

## Passo a Passo para Rodar

### 1. Clonar e Acessar o Projeto

```bash
cd elas_saude_projeto_completo
```

### 2. Iniciar o Banco de Dados

O projeto utiliza PostgreSQL via Docker. Para subir o banco, execute:

```bash
docker-compose up -d
```

> **Nota:** O banco será iniciado na porta **5433** conforme configurado no projeto.

### 3. Configurar Variáveis de Ambiente

Certifique-se de que o arquivo `.env` existe na raiz do projeto com as seguintes chaves:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5433/elas_saude
SECRET_KEY=dev-secret-key-change-in-production
```

### 4. Executar a Aplicação

O comando abaixo instalará as dependências automaticamente e iniciará o servidor Flask:

```bash
uv run python app.py
```

Após o comando, a aplicação estará disponível em: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Outros Comandos Úteis

- **Sincronizar ambiente:** `uv sync`
- **Parar banco de dados:** `docker-compose down`
- **Limpar volumes do banco:** `docker-compose down -v`
