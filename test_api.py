import requests
import json

def test_api():
    """Простой тест API"""
    
    # URL API
    url = "http://localhost:8000/api/sets"
    
    # Тестовые данные
    data = {
        "day_exercise_id": 1,
        "set_order": 1,
        "week_no": 2,
        "rep": 10
    }
    
    print("=== ТЕСТ API ===")
    print(f"URL: {url}")
    print(f"Данные: {json.dumps(data, indent=2)}")
    print()
    
    try:
        # Отправляем запрос
        response = requests.post(url, json=data)
        
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успех!")
            print(f"Ответ: {json.dumps(result, indent=2)}")
        else:
            print("❌ Ошибка!")
            print(f"Текст: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    test_api()
