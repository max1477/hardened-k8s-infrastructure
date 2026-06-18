from flask import Flask, jsonify
import redis
import os
import time
import psycopg2

app = Flask(__name__)

# Подключаемся к Redis, используя DNS-имя из Helm и пароль из переменной окружения
cache = redis.Redis(
    host='my-cache-redis-master', 
    port=6379,
    password=os.environ.get('MY_DB_PASSWORD'), # Тот самый зашифрованный Секрет!
    decode_responses=True
)

@app.route('/api/margin')
def get_margin():
    try:
        # 1. Пытаемся взять данные из быстрого кэша
        cached_data = cache.get("xrp_margin")
        if cached_data:
            return jsonify({"status": "success", "source": "REDIS_CACHE", "asset": "XRP", "margin": cached_data})
        
        # 2. Если кэша нет (имитация тяжелого расчета в базе данных)
        calculated_margin = "1500"
        
        # 3. Записываем результат в Redis на 60 секунд
        cache.set("xrp_margin", calculated_margin, ex=60)
        
        return jsonify({"status": "success", "source": "HEAVY_CALCULATION", "asset": "XRP", "margin": calculated_margin})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Слушаем порт 5000
    app.run(host='0.0.0.0', port=5000)

# 1. Считываем переменные, которые Kubernetes прописал в контейнер при старте
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "secure_app_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "super-secure-password-123")
DB_NAME = os.getenv("POSTGRES_DB", "secure_app_db")

def get_db_connection():
    # База данных в K8s при перезапуске может инициализироваться на пару секунд дольше бэкенда.
    # Применяем паттерн Retry Loop (цикл повторных попыток), чтобы бэкенд не падал при старте.
    for i in range(5):
        try:
            connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            print("Успешное подключение к PostgreSQL базе данных!")
            return connection
        except psycopg2.OperationalError as e:
            print(f"База данных еще недоступна, ждем... Попытка {i+1}/5. Ошибка: {e}")
            time.sleep(3)
    raise Exception("Критическая ошибка: Не удалось подключиться к базе данных.")

@app.route('/test-db')
def test_db():
    try:
        # Открываем подключение к нашей защищенной БД
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Делаем простейший SQL-запрос, чтобы узнать версию Postgres
        cur.execute('SELECT version();')
        db_version = cur.fetchone()
        
        # Обязательно закрываем соединение, чтобы не "положить" базу
        cur.close()
        conn.close()
        
        return f"Ура! Бэкенд успешно связался с БД. Отвечает: {db_version[0]}"
    except Exception as e:
        return f"База данных недоступна. Ошибка: {str(e)}", 500
# Тест подключения к БД