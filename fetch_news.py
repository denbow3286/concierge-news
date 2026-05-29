import os
import json
import requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

all_results = []
has_more = True
next_cursor = None

print("Notionからデータを全件取得します...")

while has_more:
    payload = {}
    if next_cursor:
        payload["start_cursor"] = next_cursor

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"エラーが発生しました: {response.status_code}")
        break

    data = response.json()
    all_results.extend(data.get("results", []))
    
    has_more = data.get("has_more", False)
    next_cursor = data.get("next_cursor", None)

print(f"合計 {len(all_results)} 件のニュースを取得しました！")

# ⚠️今回は「整形せずに」そのまま全データを保存します
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print("生データをnews.jsonに保存しました！")
