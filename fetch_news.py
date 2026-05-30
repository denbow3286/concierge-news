import os
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

def fetch_and_process_news():
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")

    if not all([notion_token, database_id, gemini_api_key]):
        print("エラー: 必要な環境変数が設定されていません。")
        return

    # Gemini APIの初期設定
    genai.configure(api_key=gemini_api_key)
    # 処理が速くコストパフォーマンスの良いモデルを指定
    model = genai.GenerativeModel('gemini-1.5-flash')

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # ステータスが「公開」のものだけを取得するフィルター
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

        # 各プロパティを安全に取得（存在しない・空の場合はデフォルト値を設定）
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

        # summaryプロパティの確認
        try:
            summary = props.get("summary", {}).get("rich_text", [{}])[0].get("plain_text", "")
        except IndexError:
            summary = ""

        # summaryが空、かつURLが存在する場合のみ、スクレイピングと要約を実行
        if not summary and url:
            print(f"要約生成中: {title}")
            try:
                # スクレイピング
                res = requests.get(url, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # スクリプトやスタイルシートを除外してテキストを抽出
                for script in soup(["script", "style"]):
                    script.extract()
                text_content = soup.get_text(separator=' ', strip=True)

                # 本文が長すぎる場合は先頭の一部のみをGeminiに渡す（トークン節約）
                text_content = text_content[:5000]

                # Geminiで要約
                prompt = f"以下のニュース記事の本文を読み、重要なポイントを3〜4文程度の簡潔な日本語で要約してください。\n\n{text_content}"
                ai_response = model.generate_content(prompt)
                summary = ai_response.text.strip()

                # Notionへ書き戻し (PATCH)
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
                
                # 連続リクエストによるエラーを防ぐため少し待機
                time.sleep(2)

            except Exception as e:
                print(f" -> {title} の要約処理中にエラーが発生しました: {e}")
                summary = "要約の取得に失敗しました。"

        # Webサイト用のJSON形式に整形
        news_data.append({
            "original_title": title,
            "date": date_str,
            "url": url,
            "category": category,
            "summary": summary
        })

    # news.json に保存
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print("\n処理が完了し、news.json を出力しました。")

if __name__ == "__main__":
    fetch_and_process_news()
