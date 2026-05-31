import os
import json
import requests
from bs4 import BeautifulSoup
import time

def fetch_and_process_news():
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    if not all([notion_token, database_id]):
        print("エラー: 必要な環境変数が設定されていません。")
        return

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    query_url = f"https://api.notion.com/v1/databases/{database_id}/query"
    
    results = []
    has_more = True
    next_cursor = None
    
    print("Notionから公開中の記事を取得しています...")

    # ★変更点1：100件の壁を突破するページネーション（全件取得）ループ
    while has_more:
        payload = {
            "filter": {
                "property": "ステータス",
                "status": {
                    "equals": "公開"
                }
            }
        }
        if next_cursor:
            payload["start_cursor"] = next_cursor

        response = requests.post(query_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Notion APIエラー: {response.text}")
            break
            
        data = response.json()
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor", None)
        
        # API制限対策のウェイト
        time.sleep(0.5)

    print(f"{len(results)}件の公開記事を取得しました。")

    news_data = []

    for item in results:
        page_id = item["id"]
        props = item.get("properties", {})

        try:
            original_title = props.get("名前", {}).get("title", [{}])[0].get("plain_text", "No Title")
        except IndexError:
            original_title = "No Title"

        try:
            short_title = props.get("short_title", {}).get("rich_text", [{}])[0].get("plain_text", "")
        except IndexError:
            short_title = original_title

        try:
            date_str = props.get("日付", {}).get("date", {}).get("start", "")
        except AttributeError:
            date_str = ""

        try:
            url = props.get("URL", {}).get("url", "")
        except AttributeError:
            url = ""

        try:
            category = props.get("カテゴリー", {}).get("rich_text", [{}])[0].get("plain_text", "未分類")
        except IndexError:
            category = "未分類"

        try:
            full_text = props.get("full_text", {}).get("rich_text", [{}])[0].get("plain_text", "")
        except IndexError:
            full_text = ""

        if not full_text and url:
            print(f"本文取得中: {original_title}")
            try:
                req_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                res = requests.get(url, headers=req_headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                for script in soup(["script", "style"]):
                    script.extract()
                
                text_content = soup.get_text(separator=' ', strip=True)[:6000]

                if text_content:
                    chunks = [text_content[i:i+2000] for i in range(0, len(text_content), 2000)]
                    rich_text_array = [{"text": {"content": chunk}} for chunk in chunks]

                    patch_url = f"https://api
