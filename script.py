import json
import pandas as pd

# Загружаем GeoJSON
with open("yaroslavl.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])

# Категории, которые не интересуют
EXCLUDE_AMENITIES = {
    "parking", "bench", "waste_basket", "toilets", "drinking_water",
    "bicycle_parking", "hunting_stand", "fountain", "picnic_table",
    "shelter", "telephone", "post_box", "recycling", "clock",
    "waste_disposal", "fire_hydrant", "street_lamp", "grit_bin"
}

rows = []
for feature in features:
    props = feature.get("properties", {})
    name = props.get("name")
    if not name:
        continue
    amenity = props.get("amenity", "")
    if amenity in EXCLUDE_AMENITIES:
        continue

    # Координаты
    geom = feature.get("geometry", {})
    if geom.get("type") == "Point":
        coords = geom.get("coordinates", [None, None])
        lon, lat = coords[0], coords[1]
    else:
        # Для линий/полигонов центр может быть в properties
        lat = props.get("lat") or props.get("center", {}).get("lat")
        lon = props.get("lon") or props.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue

    address = (props.get("addr:street", "") + " " + props.get("addr:housenumber", "")).strip()
    phone = props.get("phone", "")
    website = props.get("website", "")
    category = props.get("amenity") or props.get("shop") or props.get("tourism") or props.get("office") or "other"

    rows.append({
        "name": name,
        "address": address,
        "phone": phone,
        "site": website,
        "lat": lat,
        "lon": lon,
        "category": category
    })

df = pd.DataFrame(rows)
df.drop_duplicates(subset=["name", "address"], inplace=True)
print(f"Всего организаций: {len(df)}")

# Сети с >=3 точками
network_counts = df.groupby("name")["address"].nunique()
valid = network_counts[network_counts >= 3].index
df_networks = df[df["name"].isin(valid)]

with pd.ExcelWriter("Сети_Ярославль_OSM.xlsx", engine="openpyxl") as writer:
    for cat, group in df_networks.groupby("category"):
        sheet_name = cat[:31]  # ограничение длины имени листа в Excel
        group.to_excel(writer, sheet_name=sheet_name, index=False)
    df_networks.to_excel(writer, sheet_name="Все сети", index=False)

print("✅ Готово: Сети_Ярославль_OSM.xlsx")
