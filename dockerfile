# Usa uma imagem Python leve e moderna
FROM python:3.9-slim

# Define o diretório de trabalho dentro do servidor
WORKDIR /app

# Instala dependências do sistema operacional necessárias para lidar com imagens (Pillow)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro (para aproveitar o cache)
COPY requirements.txt .

# Instala as bibliotecas Python do seu projeto
RUN pip3 install -r requirements.txt

# Copia TODO o resto do código (seus .py, .ttf, imagens) para dentro do servidor
COPY . .

# Expõe a porta que o Streamlit usa (padrão do Railway)
EXPOSE 8501

# O comando de verificação de saúde do app
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# O comando que INICIA o seu app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
