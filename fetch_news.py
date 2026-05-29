import os
import json
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")

print("=== 調査開始 ===")
print(f"Tokenが存在するか: {'Yes' if NOTION_TOKEN else 'No'}")
print(f"DB IDが存在するか: {'Yes' if DATABASE_ID else 'No'}")

if not NOTION_TOKEN or not DATABASE_ID:
    print("❌ TokenかDB IDが設定されていません。")
    exit(1)

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
print(f"リクエスト先URL: {url}")

# 最小限のリクエストを送信してみる
print("Notionにリクエストを送信します...")
try:
    response = requests.post(url, headers=headers, json={})
    print(f"レスポンスステータス: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ エラーが発生しました。詳細: {response.text}")
    else:
        data = response.json()
        results = data.get("results", [])
        print(f"✅ 取得成功。件数: {len(results)}")
        
        # 最初の1件のプロパティをすべて表示して、構造を確認する
        if len(results) > 0:
            first_item = results[0]
            print("\n=== 1件目のデータ構造 ===")
            print(json.dumps(first_item.get("properties", {}), ensure_ascii=False, indent=2))
        else:
             print("❌ データが0件です。データベースが空か、権限がありません。")

        # そのまま保存
        with open("news.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

except Exception as e:
    print(f"❌ プログラムの実行中にエラーが発生しました: {e}")

print("=== 調査終了 ===")
