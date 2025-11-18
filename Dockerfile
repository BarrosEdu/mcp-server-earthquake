FROM python:3.11-slim

# 1) Pasta de trabalho
WORKDIR /app

# 2) Dependências de sistema (node + npm → necessário para npx)
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 3) Instalar UV (para rodar uvx)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh 

# Adicionar uv ao PATH
ENV PATH="/root/.local/bin:${PATH}"

# 4) Copiar requirements e instalar dependências python (via pip)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copiar o resto do código
COPY . .

# 6) Porta padrão do Render
ENV PORT=10000

# 7) Comando de inicialização
CMD ["python", "src/mcp_server_news.py"]
