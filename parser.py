import requests
import pandas as pd
import time
import json
import os
from datetime import datetime, timedelta

# ---------- НАСТРОЙКИ ----------
API_KEY = "c28362f8-ec6a-474f-bd81-1a963224f51a"   # Замени на ключ из шага 1
REGION_NAME = "Ярославская"         # Название региона (можно не менять)
OUTPUT_CSV = "2gis_raw.csv"         # Файл для временного сохранения данных
PROCESSED_FILE = "processed_rubrics.txt"  # Чтобы запоминать обработанные рубрики
EXCEL_FILE = "Сети_Ярославская_область.xlsx"  # Итоговый Excel

# Стоп-слова – рубрики с такими словами будут исключены
STOP_WORDS = [
    "продуктовый", "супермаркет", "гипермаркет", "продукты питания",
    "администрация", "правительство", "полиция", "суд", "прокуратура",
    "военкомат", "паспортный стол", "госуслуги", "мфц", "налоговая",
    "фсб", "мвд", "пожарная", "следственный", "избирательная",
    "законодательное", "контрольно-счетная"
]

# ---------- ФУНКЦИИ ----------
def api_request(url, params, max_retries=10):
    """Делает запрос к API, при превышении лимита ждёт до завтра."""
    while True:
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                print("Лимит 1000 запросов исчерпан. Жду до завтра 01:00 МСК...")
                # Ждём до следующего дня (примерно)
                now = datetime.now()
                next_day = now + timedelta(days=1)
                next_run = next_day.replace(hour=1, minute=0, second=0, microsecond=0)
                wait_seconds = (next_run - now).total_seconds()
                if wait_seconds < 0:
                    wait_seconds += 24*3600
                time.sleep(wait_seconds)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса: {e}. Повтор через 30 сек...")
            time.sleep(30)

def get_region_id(api_key, region_name):
    """Получает ID региона по названию."""
    print("Ищу ID Ярославской области...")
    data = api_request(
        "https://catalog.api.2gis.com/2.0/region/list",
        {"key": api_key}
    )
    for item in data["result"]["items"]:
        if region_name.lower() in item["name"].lower():
            print(f"Найден регион: {item['name']} (id={item['id']})")
            return item["id"]
    raise Exception(f"Регион '{region_name}' не найден. Проверь название.")

def get_filtered_rubrics(api_key):
    """Загружает все рубрики и исключает продуктовые и госорганизации."""
    print("Загружаю все рубрики 2ГИС...")
    data = api_request(
        "https://catalog.api.2gis.com/2.0/rubric/list",
        {"key": api_key}
    )
    all_rubrics = data["result"]["items"]
    print(f"Всего рубрик в справочнике: {len(all_rubrics)}")
    
    filtered = []
    for rubric in all_rubrics:
        name_lower = rubric["name"].lower()
        if not any(word in name_lower for word in STOP_WORDS):
            filtered.append(rubric)
    print(f"После фильтрации осталось рубрик: {len(filtered)}")
    return filtered

def load_processed():
    """Читает список уже обработанных рубрик."""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_processed(rubric_id):
    """Добавляет рубрику в список обработанных."""
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(rubric_id + "\n")

def collect_branches_for_rubric(api_key, region_id, rubric_id, rubric_name):
    """Собирает все филиалы для заданной рубрики в регионе."""
    items_list = []
    page = 1
    while True:
        params = {
            "key": api_key,
            "region_id": region_id,
            "rubric_id": rubric_id,
            "page_size": 500,
            "page": page,
            "fields": "items.point,items.address_name,items.name,items.rubrics"
        }
        data = api_request("https://catalog.api.2gis.com/2.0/branch/search", params)
        result = data.get("result", {})
        items = result.get("items", [])
        if not items:
            break
        for item in items:
            point = item.get("point", {})
            items_list.append({
                "name": item["name"],
                "address": item.get("address_name", ""),
                "lat": point.get("lat"),
                "lon": point.get("lon"),
                "rubric_id": rubric_id,
                "rubric_name": rubric_name
            })
        total = result["total"]
        if page * 500 >= total:
            break
        page += 1
        time.sleep(0.2)   # не перегружаем API
    print(f"  Рубрика '{rubric_name}': собрано {len(items_list)} точек (всего {total})")
    return items_list

