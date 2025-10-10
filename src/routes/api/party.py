# src/routes/api/party.py
from flask import Blueprint, request, jsonify
from src.database.manager import DatabaseManager

party_bp = Blueprint('party_api', __name__, url_prefix='/api')

@party_bp.route('/parties', methods=['GET'])
def get_parties():
    """パーティ一覧を取得する"""
    try:
        with DatabaseManager() as db:
            parties = db.get_all_parties()
        return jsonify(parties)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@party_bp.route('/parties/<int:party_id>', methods=['GET'])
def get_party(party_id):
    """単一のパーティ情報を取得する"""
    try:
        with DatabaseManager() as db:
            party = db.get_party_by_id(party_id)
        if party:
            return jsonify(party)
        else:
            return jsonify({"error": "Party not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@party_bp.route('/parties', methods=['POST'])
def add_party():
    """新しいパーティを登録する"""
    data = request.json
    try:
        with DatabaseManager() as db:
            new_id = db.add_party(data)
        return jsonify({"id": new_id, "message": "Party added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@party_bp.route('/parties/<int:party_id>', methods=['PUT'])
def update_party(party_id):
    """パーティ情報を更新する"""
    data = request.json
    try:
        with DatabaseManager() as db:
            updated_rows = db.update_party(party_id, data)
        if updated_rows > 0:
            return jsonify({"message": f"Party {party_id} updated successfully"})
        else:
            return jsonify({"error": "Party not found or data unchanged"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@party_bp.route('/parties/<int:party_id>', methods=['DELETE'])
def delete_party(party_id):
    """パーティを削除する"""
    try:
        with DatabaseManager() as db:
            deleted_rows = db.delete_party(party_id)
        if deleted_rows > 0:
            return jsonify({"message": f"Party {party_id} deleted successfully"})
        else:
            return jsonify({"error": "Party not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@party_bp.route('/register-generated-party', methods=['POST'])
def register_generated_party():
    """生成されたパーティを育成済みポケモンとパーティとしてDBに登録する"""
    data = request.json
    party_data = data.get('party')
    party_name = data.get('party_name')

    if not party_data or not party_name or len(party_data) != 6:
        return jsonify({"error": "無効なパーティデータです。"}), 400

    try:
        with DatabaseManager() as db:
            new_pokemon_ids = []
            for p in party_data:
                # add_trained_pokemon が受け取る形式にデータを整形
                trained_pokemon_data = {
                    "pokemon_id": p['pokemon_id'],
                    "nickname": p['name'], # ニックネームはとりあえずポケモン名
                    "level": 50,
                    "tera_type_id": p['tera_type_id'],
                    "ability_id": p['ability_id'],
                    "nature_id": p['nature_id'],
                    "held_item_id": p['item_id'],
                    "move1_id": p['moves'][0]['id'] if len(p['moves']) > 0 else None,
                    "move2_id": p['moves'][1]['id'] if len(p['moves']) > 1 else None,
                    "move3_id": p['moves'][2]['id'] if len(p['moves']) > 2 else None,
                    "move4_id": p['moves'][3]['id'] if len(p['moves']) > 3 else None,
                    **p['evs'] # ev_hp, ev_atk, ... を展開して渡す
                }
                new_id = db.add_trained_pokemon(trained_pokemon_data)
                new_pokemon_ids.append(new_id)
            
            # 新しいパーティを登録
            party_to_add = {
                "name": party_name,
                "description": "AIにより自動生成されたパーティです。",
                "members": new_pokemon_ids
            }
            db.add_party(party_to_add)

        return jsonify({"message": f"パーティ「{party_name}」を登録しました。"}), 201

    except Exception as e:
        # import traceback; traceback.print_exc()
        return jsonify({"error": f"パーティの登録中にエラーが発生しました: {str(e)}"}), 500
