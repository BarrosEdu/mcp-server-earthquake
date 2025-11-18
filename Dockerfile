FROM python:3.11-slim

# 1) Pasta de trabalho
WORKDIR /app

# 2) Dependências de sistema: curl + Node/NPM para npx, etc.
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 3) Instalar uv (para usar uvx no yfmcp)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv && \
    ln -s /root/.local/bin/uvx /usr/local/bin/uvx

# 4) Instalar libs Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copiar o código do projeto
COPY . .

# 6) Variáveis padrão (Render vai sobrescrever PORT, mas não tem problema)
ENV PORT=10000

# 7) Comando de start: sobe o MCP server HTTP
CMD ["python", "src/mcp_server_news.py"]