def main():
    # 1. Получаем ID региона
    region_id = get_region_id(API_KEY, REGION_NAME)
    
    # 2. Получаем отфильтрованные рубрики
    rubrics = get_filtered_rubrics(API_KEY)
    
    # 3. Загружаем уже обработанные рубрики
    processed = load_processed()
    print(f"Уже обработано рубрик: {len(processed)}")
    
    # 4. Если есть сохранённые ранее данные, загружаем их
    if os.path.exists(OUTPUT_CSV):
        old_df = pd.read_csv(OUTPUT_CSV, encoding="utf-8")
        print(f"Загружено {len(old_df)} записей из предыдущих запусков")
    else:
        old_df = pd.DataFrame()
    
    # 5. Обходим необработанные рубрики
    for idx, rubric in enumerate(rubrics, 1):
        rid = rubric["id"]
        rname = rubric["name"]
        if rid in processed:
            continue
        print(f"\n[{idx}/{len(rubrics)}] Обрабатываю рубрику: {rname}")
        try:
            new_items = collect_branches_for_rubric(API_KEY, region_id, rid, rname)
        except Exception as e:
            print(f"Ошибка при обработке рубрики '{rname}': {e}")
            # Сохраняем то, что есть, и выходим (можно позже перезапустить)
            break
        
        if new_items:
            new_df = pd.DataFrame(new_items)
            # Объединяем с предыдущими данными и сохраняем в CSV
            all_df = pd.concat([old_df, new_df], ignore_index=True)
            all_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
            old_df = all_df  # обновляем переменную
            print(f"  Сохранено в {OUTPUT_CSV}, всего записей: {len(all_df)}")
        
        # Отмечаем рубрику как обработанную
        save_processed(rid)
        time.sleep(0.3)
    
    print("\nСбор данных завершён (или прерван по лимиту).")
    
    # 6. Анализируем данные и строим Excel
    if old_df.empty:
        print("Нет собранных данных. Запустите скрипт позже.")
        return
    
    print("Группирую сети (минимум 3 точки)...")
    # Убираем дубли (один филиал может быть в нескольких рубриках)
    df_unique = old_df.drop_duplicates(subset=["name", "address"])
    
    # Считаем количество адресов для каждой сети
    network_counts = df_unique.groupby("name")["address"].nunique()
    # Оставляем только сети с >= 3 точками
    valid_networks = network_counts[network_counts >= 3].index
    df_networks = df_unique[df_unique["name"].isin(valid_networks)]
    
    print(f"Найдено {len(valid_networks)} сетей (3+ точки), всего {len(df_networks)} филиалов")
    
    # Для каждой сети берём её рубрику (приоритет – та, с которой она была получена)
    # Упростим: оставим все рубрики, по которым сеть встречается, а в Excel разложим по первой рубрике
    df_networks["category"] = df_networks.groupby("name")["rubric_name"].transform("first")
    
    # Пишем Excel с листами по категориям
    print(f"Создаю Excel-файл: {EXCEL_FILE}")
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        for category, group in df_networks.groupby("category"):
            # Лист Excel не может иметь имя длиннее 31 символа
            sheet_name = category[:31]
            # Убираем дубли внутри листа
            group_sorted = group.sort_values("name")
            group_sorted.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # 7. Дополнительно сохраняем сводку
    summary = df_networks.groupby(["category", "name"]).agg(
        points=("address", "nunique"),
        addresses=("address", lambda x: ", ".join(sorted(x.unique())[:5]) + ("..." if len(x.unique())>5 else ""))
    ).reset_index()
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="a") as writer:
        summary.to_excel(writer, sheet_name="Сводка_сети", index=False)
    
    print(f"\nГотово! Итоговый файл: {EXCEL_FILE}")
    print("В нём вкладки с категориями и вкладка 'Сводка_сети' с перечнем сетей.")

if __name__ == "__main__":
    main()
