import traceback
import math
import uuid

from flask import Blueprint, jsonify, request
from src.database.manager import DatabaseManager
from src.services.dashboard_service import DashboardService
from src.core import calculator
from src.ai import simulator

# APIエンドポイント用のBlueprintを作成
api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- シミュレーションセッション管理 ---
# 本番環境ではRedisなどを使用すべきだが、ここでは簡易的にグローバル変数で管理
simulations = {}

# --- F-05: 育成済みポケモン管理 (Trained Pokemons) ---

@api_bp.route('/trained-pokemons', methods=['GET'])
def get_trained_pokemons():
    """登録済みの育成済みポケモンを一覧で取得する。"""
    try:
        with DatabaseManager() as db:
            pokemons = db.get_all_trained_pokemons()
        return jsonify(pokemons), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['GET'])
def get_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモンの詳細を取得する。"""
    try:
        with DatabaseManager() as db:
            pokemon = db.get_trained_pokemon_by_id(pokemon_id)
        if pokemon:
            return jsonify(pokemon), 200
        else:
            return jsonify({'error': 'Pokemon not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trained-pokemons', methods=['POST'])
def add_trained_pokemon():
    """新しい育成済みポケモンを登録する。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    # フロントエンドからのキー 'pokemon_master_id' を 'pokemon_id' に変換
    if 'pokemon_master_id' in data:
        data['pokemon_id'] = data.pop('pokemon_master_id')
    
    try:
        with DatabaseManager() as db:
            new_id = db.add_trained_pokemon(data)
        return jsonify({'message': 'Pokemon added successfully', 'id': new_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['PUT'])
def update_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモン情報を更新する。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    # フロントエンドからのキー 'pokemon_master_id' を 'pokemon_id' に変換
    if 'pokemon_master_id' in data:
        data['pokemon_id'] = data.pop('pokemon_master_id')

    try:
        with DatabaseManager() as db:
            updated_rows = db.update_trained_pokemon(pokemon_id, data)
        if updated_rows > 0:
            return jsonify({'message': f'Pokemon {pokemon_id} updated successfully'}), 200
        else:
            return jsonify({'error': 'Pokemon not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['DELETE'])
def delete_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモンを削除する。"""
    try:
        with DatabaseManager() as db:
            deleted_rows = db.delete_trained_pokemon(pokemon_id)
        if deleted_rows > 0:
            return jsonify({'message': f'Pokemon {pokemon_id} deleted successfully'}), 200
        else:
            return jsonify({'error': 'Pokemon not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Master Data API Endpoints ---

@api_bp.route('/master/<resource>', methods=['GET'])
def get_master_data(resource):
    """ポケモン、技、特性などのマスターデータを取得する。"""
    valid_resources = ['pokemons', 'moves', 'items', 'abilities', 'natures', 'types']
    if resource not in valid_resources:
        return jsonify({'error': 'Invalid resource specified'}), 404

    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            # name_ja がないテーブル (moves) のために name を使う -> name_jaが存在するため修正
            if resource == 'pokemons':
                # ポケモン名で重複を除外する（フォルム違いなどをまとめる）
                cursor.execute("SELECT MIN(id) as id, name, name_ja FROM pokemons GROUP BY name_ja ORDER BY name_ja")
            else:
                 cursor.execute(f"SELECT id, name, name_ja FROM {resource} WHERE name_ja IS NOT NULL AND name_ja != '' ORDER BY name_ja")
            items = cursor.fetchall()
        return jsonify([dict(item) for item in items]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 持ち物編集用API ---

@api_bp.route('/items', methods=['POST'])
def add_item():
    """新しい持ち物を追加する。"""
    data = request.get_json()
    if not data or not data.get('name_ja'):
        return jsonify({'error': 'Invalid data: name_ja is required.'}), 400
    
    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            # 既存の持ち物名と重複しないかチェック
            cursor.execute("SELECT id FROM items WHERE name_ja = ?", (data['name_ja'],))
            if cursor.fetchone():
                return jsonify({'error': 'Item with this name already exists.'}), 409
            
            # name は name_ja と同じ値で登録
            cursor.execute(
                "INSERT INTO items (name, name_ja) VALUES (?, ?)",
                (data['name_ja'], data['name_ja'])
            )
            db.conn.commit()
            new_id = cursor.lastrowid
        return jsonify({'message': 'Item added successfully', 'id': new_id, 'name_ja': data['name_ja']}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """持ち物名を更新する。"""
    data = request.get_json()
    if not data or not data.get('name_ja'):
        return jsonify({'error': 'Invalid data: name_ja is required.'}), 400

    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            # 既存の持ち物名と重複しないかチェック (自分自身を除く)
            cursor.execute("SELECT id FROM items WHERE name_ja = ? AND id != ?", (data['name_ja'], item_id))
            if cursor.fetchone():
                return jsonify({'error': 'Item with this name already exists.'}), 409

            # name は name_ja と同じ値で更新
            cursor.execute(
                "UPDATE items SET name = ?, name_ja = ? WHERE id = ?",
                (data['name_ja'], data['name_ja'], item_id)
            )
            db.conn.commit()
            if cursor.rowcount == 0:
                return jsonify({'error': 'Item not found'}), 404
        return jsonify({'message': 'Item updated successfully', 'id': item_id, 'name_ja': data['name_ja']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """持ち物を削除する。"""
    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            db.conn.commit()
            if cursor.rowcount == 0:
                return jsonify({'error': 'Item not found'}), 404
        return jsonify({'message': 'Item deleted successfully'}), 200
    except Exception as e:
        # 外部キー制約違反の場合
        if 'FOREIGN KEY constraint failed' in str(e):
            return jsonify({'error': 'This item is currently in use by a trained Pokémon and cannot be deleted.'}), 409
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties', methods=['GET'])
def get_parties():
    """登録済みのパーティを一覧で取得する。"""
    try:
        with DatabaseManager() as db:
            parties = db.get_all_parties()
        return jsonify(parties), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties/<int:party_id>', methods=['GET'])
def get_party(party_id):
    """指定したIDのパーティ詳細を取得する。"""
    try:
        with DatabaseManager() as db:
            party = db.get_party_by_id(party_id)
        if party:
            return jsonify(party), 200
        else:
            return jsonify({'error': 'Party not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties', methods=['POST'])
def add_party():
    """新しいパーティを登録する。"""
    data = request.get_json()
    if not data or not data.get('name') or 'members' not in data:
        return jsonify({'error': 'Invalid data: name and members are required.'}), 400
    
    try:
        with DatabaseManager() as db:
            new_id = db.add_party(data)
        return jsonify({'message': 'Party added successfully', 'id': new_id}), 201
    except Exception as e:
        print(f"Error in add_party: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties/<int:party_id>', methods=['PUT'])
def update_party(party_id):
    """指定したIDのパーティ情報を更新する。"""
    data = request.get_json()
    if not data or not data.get('name') or 'members' not in data:
        return jsonify({'error': 'Invalid data: name and members are required.'}), 400

    try:
        with DatabaseManager() as db:
            updated_rows = db.update_party(party_id, data)
        if updated_rows > 0:
            return jsonify({'message': f'Party {party_id} updated successfully'}), 200
        else:
            return jsonify({'error': 'Party not found or no changes made'}), 404
    except Exception as e:
        print(f"Error in update_party: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties/<int:party_id>', methods=['DELETE'])
def delete_party(party_id):
    """指定したIDのパーティを削除する。"""
    try:
        with DatabaseManager() as db:
            deleted_rows = db.delete_party(party_id)
        if deleted_rows > 0:
            return jsonify({'message': f'Party {party_id} deleted successfully'}), 200
        else:
            return jsonify({'error': 'Party not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- F-07: 計算機 (Calculator) ---

@api_bp.route('/calculate/status', methods=['POST'])
def calculate_status_api():
    """ポケモンのステータス実数値を計算して返す。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        pokemon_id = data.get('pokemon_id')
        level = int(data.get('level', 50))
        evs = data.get('evs', {})
        # 個体値は常に31で固定
        ivs = {'hp': 31, 'attack': 31, 'defense': 31, 'sp_attack': 31, 'sp_defense': 31, 'speed': 31}
        nature_id = data.get('nature_id')

        with DatabaseManager() as db:
            # 1. 種族値を取得
            cursor = db.get_cursor()
            cursor.execute("SELECT hp, attack, defense, sp_attack, sp_defense, speed FROM pokemons WHERE id = ?", (pokemon_id,))
            base_stats_row = cursor.fetchone()
            if not base_stats_row:
                return jsonify({'error': 'Pokemon not found'}), 404
            base_stats = dict(base_stats_row)

            # 2. 性格補正を取得
            cursor.execute("SELECT increased_stat, decreased_stat FROM natures WHERE id = ?", (nature_id,))
            nature_row = cursor.fetchone()
            nature = dict(nature_row) if nature_row else None

        # 3. 計算実行
        calculated_stats = calculator.calculate_status(base_stats, level, evs, ivs, nature)

        return jsonify(calculated_stats), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/calculate/damage', methods=['POST'])
def calculate_damage_api():
    """ダメージ計算を行い、結果を返す。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        # フロントエンドから送られてくるデータを展開
        attacker_level = int(data['attacker_level'])
        attack_stat = int(data['attack_stat'])
        defender_hp = int(data['defender_hp'])
        defense_stat = int(data['defense_stat'])
        move_id = int(data['move_id'])
        defender_id = int(data['defender_id'])

        with DatabaseManager() as db:
            cursor = db.get_cursor()
            # 技情報を取得
            cursor.execute("SELECT power, type, category FROM moves WHERE id = ?", (move_id,))
            move_info = cursor.fetchone()
            if not move_info:
                return jsonify({'error': 'Move not found'}), 404
            move_power, move_type, move_category = move_info

            # 防御側ポケモンのタイプを取得
            cursor.execute("SELECT type1, type2 FROM pokemons WHERE id = ?", (defender_id,))
            defender_types = cursor.fetchone()
            if not defender_types:
                return jsonify({'error': 'Defender not found'}), 404
            defender_type1, defender_type2 = defender_types

        # ダメージ計算実行
        min_damage, max_damage = calculator.calculate_damage(
            attacker_level=attacker_level,
            move_power=move_power,
            attack_stat=attack_stat,
            defense_stat=defense_stat,
            move_type=move_type,
            defender_type1=defender_type1,
            defender_type2=defender_type2
        )

        # 確定数を計算
        if min_damage > 0:
            min_hits_to_ko = math.ceil(defender_hp / max_damage) if max_damage > 0 else float('inf')
            max_hits_to_ko = math.ceil(defender_hp / min_damage) if min_damage > 0 else float('inf')
        else:
            min_hits_to_ko = float('inf')
            max_hits_to_ko = float('inf')

        return jsonify({
            'min_damage': min_damage,
            'max_damage': max_damage,
            'min_damage_percent': round((min_damage / defender_hp) * 100, 1) if defender_hp > 0 else 0,
            'max_damage_percent': round((max_damage / defender_hp) * 100, 1) if defender_hp > 0 else 0,
            'min_hits_to_ko': min_hits_to_ko,
            'max_hits_to_ko': max_hits_to_ko
        }), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# --- F-08: 疑似対戦シミュレーション (Step-by-step) ---

@api_bp.route('/simulations', methods=['POST'])
def create_simulation():
    """新しい対戦シミュレーションセッションを作成する。"""
    data = request.get_json()
    if not data or 'party1_id' not in data or 'party2_id' not in data:
        return jsonify({'error': 'Invalid data: party1_id and party2_id are required.'}), 400

    try:
        party1_id = int(data['party1_id'])
        party2_id = int(data['party2_id'])

        with DatabaseManager() as db:
            party1 = db.get_party_by_id(party1_id)
            party2 = db.get_party_by_id(party2_id)

        if not party1 or not party2:
            return jsonify({'error': 'One or both parties not found.'}), 404

        sim_id = str(uuid.uuid4())
        sim = simulator.BattleSimulator(party1, party2, party1_id, party2_id)
        simulations[sim_id] = sim
        
        # 選出フェーズを開始
        sim.start_selection()

        return jsonify({'simulation_id': sim_id, 'state': sim.get_state()}), 201

    except Exception as e:
        print(f"Error in create_simulation: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/simulations/<sim_id>', methods=['GET'])
def get_simulation_state(sim_id):
    """指定したシミュレーションの状態を取得する。"""
    sim = simulations.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation not found'}), 404
    return jsonify(sim.get_state()), 200

@api_bp.route('/simulations/<sim_id>/select', methods=['POST'])
def set_simulation_selection(sim_id):
    """シミュレーションの選出を決定する。"""
    sim = simulations.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation not found'}), 404

    data = request.get_json()
    if not data or 'selection1' not in data or 'selection2' not in data:
        return jsonify({'error': 'Invalid data: selection1 and selection2 are required.'}), 400

    try:
        # フロントエンドからのインデックスは 0-5, 0-5
        selection1 = [int(i) for i in data['selection1']]
        selection2 = [int(i) for i in data['selection2']]
        
        sim.set_selection(selection1, selection2)
        return jsonify(sim.get_state()), 200

    except Exception as e:
        print(f"Error in set_simulation_selection: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/simulations/<sim_id>/next_turn', methods=['POST'])
def advance_simulation_turn(sim_id):
    """シミュレーションを1ターン進める。"""
    sim = simulations.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation not found'}), 404

    try:
        sim.next_turn()
        return jsonify(sim.get_state()), 200

    except Exception as e:
        print(f"Error in advance_simulation_turn: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# --- F-12: 分析ダッシュボード (Analysis Dashboard) ---

@api_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """ダッシュボードに表示するための主要な分析データをまとめて取得する。"""
    try:
        service = DashboardService()
        dashboard_data = service.get_dashboard_data()
        return jsonify(dashboard_data), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dashboard/customization', methods=['GET'])
def get_customization_data():
    """指定されたポケモンのカスタマイズ（技・持ち物・テラス）ランキングを取得する。"""
    pokemon_name = request.args.get('pokemon_name')
    if not pokemon_name:
        return jsonify({'error': 'pokemon_name query parameter is required.'}), 400
    
    try:
        service = DashboardService()
        customization_data = service.get_customization_data(pokemon_name)
        return jsonify(customization_data), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500