import os
import requests
import json

def fetch_notion_data():
    # 環境変数の取得
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    # 環境変数が正しくセットされているか確認（トークン自体は表示しない）
    if not notion_token or not database_id:
        print("エラー: NOTION_TOKEN または NOTION_DATABASE_ID が設定されていません。")
        return

    print(f"データベースID: {database_id}")
    print("Notion APIにリクエストを送信中...")

    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28" # 必要に応じてご使用のバージョンに合わせてください
    }

    try:
        response = requests.post(url, headers=headers)
        
        # ステータスコードの出力
        print(f"ステータスコード: {response.status_code}")

        # リクエストが失敗した場合のエラー内容出力
        if response.status_code != 200:
            print("Notion APIエラーメッセージ:")
            print(response.text)
            return

        # データの解析
        data = response.json()
        results = data.get("results", [])
        
        # 取得できた件数の出力
        print(f"取得できたデータ件数: {len(results)}件")

        # 最初の1件の生データを出力
        if len(results) > 0:
            print("\n=== 最初の1件の生データ (JSON) ===")
            print(json.dumps(results[0], indent=2, ensure_ascii=False))
            print("==================================")
        else:
            print("データベースにレコードが存在しない、もしくはフィルターで弾かれている可能性があります。")

        # デバッグ用として、空のリストを強制的に書き出しておく（Actionsのエラー回避のため）
        with open("news.json", "w", encoding="utf-8") as f:
            json.dump([], f)
        print("\nデバッグ用ダミーとして news.json を出力しました。")

    except Exception as e:
        print(f"通信エラーなどの例外が発生しました: {e}")

if __name__ == "__main__":
    fetch_notion_data()
