import os
import json
import requests
from bs4 import BeautifulSoup
from google import genai
import time

def fetch_and_process_news():
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")

    if not all([notion_token, database_id, gemini_api_key]):
        print("エラー: 必要な環境変数が設定されていません。")
        return

    # 最新のSDKでクライアントを初期化
    client = genai.Client(api_key=gemini_api_key)

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

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

        try:
            title = props.get("名前", {}).get("title", [{}])[0].get("plain_text", "No Title")
        except IndexError:
            title = "No Title"

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
            summary = props.get("summary", {}).get("rich_text", [{}])[0].get("plain_text", "")
        except IndexError:
            summary = ""

        if not summary and url:
            print(f"要約生成中: {title}")
            try:
                res = requests.get(url, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                for script in soup(["script", "style"]):
                    script.extract()
                text_content = soup.get_text(separator=' ', strip=True)[:5000]

                prompt = f"以下のニュース記事の本文を読み、重要なポイントを3〜4文程度の簡潔な日本語で要約してください。\n\n{text_content}"
                
                # ★他のAIさんの指摘通り、正しいモデル名でシンプルに指定！
                ai_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                summary = ai_response.text.strip()

                patch_url = f"https://api.notion.com/v1/pages/{page_id}"
                patch_payload = {
                    "properties": {
                        "summary": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": summary
                                    }
                                }
                            ]
                        }
                    }
                }
                requests.patch(patch_url, headers=headers, json=patch_payload)
                print(f" -> 要約完了＆Notion更新成功")
                
                time.sleep(2)

            except Exception as e:
                print(f" -> {title} の要約処理中にエラーが発生しました: {e}")
                summary = "要約の取得に失敗しました。"

        news_data.append({
            "original_title": title,
            "date": date_str,
            "url": url,
            "category": category,
            "summary": summary
        })

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print("\n処理が完了し、news.json を出力しました。")

if __name__ == "__main__":
    fetch_and_process_news()
