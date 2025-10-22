# src/routes/api/party.py
from flask import Blueprint, request, jsonify
from src.services.party_service import PartyService

party_bp = Blueprint('party_api', __name__, url_prefix='/api')
service = PartyService()

@party_bp.route('/parties', methods=['GET'])
def get_parties():
    """パーティ一覧を取得する"""
    parties = service.get_all()
    return jsonify(parties)

@party_bp.route('/parties/<int:party_id>', methods=['GET'])
def get_party(party_id):
    """単一のパーティ情報を取得する"""
    party = service.get_by_id(party_id)
    if party:
        return jsonify(party)
    else:
        return jsonify({"error": "Party not found"}), 404

@party_bp.route('/parties', methods=['POST'])
def add_party():
    """新しいパーティを登録する"""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    new_id = service.create(data)
    return jsonify({"id": new_id, "message": "Party added successfully"}), 201

@party_bp.route('/parties/<int:party_id>', methods=['PUT'])
def update_party(party_id):
    """パーティ情報を更新する"""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    updated_rows = service.update(party_id, data)
    if updated_rows > 0:
        return jsonify({"message": f"Party {party_id} updated successfully"})
    else:
        return jsonify({"error": "Party not found or data unchanged"}), 404

@party_bp.route('/parties/<int:party_id>', methods=['DELETE'])
def delete_party(party_id):
    """パーティを削除する"""
    deleted_rows = service.delete(party_id)
    if deleted_rows > 0:
        return jsonify({"message": f"Party {party_id} deleted successfully"})
    else:
        return jsonify({"error": "Party not found"}), 404

@party_bp.route('/register-generated-party', methods=['POST'])
def register_generated_party():
    """生成されたパーティを育成済みポケモンとパーティとしてDBに登録する"""
    data = request.json
    party_data = data.get('party')
    party_name = data.get('party_name')

    try:
        service.register_generated_party(party_data, party_name)
        return jsonify({"message": f"パーティ「{party_name}」を登録しました。"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # logging.exception(e)
        return jsonify({"error": "Failed to register generated party"}), 500
