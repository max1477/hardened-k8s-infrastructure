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

# ==========================================
# БЛОК УПРАВЛЕНИЯ ДАННЫМИ (CRUD)
# ==========================================

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Создаем таблицу с UNIQUE ограничением, чтобы не плодить дубли активов
    cur.execute('''
        CREATE TABLE IF NOT EXISTS crypto_assets (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE,
            amount REAL
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Инициализируем таблицу при запуске скрипта
init_db()

@app.route('/api/add/<name>/<float:amount>')
def add_asset(name, amount):
    conn = get_db_connection()
    cur = conn.cursor()
    # Умная вставка (UPSERT): если актив уже есть, прибавляем сумму к существующей
    cur.execute('''
        INSERT INTO crypto_assets (name, amount) 
        VALUES (%s, %s)
        ON CONFLICT (name) 
        DO UPDATE SET amount = crypto_assets.amount + EXCLUDED.amount;
    ''', (name, amount))
    conn.commit()
    cur.close()
    conn.close()
    return f"Успех! Баланс {name} пополнен. Зачислено: {amount}"

@app.route('/api/assets')
def get_assets():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, amount FROM crypto_assets")
    assets = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"asset": row[0], "amount": row[1]} for row in assets])

@app.route('/api/update/<name>/<float:new_amount>')
def update_asset(name, new_amount):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE crypto_assets SET amount = %s WHERE name = %s", (new_amount, name))
    conn.commit()
    cur.close()
    conn.close()
    return f"Обновлено: {name} до {new_amount}"

@app.route('/api/delete/<name>')
def delete_asset(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM crypto_assets WHERE name = %s", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return f"Удалено: {name}"

# ==========================================
# ЗАПУСК СЕРВЕРА (СТРОГО ВНИЗУ!) ;)
# ==========================================

if __name__ == '__main__':
    # Слушаем порт 5000
    app.run(host='0.0.0.0', port=5000)