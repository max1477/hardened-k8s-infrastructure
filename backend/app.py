from flask import Flask, jsonify
import redis
import os

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
