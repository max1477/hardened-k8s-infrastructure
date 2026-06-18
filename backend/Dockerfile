# Используем легкий официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую папку
WORKDIR /app

# Устанавливаем нужные библиотеки (веб-сервер Flask и драйвер Redis)
RUN pip install --no-cache-dir flask redis

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txtЧЁ

# Копируем наш код
COPY app.py .

# DevSecOps правило: Создаем пользователя без прав root и переключаемся на него
RUN useradd -m backenduser
USER backenduser

# Открываем порт
EXPOSE 5000

# Запускаем приложение
CMD ["python", "app.py"]
