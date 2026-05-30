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

    # 公開記事を取得
    query_url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {
        "filter": {
            "property": "ステータス",
            "status": {
                "equals": "公開"
            }
        }
    }

    print("Notionから公開中の記事を取得しています...")
    response = requests.post(query_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Notion APIエラー: {response.text}")
        return

    results = response.json().get("results", [])
    print(f"{len(results)}件の公開記事を取得しました。")

    news_data = []

    for item in results:
        page_id = item["id"]
        props = item.get("properties", {})

        # 各プロパティの取得
        try:
            original_title = props.get("名前", {}).get("title", [{}])[0].get("plain_text", "No Title")
        except IndexError:
            original_title = "No Title"

        try:
            short_title = props.get("short_title", {}).get("rich_text", [{}])[0].get("plain_text", "")
        except IndexError:
            short_title = original_title  # 万が一空の場合は元のタイトルをフォールバック

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

        # full_textが空、かつURLが存在する場合のみスクレイピングを実行
        # （XやYouTubeなどのエラーが出やすいサイトは除外設定も可能ですが、今回はそのままアタックして失敗したらスキップする安全設計です）
        if not full_text and url:
            print(f"本文取得中: {original_title}")
            try:
                # 偽装ユーザーエージェントを設定し、スクレイピングの成功率を上げる
                req_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                res = requests.get(url, headers=req_headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                for script in soup(["script", "style"]):
                    script.extract()
                
                # 本文を抽出（内部検索用として最大6000文字まで取得）
                text_content = soup.get_text(separator=' ', strip=True)[:6000]

                if text_content:
                    # Notionの仕様（1ブロック2000文字制限）に合わせてテキストを分割
                    chunks = [text_content[i:i+2000] for i in range(0, len(text_content), 2000)]
                    rich_text_array = [{"text": {"content": chunk}} for chunk in chunks]

                    patch_url = f"https://api.notion.com/v1/pages/{page_id}"
                    patch_payload = {
                        "properties": {
                            "full_text": {
                                "rich_text": rich_text_array
                            }
                        }
                    }
                    requests.patch(patch_url, headers=headers, json=patch_payload)
                    print(f" -> 本文取得＆Notion保存 成功")
                else:
                    print(f" -> 本文の抽出ができませんでした（動的サイト等の理由）")
                
                time.sleep(1) # サーバーへの負荷軽減

            except Exception as e:
                print(f" -> 取得エラー（タイムアウト・ブロック等）: {e}")

        # ★Web公開用の JSON（著作権的に安全なデータのみを出力）
        # 本文（full_text）は内部検索用なのでここには絶対に入れない
        news_data.append({
            "original_title": original_title,
            "short_title": short_title,
            "date": date_str,
            "url": url,
            "category": category
        })

    # news.json に保存
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print("\n処理が完了し、安全な news.json を出力しました。")

if __name__ == "__main__":
    fetch_and_process_news()
