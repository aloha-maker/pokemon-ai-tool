
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "pokemon_ai.db")

def main():
    """ `types` テーブルへの書き込みテストを実行する """
    print(f"データベース '{DB_PATH}' に接続します...")
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("データベースに接続しました。")
        print('----------------------------------')
        
        # 1. INSERT
        print('INSERT INTO types ... を試みます。')
        cursor.execute("INSERT INTO types (id, name, name_ja) VALUES (999, 'test-type', 'テストタイプ')")
        conn.commit()
        print('-> INSERTに成功しました。')
        print('----------------------------------')

        # 2. SELECT
        print('SELECT * FROM types WHERE id = 999 を試みます。')
        cursor.execute('SELECT * FROM types WHERE id = 999')
        row = cursor.fetchone()
        print(f'-> 取得データ: {row}')
        if not row:
            raise AssertionError("挿入したデータが見つかりません。")
        print('----------------------------------')

        # 3. DELETE
        print('DELETE FROM types WHERE id = 999 を試みます。')
        cursor.execute('DELETE FROM types WHERE id = 999')
        conn.commit()
        print('-> テストデータを削除しました。')
        print('==================================')
        print('テストは成功です。テーブルは正常に存在し、書き込み可能です。')

    except Exception as e:
        print(f'エラーが発生しました: {e}')
        print('==================================')
        print('テストは失敗です。テーブルが存在しないか、スキーマが異なる可能性があります。')
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("データベース接続を閉じました。")

if __name__ == '__main__':
    main()
