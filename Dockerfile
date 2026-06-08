# Используем тот самый безопасный образ без прав root
FROM nginxinc/nginx-unprivileged:1.25.3-alpine

# Копируем наш интерфейс в папку, из которой Nginx раздает сайты
COPY ./src /usr/share/nginx/html

# Сообщаем, что контейнер будет слушать безопасный порт
EXPOSE 8080
