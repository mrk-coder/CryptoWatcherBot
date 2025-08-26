FROM python:3.10-slim

WORKDIR /app

# Копируем requirements первыми для кэширования зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВЕСЬ код проекта
COPY . .

CMD ["python", "bot.py"]
