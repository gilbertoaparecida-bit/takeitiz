# Usa Python 3.9 que é mais leve e compatível com as rodas prontas (evita compilação)
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala apenas o essencial do sistema para rodar (evita tralha desnecessária)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia os requisitos
COPY requirements.txt .

# Instala as bibliotecas. O --only-binary diz para baixar versões prontas em vez de compilar
RUN pip3 install --no-cache-dir -r requirements.txt

# Copia o resto do site
COPY . .

# Expõe a porta correta
EXPOSE 8501

# Comando para iniciar
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
