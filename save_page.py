import requests

REGION = "Ярославль"
QUERY = "аптека"

url = f"https://2gis.ru/{REGION}/search/{QUERY}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    with open("page.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("HTML сохранён в page.html. Отправьте этот файл мне для анализа.")
else:
    print(f"Ошибка {resp.status_code}. Попробуйте открыть {url} в браузере.")
