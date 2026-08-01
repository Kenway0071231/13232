import requests
import json

API_KEY = "c28362f8-ec6a-474f-bd81-1a963224f51a"
REGION_ID = 28  # Ярославль

test_params = [
    # Базовые варианты
    {"key": API_KEY, "region_id": REGION_ID},
    {"key": API_KEY},
    # С дополнительными параметрами
    {"key": API_KEY, "region_id": REGION_ID, "locale": "ru_RU"},
    {"key": API_KEY, "region_id": REGION_ID, "page": 1, "page_size": 50},
    {"key": API_KEY, "region_id": REGION_ID, "fields": "items.id,items.name"},
    # Другой возможный endpoint (вдруг изменился)
    # но оставим только rubric/list, просто с другим доменом? Нет, домен catalog.api.2gis.com
]

# Попробуем и альтернативный URL (если был изменён)
urls = [
    "https://catalog.api.2gis.com/2.0/rubric/list",
    "https://api.2gis.com/2.0/rubric/list"   # вдруг
]

for url in urls:
    for params in test_params:
        print(f"\n=== Запрос: {url} params={params}")
        try:
            resp = requests.get(url, params=params, timeout=10)
            print(f"Статус: {resp.status_code}")
            data = resp.json()
            print("Ключи ответа:", list(data.keys()))
            # Если есть meta, покажем его полностью
            if 'meta' in data:
                print("meta:", json.dumps(data['meta'], indent=2, ensure_ascii=False))
            # Попробуем найти рубрики в возможных местах
            rubrics = data.get("items") or data.get("result", {}).get("items") or data.get("rubrics")
            if rubrics:
                print(f"Найдено рубрик: {len(rubrics)} (показываю до 3)")
                for r in rubrics[:3]:
                    print(f"  - {r.get('name')} (id={r.get('id')})")
            else:
                print("Рубрик не найдено в стандартных полях. Сырой ответ (первые 500 символов):")
                print(str(data)[:500])
        except Exception as e:
            print(f"Ошибка: {e}")
        time.sleep(0.3)

# Также попробуем branch/search с минимальным запросом, чтобы увидеть рубрики в организациях
print("\n=== Проверка branch/search (без rubric_id) на предмет наличия рубрик ===")
params = {
    "key": API_KEY,
    "region_id": REGION_ID,
    "page_size": 1,
    "page": 1,
    "fields": "items.rubrics"
}
resp = requests.get("https://catalog.api.2gis.com/2.0/branch/search", params=params)
print("Статус:", resp.status_code)
data = resp.json()
print("Ключи:", list(data.keys()))
if 'result' in data:
    items = data['result'].get('items', [])
    if items:
        print("Удалось получить организации!")
        rubrics = items[0].get('rubrics', [])
        for r in rubrics:
            print(f"  Рубрика: {r.get('name')} (id={r.get('id')})")
    else:
        print("Организаций нет.")
else:
    print("Нет result. Сырой ответ:", str(data)[:300])
