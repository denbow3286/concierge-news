import os
import json
import requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

print("調査を開始します...")

# 1. 今見ているデータベースの名前を特定する
db_info_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
db_res = requests.get(db_info_url, headers=headers)

if db_res.status_code == 200:
    title_arr = db_res.json().get("title", [])
    db_title = title_arr[0].get("plain_text", "名前なし（または空）") if title_arr else "名前なし（または空）"
    print(f"✅ 接続成功！現在ロボットが見ているデータベース名: 【 {db_title} 】")
else:
    print(f"❌ データベースにアクセスできません。エラーコード: {db_res.status_code}")

# 2. データを取得してみる
url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
response = requests.post(url, headers=headers, json={})
data = response.json()
all_results = data.get("results", [])

print(f"取得したニュースの件数: {len(all_results)} 件")

# 保存
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
