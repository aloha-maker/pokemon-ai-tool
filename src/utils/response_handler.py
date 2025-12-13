# src/utils/response_handler.py
from flask import jsonify

def api_success(data, status_code=200):
    """
    APIの成功レスポンスを生成する。

    Args:
        data: レスポンスのペイロードとなるデータ。
        status_code: HTTPステータスコード。デフォルトは200。

    Returns:
        Flaskのレスポンスオブジェクトとステータスコードのタプル。
    """
    response = {
        'status': 'success',
        'data': data
    }
    return jsonify(response), status_code

def api_fail(data, status_code=400):
    """
    APIの失敗レスポンス（クライアントエラー）を生成する。
    バリデーションエラーなどに使用する。

    Args:
        data: エラーの詳細情報。
        status_code: HTTPステータスコード。デフォルトは400。

    Returns:
        Flaskのレスポンスオブジェクトとステータスコードのタプル。
    """
    response = {
        'status': 'fail',
        'data': data
    }
    return jsonify(response), status_code

def api_error(message="Internal Server Error", status_code=500):
    """
    APIのエラーレスポンス（サーバーエラー）を生成する。
    予期せぬ例外などに使用する。

    Args:
        message: エラーメッセージ。
        status_code: HTTPステータスコード。デフォルトは500。

    Returns:
        Flaskのレスポンスオブジェクトとステータスコードのタプル。
    """
    response = {
        'status': 'error',
        'message': message
    }
    return jsonify(response), status_code
