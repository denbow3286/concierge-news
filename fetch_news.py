import os
import json
import requests

# GitHubに登録した合鍵と地図（ID）を読み込む
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

# Notionにお願いするための設定
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

print("Notionからデータを取得中...")

# データを取得
response = requests.post(url, headers=headers)
data = response.json()

# 取得したデータを news.json というファイルに保存する
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("無事にデータを取得し、news.jsonに保存しました！")
