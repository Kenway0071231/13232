import requests
API_KEY = "c28362f8-ec6a-474f-bd81-1a963224f51a"
resp = requests.get("https://catalog.api.2gis.com/2.0/region/list", params={"key": API_KEY})
for item in resp.json()["result"]["items"]:
    if "ярослав" in item["name"].lower():
        print(f"{item['name']}  (id={item['id']})")
