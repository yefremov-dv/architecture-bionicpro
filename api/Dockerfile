FROM python:3.10-slim-buster

# Настраиваем рабочую директорию
WORKDIR /app

# Сначала копируем сам код
COPY . .

# Затем ставим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем main script
CMD ["python", "/app/app.py"]