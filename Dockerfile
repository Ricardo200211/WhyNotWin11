# Use a imagem base do Python
FROM python:3.9

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie os arquivos necessários para o diretório de trabalho

COPY main.py ./

RUN git clone https://github.com/Ricardo200211/idade_calculator.git .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta 80 para acesso HTTP
EXPOSE 80

# Defina o comando para iniciar o aplicativo
CMD ["python3", "main.py"]
