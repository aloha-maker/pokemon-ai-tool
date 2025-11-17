# src/routes/api/party.py
from flask import Blueprint, request
from src.services.party_service import PartyService
from src.utils.response_handler import api_success, api_fail, api_error
import logging

party_bp = Blueprint('party_api', __name__, url_prefix='/api')
service = PartyService()

@party_bp.route('/parties', methods=['GET'])
def get_parties():
    """パーティ一覧を取得する"""
    try:
        parties = service.get_all()
        return api_success(parties)
    except Exception as e:
        logging.exception("Error getting all parties")
        return api_error("パーティ一覧の取得に失敗しました。")

@party_bp.route('/parties/<int:party_id>', methods=['GET'])
def get_party(party_id):
    """単一のパーティ情報を取得する"""
    try:
        party = service.get_by_id(party_id)
        if party:
            return api_success(party)
        else:
            return api_fail({"message": "Party not found"}, 404)
    except Exception as e:
        logging.exception(f"Error getting party {party_id}")
        return api_error("パーティ情報の取得に失敗しました。")

@party_bp.route('/parties', methods=['POST'])
def add_party():
    """新しいパーティを登録する"""
    try:
        data = request.json
        if not data:
            return api_fail({"message": "No data provided"})
        
        new_id = service.create(data)
        return api_success({"id": new_id, "message": "Party added successfully"}, 201)
    except Exception as e:
        logging.exception("Error adding new party")
        return api_error("パーティの登録に失敗しました。")

@party_bp.route('/parties/<int:party_id>', methods=['PUT'])
def update_party(party_id):
    """パーティ情報を更新する"""
    try:
        data = request.json
        if not data:
            return api_fail({"message": "No data provided"})
        
        updated_rows = service.update(party_id, data)
        if updated_rows > 0:
            return api_success({"message": f"Party {party_id} updated successfully"})
        else:
            return api_fail({"message": "Party not found or data unchanged"}, 404)
    except Exception as e:
        logging.exception(f"Error updating party {party_id}")
        return api_error("パーティの更新に失敗しました。")

@party_bp.route('/parties/<int:party_id>', methods=['DELETE'])
def delete_party(party_id):
    """パーティを削除する"""
    try:
        deleted_rows = service.delete(party_id)
        if deleted_rows > 0:
            return api_success({"message": f"Party {party_id} deleted successfully"})
        else:
            return api_fail({"message": "Party not found"}, 404)
    except Exception as e:
        logging.exception(f"Error deleting party {party_id}")
        return api_error("パーティの削除に失敗しました。")

@party_bp.route('/register-generated-party', methods=['POST'])
def register_generated_party():
    """生成されたパーティを育成済みポケモンとパーティとしてDBに登録する"""
    try:
        data = request.json
        party_data = data.get('party')
        party_name = data.get('party_name')

        service.register_generated_party(party_data, party_name)
        return api_success({"message": f"パーティ「{party_name}」を登録しました。"}, 201)
    except ValueError as e:
        return api_fail({"message": str(e)})
    except Exception as e:
        logging.exception("Error registering generated party")
        return api_error("生成されたパーティの登録に失敗しました。")

@party_bp.route('/party/<int:party_id>', methods=['GET'])
def get_party_menber(party_id):
    """単一のパーティ情報を取得する"""
    try:
        party = service.get_party_menber_by_id(party_id)
        if party:
            return api_success(party)
        else:
            return api_fail({"message": "Party not found"}, 404)
    except Exception as e:
        logging.exception(f"Error getting party {party_id}")
        return api_error("パーティ情報の取得に失敗しました。")
