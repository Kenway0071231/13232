import requests, json

API_KEY = "c28362f8-ec6a-474f-bd81-1a963224f51a"

# 1. Проверяем region/list
print("=== region/list ===")
resp = requests.get("https://catalog.api.2gis.com/2.0/region/list", params={"key": API_KEY})
print("Статус:", resp.status_code)
data = resp.json()
print("Ключи:", list(data.keys()))
if 'meta' in data:
    print("meta:", json.dumps(data['meta'], indent=2, ensure_ascii=False))
if 'items' in data:
    print(f"Регионов: {len(data['items'])}")
elif 'result' in data and 'items' in data['result']:
    print(f"Регионов: {len(data['result']['items'])}")

# 2. Проверяем profile (информация о ключе)
print("\n=== profile ===")
resp = requests.get("https://catalog.api.2gis.com/2.0/profile", params={"key": API_KEY})
print("Статус:", resp.status_code)
data = resp.json()
print("Ключи:", list(data.keys()))
if 'meta' in data:
    print("meta:", json.dumps(data['meta'], indent=2, ensure_ascii=False))
else:
    print(json.dumps(data, indent=2, ensure_ascii=False))
