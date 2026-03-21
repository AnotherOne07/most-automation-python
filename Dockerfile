# Imagem oficial do Playwright
FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de dependencia primeiro
COPY requirements.txt .

# Instalação das dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o repositorio local para o container
COPY . .

# Expõe a porta que a API vai utilizar
EXPOSE 8000

CMD ["python", "-m","src.core.main"]