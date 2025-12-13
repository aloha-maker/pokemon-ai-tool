 P0-3: APIエラーレスポンスからの情報漏洩防止

  現状
  多くのAPIエンドポイントが、例外発生時に str(e) を含んだエラーメッセージをクライアントに返しており、内部情報が漏洩するリスクがある。また、サーバー側のログ記録が不十分。

  修正内容
   1. Flaskのグローバルなエラーハンドラを導入し、予期せぬ Exception を一元的に捕捉する。
   2. ハンドラ内で logging.exception() を使ってエラー詳細をサーバーログに記録し、クライアントには固定の汎用メッセージを返す。
   3. 各APIエンドポイントの個別 try-except は、より具体的な例外（例: ValueError）の捕捉に限定するか、削除する。

  手順
   1. `app.py` にロギング設定とグローバルハンドラを追加:

    1     # app.py
    2     import logging
    3 
    4     def create_app():
    5         # ...
    6         if not app.debug:
    7             # 本番環境用のロギング設定
    8             logging.basicConfig(level=logging.INFO, filename='production.log',
    9                                 format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
   10 
   11         @app.errorhandler(Exception)
   12         def handle_unexpected_error(e):
   13             """予期せぬ例外を捕捉するグローバルハンドラ"""
   14             logging.exception(f"An unexpected error occurred: {e}")
   15             return jsonify({"error": "サーバー内部で予期せぬエラーが発生しました。"}), 500
   16 
   17         return app, socketio
   2. 各APIエンドポイントの修正:
       * 修正前 (`src/routes/api/party.py`):

   1         @party_bp.route('/parties', methods=['GET'])
   2         def get_parties():
   3             try:
   4                 with DatabaseManager() as db:
   5                     parties = db.get_all_parties()
   6                 return jsonify(parties)
   7             except Exception as e:
   8                 return jsonify({"error": str(e)}), 500
       * 修正後:

   1         @party_bp.route('/parties', methods=['GET'])
   2         def get_parties():
   3             # 予期せぬ例外はグローバルハンドラが捕捉するため、try-exceptを削除
   4             with DatabaseManager() as db:
   5                 parties = db.get_all_parties()
   6             return jsonify(parties)

  影響範囲
   - app.py
   - src/routes/api/ 配下のほぼすべてのファイル

  テスト方法
   1. テスト対象のAPIエンドポイント（例: /api/parties）のロジック内に、意図的にエラーを発生させるコード（例: raise ValueError("This is a test error")）を一時的に挿入する。
   2. curl やブラウザからそのAPIを呼び出す。
   3. 確認:
       * クライアントへのレスポンスが {"error": "サーバー内部で予期せぬエラーが発生しました。"} となり、"This is a test error" のような詳細が含まれていないこと。
       * サーバーのコンソールまたは production.log ファイルに、ValueError: This is a test error を含む完全なスタックトレースが記録されていること。

  工数
  約2〜3時間（影響範囲は広いが、修正内容は定型的）

  リスク
   - リスク: 低。エラーハンドリングをより安全な方向に統一する修正であり、正常系のロジックへの影響は少ない。
   - 対策: 修正後に主要なAPIが正常にレスポンスを返すことを確認する。